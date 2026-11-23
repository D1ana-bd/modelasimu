import math
import random
import pygame

# ==============================================================================
# CONFIGURAÇÕES VISUAIS & PALETA DE CORES
# ==============================================================================
GRID_SIZE = 41          # 41x41 células (conforme proposta)
CELL_PX = 20            # 41 * 20 = 820px de altura/largura do mapa
MAP_W = GRID_SIZE * CELL_PX
HUD_W = 380
WIDTH = MAP_W + HUD_W
HEIGHT = MAP_W
FPS = 60

# Cores (Dark Urban Theme)
BG_DARK      = (15, 19, 26)
ROAD_COLOR   = (24, 30, 40)
ROAD_LINE    = (38, 47, 63)
BLOCK_BASE   = (20, 25, 34)
BUILDING_COL = (29, 36, 49)
HUD_BG       = (18, 22, 30)
CARD_BG      = (25, 31, 43)
CARD_BORDER  = (45, 56, 76)

# Cores Semânticas dos Agentes
COL_IDLE     = (46, 213, 115)   # Verde: Livre
COL_ENROUTE  = (255, 165, 2)    # Âmbar: A caminho / Reposicionamento
COL_OCCUPIED = (0, 210, 211)    # Ciano: Ocupado
COL_PAX_EVT  = (255, 56, 225)   # Magenta: Passageiro do evento
COL_PAX_CITY = (241, 242, 246)  # Branco: Passageiro cidade
COL_TEXT     = (235, 240, 248)
COL_MUTED    = (140, 152, 173)


