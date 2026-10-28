"""Frota disponível no início da simulação.

PLACEHOLDER: substituído em feature/supply-data
(frota inicial e chegada de carros calibradas com os dados reais).
"""

from __future__ import annotations

import numpy as np

from rideshare_sim.core.entities import Vehicle


def create_fleet(params: dict, rng: np.random.Generator) -> list[Vehicle]:
    """Cria a frota inicial.

    Versão provisória: `n_vehicles` carros livres, distribuídos ao acaso
    pela zona do estádio e pelas zonas vizinhas.
    """
    p = params["placeholder"]
    zones = [p["stadium_zone"], *p["nearby_zones"]]
    return [
        Vehicle(id=i, zone=int(rng.choice(zones)))
        for i in range(p["n_vehicles"])
    ]