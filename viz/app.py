"""Visualização da simulação (Mesa + Solara).

Correr na raiz do repositório com:
    solara run viz/app.py

Mostra:
    - um painel com o relógio e os números principais (evento vs. cidade);
    - o mapa esquemático da cidade, com a zona do evento e o estádio;
    - três gráficos ao longo do tempo (em minutos, com o fim do jogo marcado).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import solara  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Polygon, Rectangle  # noqa: E402
from mesa.visualization import Slider, SolaraViz  # noqa: E402
from mesa.visualization.utils import update_counter  # noqa: E402

from rideshare_sim.core.entities import PassengerType, RequestStatus, VehicleStatus  # noqa: E402
from rideshare_sim.model import RideshareModel  # noqa: E402

# ------------------------------------------------------------------ cores
# Paleta validada para daltonismo (evento, cidade, carro livre).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3de"
EVENT = "#eb6834"        # tudo o que é do evento
EVENT_ZONE = "#fbe3d8"   # fundo da zona do evento
CITY = "#2a78d6"         # tudo o que é da cidade
FREE = "#1baf7a"         # carro livre
TO_PICKUP = "#52514e"    # carro a caminho de um passageiro
BUSY = "#b8b7b0"         # carro com passageiro

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# --------------------------------------------------------------- auxiliares

def _clock_text(t: float) -> tuple[str, str]:
    if t < 0:
        return f"{t:+.0f} min", f"faltam {-t:.0f} min para o fim do jogo"
    if t == 0:
        return "0 min", "o jogo acabou agora"
    return f"+{t:.0f} min", f"{t:.0f} min depois do fim do jogo"


def _zone_stats(model, ptype):
    ps = [p for p in model.passengers if p.ptype == ptype]
    waiting = sum(p.status == RequestStatus.WAITING for p in ps)
    done = [p for p in ps if p.status in (RequestStatus.SERVED, RequestStatus.ABANDONED)]
    abandoned = sum(p.status == RequestStatus.ABANDONED for p in done)
    waits = [p.wait_for_pickup for p in ps if p.t_pickup is not None]
    pct = 100 * abandoned / len(done) if done else 0.0
    mean_wait = sum(waits) / len(waits) if waits else 0.0
    return waiting, pct, mean_wait


# ------------------------------------------------------------- componentes

@solara.component
def Dashboard(model):
    """Relógio + números principais."""
    update_counter.get()
    big, small = _clock_text(model.time_min)
    ev_wait, ev_pct, ev_mean = _zone_stats(model, PassengerType.EVENT)
    ci_wait, ci_pct, ci_mean = _zone_stats(model, PassengerType.CITY)
    free = sum(v.status == VehicleStatus.IDLE for v in model.vehicles)
    total = len(model.vehicles)

    card = "padding:14px 18px;border-radius:12px;background:#ffffff;border:1px solid #e4e3de;min-width:170px;flex:1;"
    label = "font-size:12px;color:#52514e;margin:0 0 4px 0;"
    value = "font-size:26px;font-weight:600;color:#0b0b0b;margin:0;line-height:1.2;"
    sub = "font-size:12px;color:#52514e;margin:4px 0 0 0;"

    def zone_card(title, color, waiting, pct, mean):
        return f"""
        <div style="{card}border-top:4px solid {color};">
          <p style="{label}"><b style="color:{color}">●</b> {title}</p>
          <p style="{value}">{pct:.0f}% <span style="font-size:13px;font-weight:400;color:#52514e">desistem</span></p>
          <p style="{sub}">{waiting} à espera · espera média {mean:.1f} min</p>
        </div>"""

    solara.HTML(tag="div", unsafe_innerHTML=f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;font-family:sans-serif;width:100%;">
      <div style="{card}">
        <p style="{label}">Relógio</p>
        <p style="{value}">{big}</p>
        <p style="{sub}">{small}</p>
      </div>
      {zone_card("Zona do evento", EVENT, ev_wait, ev_pct, ev_mean)}
      {zone_card("Resto da cidade", CITY, ci_wait, ci_pct, ci_mean)}
      <div style="{card}border-top:4px solid {FREE};">
        <p style="{label}"><b style="color:{FREE}">●</b> Frota</p>
        <p style="{value}">{free} <span style="font-size:13px;font-weight:400;color:#52514e">de {total} livres</span></p>
        <p style="{sub}">{100 * (total - free) / max(total, 1):.0f}% dos carros ocupados</p>
      </div>
    </div>""")


