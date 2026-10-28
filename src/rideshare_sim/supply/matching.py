"""Regras de matching entre pedidos e veículos.

PLACEHOLDER: versão base do matching imediato.
Completado em feature/supply-model (matching em lote).
"""

from __future__ import annotations

from rideshare_sim.core.entities import Request, Vehicle
from rideshare_sim.core.interfaces import TravelTime


def match_immediate(
    pending: list[Request],
    free_vehicles: list[Vehicle],
    now: float,
    travel_time: TravelTime,
) -> list[tuple[Request, Vehicle]]:
    """Matching imediato: o pedido mais antigo fica com o carro livre mais próximo."""
    available = list(free_vehicles)
    pairs: list[tuple[Request, Vehicle]] = []

    for request in sorted(pending, key=lambda r: r.t_request):
        if not available:
            break
        nearest = min(available, key=lambda v: travel_time(v.zone, request.origin, now))
        pairs.append((request, nearest))
        available.remove(nearest)

    return pairs