# ==============================================================================
# 1. GERADOR DO MAPA URBANO EM CACHE (Ruas, Quarteirões e Estádio)
# ==============================================================================
def build_city_background(stadium_cell=(20, 20), event_radius_cells=3):
    surf = pygame.Surface((MAP_W, HEIGHT))
    surf.fill(ROAD_COLOR)

    rng = random.Random(42)  # Semente fixa para os prédios não mudarem

    # Desenhar quarteirões entre as linhas da grelha (cada célula = cruzamento/rua)
    for gx in range(GRID_SIZE):
        for gy in range(GRID_SIZE):
            px, py = gx * CELL_PX, gy * CELL_PX

            # Eixos da rua (cruzamento)
            pygame.draw.line(surf, ROAD_LINE, (px, py + CELL_PX // 2), (px + CELL_PX, py + CELL_PX // 2), 1)
            pygame.draw.line(surf, ROAD_LINE, (px + CELL_PX // 2, py), (px + CELL_PX // 2, py + CELL_PX), 1)

            # Quarteirões nos 4 cantos da célula (edifícios estilizados)
            if abs(gx - stadium_cell[0]) > 2 or abs(gy - stadium_cell[1]) > 2:
                for dx, dy in [(2, 2), (CELL_PX // 2 + 2, 2), (2, CELL_PX // 2 + 2), (CELL_PX // 2 + 2, CELL_PX // 2 + 2)]:
                    if rng.random() > 0.22:
                        bw = rng.randint(4, CELL_PX // 2 - 3)
                        bh = rng.randint(4, CELL_PX // 2 - 3)
                        pygame.draw.rect(surf, BUILDING_COL, (px + dx, py + dy, bw, bh), border_radius=1)

    # Centro do estádio em píxeis
    cx = stadium_cell[0] * CELL_PX + CELL_PX // 2
    cy = stadium_cell[1] * CELL_PX + CELL_PX // 2
    radius_px = event_radius_cells * CELL_PX + 14

    # Halo translúcido da Zona do Evento (raio de 3 células)
    halo = pygame.Surface((radius_px * 3, radius_px * 3), pygame.SRCALPHA)
    h_center = (radius_px * 3 // 2, radius_px * 3 // 2)
    pygame.draw.circle(halo, (0, 210, 211, 25), h_center, int(radius_px * 1.15))
    pygame.draw.circle(halo, (0, 210, 211, 160), h_center, radius_px, width=3)
    pygame.draw.circle(halo, (255, 195, 18, 140), h_center, int(radius_px * 0.78), width=2)
    surf.blit(halo, (cx - h_center[0], cy - h_center[1]))

    # Ícone top-down do Estádio
    stad_rect = pygame.Rect(0, 0, 44, 54)
    stad_rect.center = (cx, cy)
    pygame.draw.rect(surf, (115, 125, 140), stad_rect, border_radius=18)
    pygame.draw.rect(surf, (45, 52, 64), stad_rect.inflate(-10, -10), border_radius=14)
    pitch_rect = stad_rect.inflate(-22, -22)
    pygame.draw.rect(surf, (39, 130, 75), pitch_rect, border_radius=3)
    pygame.draw.rect(surf, (180, 220, 190), pitch_rect, width=1)

    # Etiquetas do estádio
    font_b = pygame.font.SysFont("SF Pro Display", 12, bold=True)
    font_s = pygame.font.SysFont("SF Pro Display", 11, bold=True)
    lbl_est = font_b.render("ESTÁDIO", True, (255, 255, 255))
    surf.blit(lbl_est, lbl_est.get_rect(center=(cx, cy)))

    lbl_zona = font_s.render("ZONA DO EVENTO (3 cél.)", True, (0, 230, 230))
    surf.blit(lbl_zona, lbl_zona.get_rect(center=(cx, cy + radius_px + 12)))

    return surf


# ==============================================================================
# 2. DESENHO DOS AGENTES (Carros orientados & Passageiros com brilho)
# ==============================================================================
def draw_car(surf, px, py, state, direction=(1, 0)):
    color = {
        "livre": COL_IDLE,
        "a_caminho": COL_ENROUTE,
        "a_reposicionar": COL_ENROUTE,
        "ocupado": COL_OCCUPIED,
    }.get(state, COL_IDLE)

    # Superfície pequena para rodar o carro consoante a direção
    car_s = pygame.Surface((16, 10), pygame.SRCALPHA)
    pygame.draw.rect(car_s, color, (1, 1, 14, 8), border_radius=3)
    # Para-brisas e vidro traseiro
    pygame.draw.rect(car_s, (15, 20, 28), (4, 2, 3, 6), border_radius=1)
    pygame.draw.rect(car_s, (15, 20, 28), (10, 2, 2, 6), border_radius=1)
    # Faróis frontais
    pygame.draw.circle(car_s, (255, 250, 200), (14, 3), 1)
    pygame.draw.circle(car_s, (255, 250, 200), (14, 7), 1)

    angle = -math.degrees(math.atan2(direction[1], direction[0]))
    rotated = pygame.transform.rotate(car_s, angle)
    surf.blit(rotated, rotated.get_rect(center=(px, py)))


def draw_passenger(surf, px, py, pax_type, jitter=(0, 0)):
    jx, jy = px + jitter[0], py + jitter[1]
    if pax_type == "evento":
        # Halo suave magenta para destacar aglomeração no estádio
        glow = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 56, 225, 70), (8, 8), 7)
        surf.blit(glow, (jx - 8, jy - 8))
        pygame.draw.circle(surf, COL_PAX_EVT, (jx, jy), 3)
    else:
        pygame.draw.circle(surf, COL_PAX_CITY, (jx, jy), 3)


# ==============================================================================
# 3. PAINEL LATERAL (HUD DE TELEMETRIA E KPIs)
# ==============================================================================
def draw_hud(surf, kpis, paused, steps_per_sec):
    x0 = MAP_W
    pygame.draw.rect(surf, HUD_BG, (x0, 0, HUD_W, HEIGHT))
    pygame.draw.line(surf, CARD_BORDER, (x0, 0), (x0, HEIGHT), 2)

    f_title = pygame.font.SysFont("SF Pro Display", 20, bold=True)
    f_sub   = pygame.font.SysFont("SF Pro Display", 13, bold=True)
    f_val   = pygame.font.SysFont("SF Pro Display", 19, bold=True)
    f_lbl   = pygame.font.SysFont("SF Pro Display", 12)

    pad = 20
    y = 22

    # Título & Badge de Fase
    surf.blit(f_title.render("SIMULAÇÃO TVDE - TEMA 14", True, COL_TEXT), (x0 + pad, y))
    y += 34
    badge_rect = pygame.Rect(x0 + pad, y, HUD_W - 2 * pad, 32)
    pygame.draw.rect(surf, (30, 45, 65), badge_rect, border_radius=6)
    pygame.draw.rect(surf, (65, 130, 190), badge_rect, width=1, border_radius=6)
    fase_txt = f"FASE: {kpis['fase']} ({kpis['minuto']:+d} min)"
    surf.blit(f_sub.render(fase_txt, True, (130, 200, 255)), (x0 + pad + 12, y + 8))
    y += 48

    # Cabeçalhos das colunas: Zona Evento vs Resto da Cidade
    col_w = (HUD_W - 3 * pad) // 2
    surf.blit(f_sub.render("ZONA EVENTO", True, COL_ENROUTE), (x0 + pad + 18, y))
    surf.blit(f_sub.render("RESTO DA CIDADE", True, COL_OCCUPIED), (x0 + 2 * pad + col_w + 8, y))
    y += 22

    def draw_kpi_card(cx, cy, title, sub, val, val_color):
        r = pygame.Rect(cx, cy, col_w, 76)
        pygame.draw.rect(surf, CARD_BG, r, border_radius=8)
        pygame.draw.rect(surf, CARD_BORDER, r, width=1, border_radius=8)
        surf.blit(f_sub.render(title, True, COL_TEXT), (cx + 12, cy + 10))
        surf.blit(f_lbl.render(sub, True, COL_MUTED), (cx + 12, cy + 28))
        surf.blit(f_val.render(val, True, val_color), (cx + 12, cy + 46))

    # Cartões de Tempo de Espera (Médio / P90)
    draw_kpi_card(x0 + pad, y, "Tempo de Espera", "Médio / P90 (min)",
                  f"{kpis['wait_evt_avg']:.1f}m / {kpis['wait_evt_p90']:.1f}m", COL_ENROUTE)
    draw_kpi_card(x0 + 2 * pad + col_w, y, "Tempo de Espera", "Médio / P90 (min)",
                  f"{kpis['wait_city_avg']:.1f}m / {kpis['wait_city_p90']:.1f}m", COL_OCCUPIED)
    y += 88

    # Cartões de % Desistências
    draw_kpi_card(x0 + pad, y, "% Desistências", "Abandonados / Total",
                  f"{kpis['drop_evt']:.1f}%", COL_ENROUTE)
    draw_kpi_card(x0 + 2 * pad + col_w, y, "% Desistências", "Abandonados / Total",
                  f"{kpis['drop_city']:.1f}%", COL_OCCUPIED)
    y += 96

    # Barra de Utilização da Frota
    r_util = pygame.Rect(x0 + pad, y, HUD_W - 2 * pad, 62)
    pygame.draw.rect(surf, CARD_BG, r_util, border_radius=8)
    pygame.draw.rect(surf, CARD_BORDER, r_util, width=1, border_radius=8)
    surf.blit(f_sub.render("UTILIZAÇÃO DA FROTA", True, COL_TEXT), (x0 + pad + 12, y + 10))
    util_pct = kpis["utilizacao"]
    surf.blit(f_sub.render(f"{util_pct:.0f}%", True, COL_OCCUPIED), (x0 + HUD_W - pad - 45, y + 10))
    bar_bg = pygame.Rect(x0 + pad + 12, y + 36, HUD_W - 2 * pad - 24, 12)
    pygame.draw.rect(surf, (15, 20, 28), bar_bg, border_radius=6)
    bar_fg = pygame.Rect(bar_bg.x, bar_bg.y, int(bar_bg.w * (util_pct / 100.0)), bar_bg.h)
    pygame.draw.rect(surf, COL_IDLE, bar_fg, border_radius=6)
    y += 74

    # Cartão Km Vazios
    r_km = pygame.Rect(x0 + pad, y, HUD_W - 2 * pad, 56)
    pygame.draw.rect(surf, CARD_BG, r_km, border_radius=8)
    pygame.draw.rect(surf, CARD_BORDER, r_km, width=1, border_radius=8)
    surf.blit(f_sub.render("KM VAZIOS DO SISTEMA", True, COL_TEXT), (x0 + pad + 12, y + 10))
    surf.blit(f_val.render(f"{kpis['km_vazios']:.1f} km", True, COL_TEXT), (x0 + pad + 12, y + 29))
    surf.blit(f_lbl.render(f"Vel: {steps_per_sec} steps/s", True, COL_IDLE if not paused else COL_ENROUTE),
              (x0 + HUD_W - pad - 110, y + 33))
    y += 72

    # Legenda
    surf.blit(f_sub.render("LEGENDA", True, COL_TEXT), (x0 + pad, y))
    y += 24
    leg_items = [
        (COL_IDLE, "Carro Livre"),
        (COL_ENROUTE, "A caminho / Reposic."),
        (COL_OCCUPIED, "Carro Ocupado"),
        (COL_PAX_EVT, "Passageiro Evento"),
        (COL_PAX_CITY, "Passageiro Cidade"),
    ]
    for i, (col, label) in enumerate(leg_items):
        lx = x0 + pad + (i % 2) * 175
        ly = y + (i // 2) * 24
        pygame.draw.rect(surf, col, (lx, ly + 2, 12, 12), border_radius=3)
        surf.blit(f_lbl.render(label, True, COL_TEXT), (lx + 18, ly + 1))

    # Rodapé de Controlos
    ctrl_txt = "[Espaço] Pausar  |  [+/-] Velocidade  |  [R] Reiniciar"
    surf.blit(f_lbl.render(ctrl_txt, True, COL_MUTED), (x0 + pad, HEIGHT - 28))


# ==============================================================================
# 4. LOOP PRINCIPAL (Exemplo pronto a ligar ao teu modelo Mesa)
# ==============================================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TVDE Fleet Simulation - Tema 14 (Mesa + Pygame)")
    clock = pygame.time.Clock()

    background = build_city_background(stadium_cell=(20, 20), event_radius_cells=3)

    # --------------------------------------------------------------------------
    # LIGAR AO MESA: Substitui esta secção pela inicialização do teu TVDEModel:
    # model = TVDEModel(num_carros=150, matching="lote", reposicionamento=True, limite_x=0.3)
    # --------------------------------------------------------------------------
    rng = random.Random(14)
    demo_cars = [
        {"x": rng.randint(0, 40), "y": rng.randint(0, 40), "px": 0, "py": 0,
         "state": rng.choice(["livre", "a_caminho", "ocupado"]), "dir": (1, 0)}
        for _ in range(90)
    ]
    for c in demo_cars:
        c["px"], c["py"] = c["x"], c["y"]

    demo_pax = []
    for _ in range(180):
        # Concentração perto do estádio (20, 20)
        ex = int(max(0, min(40, rng.gauss(20, 2.2))))
        ey = int(max(0, min(40, rng.gauss(20, 2.2))))
        demo_pax.append({"x": ex, "y": ey, "type": "evento", "jitter": (rng.randint(-6, 6), rng.randint(-6, 6))})
    for _ in range(25):
        demo_pax.append({"x": rng.randint(0, 40), "y": rng.randint(0, 40), "type": "cidade", "jitter": (0, 0)})

    paused = False
    steps_per_sec = 4
    step_timer = 0.0
    step_count = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    steps_per_sec = min(30, steps_per_sec + 2)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    steps_per_sec = max(1, steps_per_sec - 2)
                elif event.key == pygame.K_r:
                    step_count = 0  # Aqui reinicias o model = TVDEModel(...)

        # Avançar 1 step do Mesa consoante a velocidade escolhida
        if not paused:
            step_timer += dt
            step_interval = 1.0 / steps_per_sec
            if step_timer >= step_interval:
                step_timer -= step_interval
                step_count += 1

                # LIGAR AO MESA:
                # for car in model.carros: car.prev_pos = car.pos
                # model.step()

                # Movimento dummy apenas para demonstração visual:
                for c in demo_cars:
                    c["px"], c["py"] = c["x"], c["y"]
                    dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                    c["x"] = max(0, min(40, c["x"] + dx))
                    c["y"] = max(0, min(40, c["y"] + dy))
                    c["dir"] = (dx, dy)

        # Fator de interpolação suave (0.0 -> 1.0) entre o step anterior e o atual
        alpha = min(1.0, step_timer * steps_per_sec) if not paused else 1.0

        # 1. Desenhar fundo urbano
        screen.blit(background, (0, 0))

        # 2. Desenhar passageiros à espera
        for p in demo_pax:
            px = p["x"] * CELL_PX + CELL_PX // 2
            py = p["y"] * CELL_PX + CELL_PX // 2
            draw_passenger(screen, px, py, p["type"], p["jitter"])

        # 3. Desenhar carros interpolados nas ruas
        for c in demo_cars:
            ix = (c["px"] + (c["x"] - c["px"]) * alpha) * CELL_PX + CELL_PX // 2
            iy = (c["py"] + (c["y"] - c["py"]) * alpha) * CELL_PX + CELL_PX // 2
            draw_car(screen, ix, iy, c["state"], c["dir"])

        # 4. Ler KPIs reais do teu model.datacollector e desenhar HUD
        minuto_relativo = -60 + (step_count // 2)  # Cada passo = 30s (2 passos = 1 min)
        kpis = {
            "fase": "PICO PÓS-JOGO" if minuto_relativo >= 0 else "PRÉ-JOGO",
            "minuto": minuto_relativo,
            "wait_evt_avg": 14.5,
            "wait_evt_p90": 24.1,
            "wait_city_avg": 4.2,
            "wait_city_p90": 8.5,
            "drop_evt": 18.4,
            "drop_city": 2.1,
            "utilizacao": 94.0,
            "km_vazios": 142.8,
        }
        draw_hud(screen, kpis, paused, steps_per_sec)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()