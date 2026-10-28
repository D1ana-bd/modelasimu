"""Geração de pedidos após o fim do jogo.

PLACEHOLDER: substituído em feature/demand-data
(Poisson não homogéneo e destinos ajustados aos dados TLC).
"""

from __future__ import annotations

import numpy as np

from rideshare_sim.core.entities import Request


def generate_requests(params: dict, rng: np.random.Generator) -> list[Request]:
    """Gera os pedidos de uma replicação.

    Versão provisória: Poisson homogéneo (taxa constante) durante
    `request_duration_min`, origem no estádio, destino uniforme entre
    as zonas de destino e paciência exponencial.
    """
    p = params["placeholder"]
    rate = p["request_rate_per_min"]
    duration = p["request_duration_min"]

    requests: list[Request] = []
    t = 0.0
    while True:
        t += rng.exponential(1 / rate)  # tempo até ao próximo pedido
        if t > duration:
            break
        requests.append(
            Request(
                id=len(requests),
                t_request=t,
                origin=p["stadium_zone"],
                destination=int(rng.choice(p["destination_zones"])),
                patience=rng.exponential(p["patience_mean_min"]),
            )
        )
    return requests