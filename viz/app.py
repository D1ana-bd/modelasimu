"""Visualização esquemática do modelo (Mesa + Solara).

Correr na raiz do repositório com:
    solara run viz/app.py
"""

from mesa.visualization import Slider, SolaraViz, make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle

from rideshare_sim.core.entities import VehicleStatus
from rideshare_sim.demand.passenger import Passenger
from rideshare_sim.model import RideshareModel
from rideshare_sim.supply.vehicle import Vehicle

VEHICLE_COLORS = {
    VehicleStatus.IDLE: "tab:green",        # livre
    VehicleStatus.TO_PICKUP: "tab:orange",  # a caminho da recolha
    VehicleStatus.BUSY: "tab:blue",         # com passageiro
    VehicleStatus.RELOCATING: "tab:gray",   # a reposicionar-se
}


def agent_portrayal(agent):
    if isinstance(agent, Passenger):
        # passageiros à espera no estádio
        return AgentPortrayalStyle(color="tab:red", marker="s", size=120, zorder=2)
    if isinstance(agent, Vehicle):
        return AgentPortrayalStyle(color=VEHICLE_COLORS[agent.status], marker="o", size=18, zorder=3)
    return AgentPortrayalStyle()


model_params = {
    "n_vehicles": Slider("Número de carros", 250, 10, 500, 10),
    "request_rate_per_min": Slider("Pedidos por minuto", 20, 1, 50, 1),
    "patience_mean_min": Slider("Paciência média (min)", 15, 1, 40, 1),
}

grid_view = make_space_component(agent_portrayal)
queue_plot = make_plot_component(["Waiting", "Served", "Abandoned"])
fleet_plot = make_plot_component(["Idle vehicles", "Busy vehicles"])

model = RideshareModel()

page = SolaraViz(
    model,
    components=[grid_view, queue_plot, fleet_plot],
    model_params=model_params,
    name="TVDE no pico pós-jogo",
)