@solara.component
def CityMap(model):
    """Mapa esquemático: cidade, zona do evento, estádio, carros e pedidos à espera."""
    update_counter.get()
    w = model.world
    fig = Figure(figsize=(6.4, 6.4), facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)

    # ruas (linhas finas a cada 5 células) e limite da cidade
    for k in range(0, w.width + 1, 5):
        ax.axvline(k - 0.5, color=GRID, lw=0.6, zorder=0)
        ax.axhline(k - 0.5, color=GRID, lw=0.6, zorder=0)
    ax.add_patch(Rectangle((-0.5, -0.5), w.width, w.height, fill=False, ec=INK_2, lw=1, zorder=1))

    # zona do evento (losango = distância Manhattan ≤ raio)
    sx, sy = w.stadium
    r = w.event_zone_radius + 0.5
    ax.add_patch(Polygon([(sx, sy + r), (sx + r, sy), (sx, sy - r), (sx - r, sy)],
                         closed=True, fc=EVENT_ZONE, ec=EVENT, lw=1, zorder=1))

    # carros por estado
    groups = {
        VehicleStatus.BUSY: ([], BUSY, "o", 14),
        VehicleStatus.TO_PICKUP: ([], TO_PICKUP, "o", 14),
        VehicleStatus.IDLE: ([], FREE, "o", 18),
        VehicleStatus.RELOCATING: ([], FREE, "o", 18),
    }
    for v in model.vehicles:
        groups[v.status][0].append(v.pos)
    for status, (pts, color, marker, size) in groups.items():
        if pts:
            xs, ys = zip(*pts)
            hollow = status == VehicleStatus.RELOCATING
            ax.scatter(xs, ys, s=size, marker=marker, zorder=3,
                       facecolors="none" if hollow else color,
                       edgecolors=color, linewidths=1.2 if hollow else 0)

    # pedidos da cidade à espera
    city_wait = [p.origin for p in model.passengers
                 if p.ptype == PassengerType.CITY and p.status == RequestStatus.WAITING]
    if city_wait:
        xs, ys = zip(*city_wait)
        ax.scatter(xs, ys, s=34, marker="^", color=CITY, edgecolors=SURFACE, linewidths=0.8, zorder=4)

    # estádio + quantos esperam lá
    ax.scatter([sx], [sy], s=160, marker="s", color=EVENT, edgecolors=SURFACE, linewidths=1.5, zorder=5)
    ev_wait = sum(1 for p in model.passengers
                  if p.ptype == PassengerType.EVENT and p.status == RequestStatus.WAITING)
    ax.annotate(f"Estádio · {ev_wait} à espera", (sx, sy), xytext=(sx + 4.5, sy + 5.5),
                fontsize=10, fontweight="bold", color=INK, zorder=6,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=EVENT, lw=1),
                arrowprops=dict(arrowstyle="-", color=EVENT, lw=1))

    ax.set_xlim(-1, w.width)
    ax.set_ylim(-1, w.height)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)
    big, _ = _clock_text(model.time_min)
    ax.set_title(f"Cidade  ·  {big}", loc="left", fontsize=12, fontweight="bold", color=INK)

    legend = [
        Line2D([], [], marker="s", ls="", color=EVENT, markersize=8, label="Estádio"),
        Line2D([], [], marker="^", ls="", color=CITY, markersize=7, label="Pedido da cidade à espera"),
        Line2D([], [], marker="o", ls="", color=FREE, markersize=6, label="Carro livre"),
        Line2D([], [], marker="o", ls="", color=TO_PICKUP, markersize=6, label="Carro a caminho de um passageiro"),
        Line2D([], [], marker="o", ls="", color=BUSY, markersize=6, label="Carro com passageiro"),
        Line2D([], [], marker="o", ls="", mfc="none", mec=FREE, markersize=6, label="Carro a reposicionar-se"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2,
              frameon=False, fontsize=9, labelcolor=INK_2)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


def _time_chart(model, series, title, ylabel, ymax=None):
    df = model.datacollector.get_model_vars_dataframe()
    fig = Figure(figsize=(5.6, 2.7), facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    p = model.params["time"]
    ax.axvspan(0, model.params["demand"]["event"]["duration_min"], color=EVENT_ZONE, alpha=0.5, lw=0, zorder=0)
    ax.axvline(0, color=INK_2, lw=1, ls="--", zorder=1)
    ax.text(-1.5, 0.97, "fim do jogo", transform=ax.get_xaxis_transform(),
            fontsize=8.5, color=INK_2, va="top", ha="right")
    top = ymax if ymax else max(5, 1.15 * max((df[c].max() for c, _, _ in series), default=5))
    ends = [df[c].iloc[-1] for c, _, _ in series] if len(df) else []
    # etiqueta no fim de cada linha, só se as linhas não estiverem coladas (senão fica só a legenda)
    label_ends = len(ends) < 2 or abs(ends[0] - ends[1]) > 0.08 * top
    for col, label, color in series:
        ax.plot(df["Minute"], df[col], color=color, lw=2, label=label, zorder=3)
        if len(df) and label_ends:
            ax.annotate(label, (df["Minute"].iloc[-1], df[col].iloc[-1]), xytext=(4, 0),
                        textcoords="offset points", fontsize=8.5, color=INK_2, va="center")
    ax.set_xlim(p["start_min"], p["end_min"] + 18)
    ax.set_ylim(0, top)
    ax.set_xlabel("minutos em relação ao fim do jogo")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=INK)
    handles, _ = ax.get_legend_handles_labels()
    if len(series) < 2:
        handles = []  # uma só série: o título já a identifica
    handles.append(Patch(color=EVENT_ZONE, label="Pico do evento"))
    ax.legend(handles=handles, frameon=False, fontsize=8.5, loc="upper right", labelcolor=INK_2)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def WaitingChart(model):
    update_counter.get()
    _time_chart(model, [("Waiting (event)", "Evento", EVENT), ("Waiting (city)", "Cidade", CITY)],
                "Pessoas à espera de carro", "pessoas")


@solara.component
def AbandonChart(model):
    update_counter.get()
    _time_chart(model, [("Abandoned % (event)", "Evento", EVENT), ("Abandoned % (city)", "Cidade", CITY)],
                "Desistências acumuladas", "% dos pedidos", ymax=100)


@solara.component
def FleetChart(model):
    update_counter.get()
    _time_chart(model, [("Busy %", "Ocupados", TO_PICKUP)], "Carros ocupados", "% da frota", ymax=100)


# ------------------------------------------------------------- página

model_params = {
    "n_vehicles": Slider("Número de carros", 150, 10, 400, 10),
    "city_rate_per_min": Slider("Pedidos normais por minuto", 5, 0, 20, 1),
    "peak_rate_per_min": Slider("Pico do evento (pedidos/min)", 20, 0, 50, 1),
    "patience_mean_min": Slider("Paciência média (min)", 10, 1, 30, 1),
}

model = RideshareModel()

page = SolaraViz(
    model,
    components=[Dashboard, CityMap, WaitingChart, AbandonChart, FleetChart],
    model_params=model_params,
    name="TVDE: cidade + pico do evento",
)
