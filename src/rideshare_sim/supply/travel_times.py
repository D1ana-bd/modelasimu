"""Tempos de viagem entre zonas.

PLACEHOLDER: substituído em feature/supply-data
(matriz por par de zonas e hora, estimada a partir de trip_time da TLC).
"""

from __future__ import annotations

_params: dict = {}


def configure(params: dict) -> None:
    """Guarda os parâmetros usados pelas funções deste módulo."""
    _params.update(params["placeholder"])


def travel_time(zone_a: int, zone_b: int, t: float) -> float:
    """Tempo de viagem (min) de zone_a para zone_b, à hora t.

    Versão provisória: constante, menor dentro da mesma zona.
    """
    if zone_a == zone_b:
        return _params["travel_time_same_zone_min"]
    return _params["travel_time_min"]


def distance_km(zone_a: int, zone_b: int, t: float) -> float:
    """Distância (km) aproximada a partir do tempo e de uma velocidade média."""
    return travel_time(zone_a, zone_b, t) * _params["speed_kmh"] / 60