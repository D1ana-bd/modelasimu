"""Contratos entre os módulos (o que cada lado entrega ao núcleo).

Cada lado pode mudar a implementação à vontade, desde que respeite
estas assinaturas. Assim procura e oferta evoluem em paralelo.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from rideshare_sim.core.entities import Request, Vehicle


class GenerateRequests(Protocol):
    """Procura → núcleo: lista de pedidos de uma replicação, ordenada por t_request."""

    def __call__(self, params: dict, rng: np.random.Generator) -> list[Request]: ...


class TravelTime(Protocol):
    """Oferta → núcleo: tempo de viagem (min) entre duas zonas, à hora t (min)."""

    def __call__(self, zone_a: int, zone_b: int, t: float) -> float: ...


class CreateFleet(Protocol):
    """Oferta → núcleo: veículos disponíveis no início da simulação."""

    def __call__(self, params: dict, rng: np.random.Generator) -> list[Vehicle]: ...


class Match(Protocol):
    """Oferta → núcleo: decide que carro vai buscar que pedido.

    Devolve pares (pedido, veículo). Pedidos sem carro ficam para a próxima decisão.
    """

    def __call__(
        self,
        pending: list[Request],
        free_vehicles: list[Vehicle],
        now: float,
        travel_time: TravelTime,
    ) -> list[tuple[Request, Vehicle]]: ...