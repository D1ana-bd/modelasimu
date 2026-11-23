"""Quantos pedidos aparecem em cada passo.

Duas fontes de procura:
    - procura normal: em toda a cidade, a ritmo constante, o tempo tod*;
    - pico do evento: no estádio, a partir do fim do jogo (t = 0).

PLACEHOLDER: a forma do pico (triangular) e os ritmos são provisórios.
Refinados em feature/demand-city-event e calibrados com NYC (prioridade 4).
"""

from __future__ import annotations

import numpy as np


def event_rate_per_min(time_min: float, params: dict) -> float:
    """Ritmo do pico do evento (pedidos/min) no instante `time_min`.

    Forma triangular: 0 antes do fim do jogo, sobe até ao máximo em
    `ramp_up_min` e desce até 0 aos `duration_min`.
    """
    e = params["demand"]["event"]
    if not e["enabled"] or time_min < 0 or time_min >= e["duration_min"]:
        return 0.0
    peak, up, dur = e["peak_rate_per_min"], e["ramp_up_min"], e["duration_min"]
    if time_min < up:
        return peak * time_min / up
    return peak * (dur - time_min) / (dur - up)


def city_requests(time_min: float, params: dict, rng: np.random.Generator) -> int:
    """Pedidos normais da cidade neste passo (Poisson, ritmo constante)."""
    expected = params["demand"]["city_rate_per_min"] * params["time"]["tick_minutes"]
    return int(rng.poisson(expected))


def event_requests(time_min: float, params: dict, rng: np.random.Generator) -> int:
    """Pedidos do evento neste passo (Poisson, ritmo variável)."""
    expected = event_rate_per_min(time_min, params) * params["time"]["tick_minutes"]
    return int(rng.poisson(expected))