"""Visualização esquemática do modelo (Mesa + Solara).

Correr na raiz do repositório com:
    solara run viz/app.py

Versão base do Passo 1. Melhorada em feature/visualization
(zona do evento sombreada, legenda, tempo em minutos, painel de KPIs).
"""

from mesa.visualization import Slider, SolaraViz, make_plot_component, make_space_component
from mesa.visualization.components import AgentPortrayalStyle

from rideshare_sim.core.entities import PassengerType, VehicleStatus
from rideshare_sim.demand.passenger import Passenger
from rideshare_sim.model import RideshareModel
from rideshare_sim.supply.vehicle import Vehicle

VEHICLE_COLORS = {
    VehicleStatus.IDLE: "tab:green",        # livre
    VehicleStatus.TO_PICKUP: "tab:orange",  # a caminho da recolha
    VehicleStatus.BUSY: "tab:blue",         # com passageiro
    VehicleStatus.RELOCATING: "tab:gray",   # a reposicionar-se
}

PASSENGER_COLORS = {
    PassengerType.CITY: "tab:purple",  # pedido normal da cidade
    PassengerType.EVENT: "tab:red",    # pedido do evento (no estádio)
}


def agent_portrayal(agent):
    if isinstance(agent, Passenger):
        return AgentPortrayalStyle(color=PASSENGER_COLORS[agent.ptype], marker="s", size=40, zorder=2)
    if isinstance(agent, Vehicle):
        return AgentPortrayalStyle(color=VEHICLE_COLORS[agent.status], marker="o", size=18, zorder=3)
    return AgentPortrayalStyle()


model_params = {
    "n_vehicles": Slider("Número de carros", 150, 10, 400, 10),
    "city_rate_per_min": Slider("Pedidos normais por minuto", 5, 0, 20, 1),
    "peak_rate_per_min": Slider("Pico do evento (pedidos/min)", 20, 0, 50, 1),
    "patience_mean_min": Slider("Paciência média (min)", 10, 1, 30, 1),
}

grid_view = make_space_component(agent_portrayal)
waiting_plot = make_plot_component(["Waiting (city)", "Waiting (event)"])
abandon_plot = make_plot_component(["Abandoned (city)", "Abandoned (event)"])
fleet_plot = make_plot_component(["Idle vehicles", "Busy vehicles"])

model = RideshareModel()

page = SolaraViz(
    model,
    components=[grid_view, waiting_plot, abandon_plot, fleet_plot],
    model_params=model_params,
    name="TVDE: cidade + pico do evento",
)