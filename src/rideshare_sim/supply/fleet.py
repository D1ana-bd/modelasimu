"""Criação da frota.

PLACEHOLDER: `n_vehicles` carros livres espalhados à volta do estádio.
Substituído em feature/supply-calibration (frota calibrada com NYC).
"""

from __future__ import annotations

from rideshare_sim.supply.vehicle import Vehicle


def create_fleet(model) -> list[Vehicle]:
    s = model.params["supply"]
    fleet = []
    for _ in range(s["n_vehicles"]):
        v = Vehicle(model)
        cell = model.world.random_cell_near_stadium(model.rng, s["initial_radius_cells"])
        model.grid.place_agent(v, cell)
        fleet.append(v)
    return fleet