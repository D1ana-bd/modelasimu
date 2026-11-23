"""Visualização da simulação em Pygame (estilo "mapa de cidade").

O modelo é o mesmo (Mesa): este ficheiro só o DESENHA.

Correr na raiz do repositório:
    python viz/pygame_app.py
    python viz/pygame_app.py --vehicles 300 --seed 7

Guardar uma imagem de um instante (útil para o relatório):
    python viz/pygame_app.py --snapshot figura.png --at 15

Teclas:
    Espaço  pausar / continuar
    + / -   mais rápido / mais lento
    R       reiniciar
    Esc     sair

Leitura do mapa:
    - cada célula da grelha (250 m) é um cruzamento; entre cruzamentos há quarteirões;
    - a zona do evento (losango) é a fronteira usada nos KPIs "zona do evento";
    - os pontos magenta são as pessoas à espera de carro à saída do estádio
      (no modelo estão todas no estádio; aqui espalham-se à volta dele, dentro da zona);
    - os pontos brancos são pedidos da cidade à espera.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pygame  # noqa: E402

from rideshare_sim.core.entities import PassengerType, RequestStatus, VehicleStatus  # noqa: E402
from rideshare_sim.model import RideshareModel, load_params  # noqa: E402

# ------------------------------------------------------------------ cores
BG = (11, 15, 22)
STREET = (18, 24, 34)
BLOCK = (27, 34, 48)
BUILDING = (36, 45, 62)
BUILDING_EDGE = (46, 57, 78)
AVENUE_CYAN = (31, 182, 208)
AVENUE_AMBER = (214, 160, 52)
PANEL = (20, 26, 37)
CARD = (28, 36, 51)
CARD_EDGE = (44, 55, 76)
TEXT = (236, 240, 245)
TEXT_2 = (150, 162, 182)
TEXT_3 = (98, 110, 130)

EVENT = (232, 72, 245)       # tudo o que é do evento
CITY = (120, 200, 255)       # tudo o que é da cidade
CAR_IDLE = (46, 232, 122)    # carro livre
CAR_PICKUP = (255, 176, 32)  # a caminho de um passageiro
CAR_BUSY = (34, 211, 238)    # com passageiro
CAR_RELOC = (255, 176, 32)   # a reposicionar-se (contorno)

CAR_COLORS = {
    VehicleStatus.IDLE: CAR_IDLE,
    VehicleStatus.TO_PICKUP: CAR_PICKUP,
    VehicleStatus.BUSY: CAR_BUSY,
    VehicleStatus.RELOCATING: CAR_RELOC,
}

# ------------------------------------------------------------- dimensões
B = 22                 # píxeis entre cruzamentos (1 célula = 250 m)
MARGIN = 22
PANEL_W = 560
STREET_W = 5
AVENUE_EVERY = 5

SPEEDS = [0.5, 1, 2, 4, 8]       # multiplicadores de velocidade
BASE_STEPS_PER_SEC = 6           # passos do modelo por segundo, à velocidade x1


def font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("helveticaneue,helvetica,arial,dejavusans", size, bold=bold)


# =================================================================== mundo

class CityRenderer:
    """Desenha a cidade, a zona do evento, o estádio, os carros e os passageiros."""

    def __init__(self, model: RideshareModel) -> None:
        self.world = model.world
        self.n = self.world.width            # cruzamentos por lado
        self.size = (self.n - 1) * B + 2 * MARGIN
        self.background = self._build_background()
        self.crowd_spots: dict[int, tuple[float, float]] = {}

    # ---------------------------------------------------------- coordenadas

    def px(self, cell) -> tuple[float, float]:
        x, y = cell
        return MARGIN + x * B, MARGIN + (self.n - 1 - y) * B

    # ------------------------------------------------------------- fundo

    def _build_background(self) -> pygame.Surface:
        surf = pygame.Surface((self.size, self.size))
        surf.fill(BG)
        rng = random.Random(7)
        n = self.n

        # ruas
        for i in range(n):
            x, _ = self.px((i, 0))
            _, y = self.px((0, i))
            pygame.draw.line(surf, STREET, (x, MARGIN), (x, MARGIN + (n - 1) * B), STREET_W)
            pygame.draw.line(surf, STREET, (MARGIN, y), (MARGIN + (n - 1) * B, y), STREET_W)

        # quarteirões com prédios
        inner = B - STREET_W
        for i in range(n - 1):
            for j in range(n - 1):
                x0 = MARGIN + i * B + STREET_W // 2 + 1
                y0 = MARGIN + j * B + STREET_W // 2 + 1
                pygame.draw.rect(surf, BLOCK, (x0, y0, inner - 1, inner - 1), border_radius=2)
                for _ in range(rng.randint(1, 3)):
                    w = rng.randint(4, inner - 5)
                    h = rng.randint(4, inner - 5)
                    bx = x0 + rng.randint(1, inner - w - 2)
                    by = y0 + rng.randint(1, inner - h - 2)
                    pygame.draw.rect(surf, BUILDING, (bx, by, w, h))
                    pygame.draw.rect(surf, BUILDING_EDGE, (bx, by, w, h), 1)

        # avenidas (a cada 5 ruas) com linha luminosa
        glow = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        for k, i in enumerate(range(0, n, AVENUE_EVERY)):
            v_color = AVENUE_CYAN if k % 2 == 0 else AVENUE_AMBER
            h_color = AVENUE_AMBER if k % 2 == 0 else AVENUE_CYAN
            x, _ = self.px((i, 0))
            _, y = self.px((0, i))
            for width, alpha in ((5, 18), (1, 95)):
                pygame.draw.line(glow, (*v_color, alpha), (x, MARGIN), (x, MARGIN + (n - 1) * B), width)
                pygame.draw.line(glow, (*h_color, alpha), (MARGIN, y), (MARGIN + (n - 1) * B, y), width)
        surf.blit(glow, (0, 0))

        self._draw_event_zone(surf)
        self._draw_stadium(surf)
        return surf

    def _draw_event_zone(self, surf: pygame.Surface) -> None:
        cx, cy = self.px(self.world.stadium)
        r = (self.world.event_zone_radius + 0.5) * B
        diamond = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        layer = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.polygon(layer, (*EVENT, 26), diamond)
        for grow, width, alpha in ((10, 10, 18), (5, 6, 40), (0, 2, 210)):
            g = r + grow
            pts = [(cx, cy - g), (cx + g, cy), (cx, cy + g), (cx - g, cy)]
            pygame.draw.polygon(layer, (*EVENT, alpha), pts, width)
        surf.blit(layer, (0, 0))

    def _draw_stadium(self, surf: pygame.Surface) -> None:
        cx, cy = self.px(self.world.stadium)
        layer = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        for rad, alpha in ((44, 20), (38, 35), (33, 60)):
            pygame.draw.ellipse(layer, (*AVENUE_CYAN, alpha), (cx - rad * 1.15, cy - rad, rad * 2.3, rad * 2))
        surf.blit(layer, (0, 0))
        pygame.draw.ellipse(surf, (96, 106, 122), (cx - 34, cy - 29, 68, 58))
        pygame.draw.ellipse(surf, (132, 142, 158), (cx - 34, cy - 29, 68, 58), 2)
        pygame.draw.ellipse(surf, (70, 78, 92), (cx - 27, cy - 22, 54, 44))
        pitch = pygame.Rect(cx - 17, cy - 12, 34, 24)
        pygame.draw.rect(surf, (36, 140, 70), pitch, border_radius=3)
        pygame.draw.rect(surf, (210, 235, 215), pitch, 1, border_radius=3)
        pygame.draw.line(surf, (210, 235, 215), (cx, cy - 12), (cx, cy + 11), 1)
        pygame.draw.circle(surf, (210, 235, 215), (cx, cy), 5, 1)

    # ---------------------------------------------------- multidão do evento

    def crowd_spot(self, p) -> tuple[float, float]:
        """Lugar fixo (por pessoa) à volta do estádio, dentro da zona do evento."""
        if p.unique_id not in self.crowd_spots:
            rng = random.Random(p.unique_id)
            cx, cy = self.px(self.world.stadium)
            r_max = (self.world.event_zone_radius + 0.3) * B
            while True:
                dx, dy = rng.uniform(-r_max, r_max), rng.uniform(-r_max, r_max)
                if abs(dx) + abs(dy) <= r_max and (dx / 40) ** 2 + (dy / 34) ** 2 > 1:
                    break
            self.crowd_spots[p.unique_id] = (cx + dx, cy + dy)
        return self.crowd_spots[p.unique_id]

    # ------------------------------------------------------------- frame

    def draw(self, screen: pygame.Surface, model, prev_pos: dict, frac: float, t_anim: float) -> None:
        screen.blit(self.background, (0, 0))
        fx = pygame.Surface((self.size, self.size), pygame.SRCALPHA)

        # passageiros da cidade à espera (ponto branco com anel a pulsar)
        pulse = 0.5 + 0.5 * math.sin(t_anim * 4)
        for p in model.passengers:
            if p.ptype != PassengerType.CITY or p.status not in (RequestStatus.WAITING, RequestStatus.MATCHED):
                continue
            x, y = self.px(p.origin)
            x, y = x + 4, y - 4
            if p.status == RequestStatus.WAITING:
                pygame.draw.circle(fx, (*CITY, int(60 + 80 * pulse)), (x, y), 6 + 2 * pulse, 1)
                pygame.draw.circle(fx, (245, 248, 255, 255), (x, y), 3)
            else:
                pygame.draw.circle(fx, (245, 248, 255, 110), (x, y), 2.5)

        # multidão do evento
        for p in model.passengers:
            if p.ptype != PassengerType.EVENT or p.status not in (RequestStatus.WAITING, RequestStatus.MATCHED):
                continue
            x, y = self.crowd_spot(p)
            if p.status == RequestStatus.WAITING:
                pygame.draw.circle(fx, (*EVENT, 60), (x, y), 6)
                pygame.draw.circle(fx, (*EVENT, 255), (x, y), 3)
            else:
                pygame.draw.circle(fx, (*EVENT, 110), (x, y), 2)

        screen.blit(fx, (0, 0))

        # carros (posição interpolada entre passos, orientados pela direção)
        for v in model.vehicles:
            cur = self.px(v.pos)
            old = self.px(prev_pos.get(v.unique_id, v.pos))
            x = old[0] + (cur[0] - old[0]) * frac
            y = old[1] + (cur[1] - old[1]) * frac
            horizontal = abs(cur[0] - old[0]) >= abs(cur[1] - old[1])
            self._draw_car(screen, x, y, horizontal, v.status)

        # etiquetas
        cx, cy = self.px(self.world.stadium)
        _label(screen, "ESTÁDIO", (cx, cy + 40), font(13, True), TEXT)
        r = (self.world.event_zone_radius + 0.5) * B
        _label(screen, "ZONA DO EVENTO", (cx, cy + r + 16), font(12, True), EVENT)
        n_wait = sum(1 for p in model.passengers
                     if p.ptype == PassengerType.EVENT and p.status == RequestStatus.WAITING)
        if n_wait:
            f = font(13, True)
            txt = f.render(f"{n_wait} à espera de carro", True, TEXT)
            pill = txt.get_rect(midbottom=(cx, cy - r - 12)).inflate(18, 10)
            pygame.draw.rect(screen, (40, 18, 46), pill, border_radius=pill.h // 2)
            pygame.draw.rect(screen, EVENT, pill, 1, border_radius=pill.h // 2)
            screen.blit(txt, txt.get_rect(center=pill.center))

    def _draw_car(self, screen, x, y, horizontal, status) -> None:
        color = CAR_COLORS[status]
        w, h = (11, 6) if horizontal else (6, 11)
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (round(x), round(y))
        glow = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, 55), glow.get_rect(), border_radius=5)
        screen.blit(glow, (rect.x - 4, rect.y - 4))
        if status == VehicleStatus.RELOCATING:
            pygame.draw.rect(screen, color, rect, 2, border_radius=2)
        else:
            pygame.draw.rect(screen, color, rect, border_radius=2)
            win = rect.inflate(-6, -2) if horizontal else rect.inflate(-2, -6)
            pygame.draw.rect(screen, (15, 20, 28), win, border_radius=1)


# =================================================================== painel

def _label(screen, text, center, f, color) -> None:
    surf = f.render(text, True, color)
    shadow = f.render(text, True, (0, 0, 0))
    rect = surf.get_rect(center=center)
    screen.blit(shadow, rect.move(1, 1))
    screen.blit(surf, rect)


def _text(screen, text, pos, f, color, anchor="topleft") -> pygame.Rect:
    surf = f.render(text, True, color)
    rect = surf.get_rect(**{anchor: pos})
    screen.blit(surf, rect)
    return rect


def zone_stats(model, ptype) -> dict:
    ps = [p for p in model.passengers if p.ptype == ptype]
    waits = [p.wait_for_pickup for p in ps if p.t_pickup is not None]
    done = [p for p in ps if p.status in (RequestStatus.SERVED, RequestStatus.ABANDONED)]
    ab = sum(p.status == RequestStatus.ABANDONED for p in done)
    return {
        "waiting": sum(p.status == RequestStatus.WAITING for p in ps),
        "mean": float(np.mean(waits)) if waits else 0.0,
        "p90": float(np.percentile(waits, 90)) if waits else 0.0,
        "abandon": 100 * ab / len(done) if done else 0.0,
    }


def phase(model) -> tuple[str, tuple[int, int, int]]:
    t = model.time_min
    dur = model.params["demand"]["event"]["duration_min"]
    if not model.params["demand"]["event"]["enabled"]:
        return f"DIA NORMAL, SEM EVENTO ({t:+.0f} min)", CITY
    if t < 0:
        return f"ANTES DO FIM DO JOGO ({t:+.0f} min)", CITY
    if t < dur:
        return f"PICO PÓS-JOGO ({t:+.0f} min)", EVENT
    return f"DEPOIS DO PICO ({t:+.0f} min)", CAR_IDLE


class Panel:
    def __init__(self, x0: int, height: int) -> None:
        self.x0 = x0
        self.h = height
        self.history: list[tuple[float, int, int]] = []

    def record(self, model, ev, ci) -> None:
        self.history.append((model.time_min, ev["waiting"], ci["waiting"]))

    def card(self, screen, rect) -> None:
        pygame.draw.rect(screen, CARD, rect, border_radius=10)
        pygame.draw.rect(screen, CARD_EDGE, rect, 1, border_radius=10)

    def draw(self, screen, model, ev, ci, paused, speed, finished) -> None:
        x0, W = self.x0, PANEL_W
        pygame.draw.rect(screen, PANEL, (x0, 0, W, self.h))
        pad = 22
        x, w = x0 + pad, W - 2 * pad
        y = 20

        # título + fase
        _text(screen, "SIMULAÇÃO TVDE · TEMA 14", (x, y), font(26, True), TEXT)
        y += 42
        label, color = phase(model)
        if finished:
            label, color = "SIMULAÇÃO TERMINADA", TEXT_2
        badge = pygame.Rect(x, y, w, 42)
        pygame.draw.rect(screen, (*color[:3],), badge, 1, border_radius=8)
        tint = pygame.Surface(badge.size, pygame.SRCALPHA)
        pygame.draw.rect(tint, (*color, 30), tint.get_rect(), border_radius=8)
        screen.blit(tint, badge.topleft)
        _text(screen, f"FASE: {label}", badge.center, font(17, True), color, "center")
        y += 58

        # colunas evento vs cidade
        col_w = (w - 12) // 2
        cols = [(x, "ZONA DO EVENTO", EVENT, ev), (x + col_w + 12, "RESTO DA CIDADE", CITY, ci)]
        for cx, title, color, s in cols:
            _text(screen, title, (cx + col_w // 2, y), font(15, True), TEXT, "midtop")
            pygame.draw.line(screen, color, (cx, y + 24), (cx + col_w, y + 24), 3)
        y += 36
        rows = [
            ("Tempo de espera", "média / P90", lambda s: f"{s['mean']:.1f} / {s['p90']:.1f} min"),
            ("Desistências", "% dos pedidos resolvidos", lambda s: f"{s['abandon']:.1f}%"),
            ("À espera agora", "pessoas sem carro", lambda s: f"{s['waiting']}"),
        ]
        for title, sub, fmt in rows:
            for cx, _, color, s in cols:
                r = pygame.Rect(cx, y, col_w, 82)
                self.card(screen, r)
                _text(screen, title, (r.centerx, r.y + 10), font(14, True), TEXT, "midtop")
                _text(screen, sub, (r.centerx, r.y + 29), font(11), TEXT_3, "midtop")
                _text(screen, fmt(s), (r.centerx, r.y + 48), font(22, True), color, "midtop")
            y += 92

        # frota
        r = pygame.Rect(x, y, w, 66)
        self.card(screen, r)
        busy = sum(v.status != VehicleStatus.IDLE for v in model.vehicles)
        util = 100 * busy / max(len(model.vehicles), 1)
        _text(screen, "UTILIZAÇÃO DA FROTA", (r.x + 14, r.y + 10), font(14, True), TEXT)
        _text(screen, f"{util:.0f}%  ·  {len(model.vehicles) - busy} livres de {len(model.vehicles)}",
              (r.right - 14, r.y + 10), font(14, True), CAR_IDLE, "topright")
        bar = pygame.Rect(r.x + 14, r.y + 38, r.w - 28, 14)
        pygame.draw.rect(screen, (16, 21, 30), bar, border_radius=7)
        fill = bar.copy()
        fill.w = max(int(bar.w * util / 100), 1)
        pygame.draw.rect(screen, CAR_BUSY, fill, border_radius=7)
        y += 76

        # km vazios
        r = pygame.Rect(x, y, w, 52)
        self.card(screen, r)
        empty = sum(v.km_empty for v in model.vehicles)
        total = empty + sum(v.km_loaded for v in model.vehicles)
        _text(screen, "KM VAZIOS", (r.x + 14, r.y + 16), font(14, True), TEXT)
        _text(screen, f"{empty:,.0f} km  ·  {100 * empty / total if total else 0:.0f}% do total".replace(",", " "),
              (r.right - 14, r.y + 16), font(14, True), CAR_PICKUP, "topright")
        y += 62

        # mini-gráfico: pessoas à espera
        r = pygame.Rect(x, y, w, 150)
        self.card(screen, r)
        _text(screen, "PESSOAS À ESPERA AO LONGO DO TEMPO", (r.x + 14, r.y + 10), font(13, True), TEXT)
        self._sparkline(screen, pygame.Rect(r.x + 14, r.y + 34, r.w - 28, r.h - 50), model)
        y += 160

        # legenda
        r = pygame.Rect(x, y, w, 112)
        self.card(screen, r)
        _text(screen, "LEGENDA", (r.x + 14, r.y + 10), font(13, True), TEXT)
        items = [
            ("car", CAR_IDLE, "Carro livre"),
            ("car", CAR_PICKUP, "A caminho de um passageiro"),
            ("car", CAR_BUSY, "Com passageiro"),
            ("ring", CAR_RELOC, "A reposicionar-se"),
            ("dot", EVENT, "Pessoa à espera (evento)"),
            ("dot", (245, 248, 255), "Pedido à espera (cidade)"),
        ]
        for i, (kind, color, text) in enumerate(items):
            ix = r.x + 14 + (i % 2) * (w // 2)
            iy = r.y + 36 + (i // 2) * 24
            if kind == "car":
                pygame.draw.rect(screen, color, (ix, iy + 3, 14, 8), border_radius=2)
            elif kind == "ring":
                pygame.draw.rect(screen, color, (ix, iy + 3, 14, 8), 2, border_radius=2)
            else:
                pygame.draw.circle(screen, color, (ix + 7, iy + 7), 5)
            _text(screen, text, (ix + 22, iy), font(13), TEXT_2)
        y += 122

        state = "PAUSA" if paused else f"x{speed:g}"
        _text(screen, f"[Espaço] Pausar   [+/-] Velocidade ({state})   [R] Reiniciar",
              (x + w // 2, min(y, self.h - 24)), font(12), TEXT_3, "midtop")

    def _sparkline(self, screen, area, model) -> None:
        t0, t1 = model.start_min, model.end_min
        ymax = max(10, max((max(e, c) for _, e, c in self.history), default=10))

        def to_xy(t, v):
            return (area.x + (t - t0) / (t1 - t0) * area.w, area.bottom - v / ymax * area.h)

        pygame.draw.line(screen, CARD_EDGE, area.bottomleft, area.bottomright, 1)
        zx = to_xy(0, 0)[0]
        for yy in range(area.y, area.bottom, 6):
            pygame.draw.line(screen, TEXT_3, (zx, yy), (zx, yy + 3), 1)
        _text(screen, "fim do jogo", (zx - 4, area.bottom - 14), font(11), TEXT_3, "topright")
        _text(screen, f"{ymax:.0f}", (area.x, area.y), font(11), TEXT_3)
        for idx, color in ((2, CITY), (1, EVENT)):
            pts = [to_xy(h[0], h[idx]) for h in self.history]
            if len(pts) > 1:
                pygame.draw.lines(screen, color, False, pts, 2)
        _text(screen, "● evento", (area.right, area.y), font(11, True), EVENT, "topright")
        _text(screen, "● cidade", (area.right - 70, area.y), font(11, True), CITY, "topright")


# ==================================================================== app

class App:
    def __init__(self, args) -> None:
        self.args = args
        pygame.init()
        pygame.display.set_caption("Simulação TVDE · cidade + pico do evento")
        self.reset()
        # tudo é desenhado numa "tela" de tamanho fixo e depois ajustado à janela
        self.canvas_size = (self.city.size + PANEL_W, self.city.size)
        self.screen = pygame.Surface(self.canvas_size)
        if args.snapshot:
            self.window = pygame.display.set_mode((1, 1))
        else:
            info = pygame.display.Info()
            fit = min(0.95 * info.current_w / self.canvas_size[0],
                      0.85 * info.current_h / self.canvas_size[1], 1.0)
            size = (int(self.canvas_size[0] * fit), int(self.canvas_size[1] * fit))
            self.window = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

    def reset(self) -> None:
        params = load_params(self.args.config) if self.args.config else load_params()
        if self.args.vehicles:
            params["supply"]["n_vehicles"] = self.args.vehicles
        if self.args.no_event:
            params["demand"]["event"]["enabled"] = False
        self.model = RideshareModel(params=params, seed=self.args.seed)
        self.city = CityRenderer(self.model)
        self.panel = Panel(self.city.size, self.city.size)
        self.prev_pos = {v.unique_id: v.pos for v in self.model.vehicles}
        self.stats = (zone_stats(self.model, PassengerType.EVENT), zone_stats(self.model, PassengerType.CITY))
        self.speed_idx = 1
        self.paused = False
        self.acc = 0.0
        self.t_anim = 0.0

    def step_model(self) -> None:
        if not self.model.running:
            return
        self.prev_pos = {v.unique_id: v.pos for v in self.model.vehicles}
        self.model.step()
        ev = zone_stats(self.model, PassengerType.EVENT)
        ci = zone_stats(self.model, PassengerType.CITY)
        self.stats = (ev, ci)
        self.panel.record(self.model, ev, ci)

    def render(self, frac: float) -> None:
        self.city.draw(self.screen, self.model, self.prev_pos, frac, self.t_anim)
        ev, ci = self.stats
        self.panel.draw(self.screen, self.model, ev, ci, self.paused,
                        SPEEDS[self.speed_idx], not self.model.running)

    def present(self) -> None:
        """Copia a tela para a janela, à escala e centrada (sem deformar)."""
        ww, wh = self.window.get_size()
        cw, ch = self.canvas_size
        k = min(ww / cw, wh / ch)
        size = (max(1, int(cw * k)), max(1, int(ch * k)))
        self.window.fill(BG)
        scaled = pygame.transform.smoothscale(self.screen, size)
        self.window.blit(scaled, scaled.get_rect(center=(ww // 2, wh // 2)))

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000
            self.t_anim += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    pygame.quit()
                    return
                if e.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(e.size, pygame.RESIZABLE)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif e.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        self.speed_idx = min(self.speed_idx + 1, len(SPEEDS) - 1)
                    elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.speed_idx = max(self.speed_idx - 1, 0)
                    elif e.key == pygame.K_r:
                        self.reset()

            interval = 1 / (BASE_STEPS_PER_SEC * SPEEDS[self.speed_idx])
            if not self.paused and self.model.running:
                self.acc += dt
                while self.acc >= interval:
                    self.acc -= interval
                    self.step_model()
            frac = min(self.acc / interval, 1.0) if self.model.running else 1.0
            self.render(frac)
            self.present()
            pygame.display.flip()

    def snapshot(self, path: str, at_min: float) -> None:
        while self.model.running and self.model.time_min < at_min:
            self.step_model()
        self.render(1.0)
        pygame.image.save(self.screen, path)
        print(f"Imagem guardada em {path} (t = {self.model.time_min:+.0f} min)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Visualização Pygame da simulação TVDE.")
    ap.add_argument("--config", help="ficheiro YAML de parâmetros (por defeito config/base.yaml)")
    ap.add_argument("--vehicles", type=int, help="número de carros")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-event", action="store_true", help="dia normal, sem evento (E0)")
    ap.add_argument("--snapshot", help="guardar uma imagem em vez de abrir a janela")
    ap.add_argument("--at", type=float, default=15, help="minuto da imagem (com --snapshot)")
    args = ap.parse_args()

    if args.snapshot:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        App(args).snapshot(args.snapshot, args.at)
    else:
        App(args).run()


if __name__ == "__main__":
    main()