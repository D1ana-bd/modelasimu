"""Quantos pedidos aparecem em cada passo.

PLACEHOLDER: taxa constante durante `request_duration_min`.
Substituído em feature/demand-calibration pela curva real de NYC
(pico logo após o jogo e depois a descer).
"""

from __future__ import annotations

import numpy as np


def new_requests(time_min: float, params: dict, rng: np.random.Generator) -> int:
    d = params["demand"]
    if time_min >= d["request_duration_min"]:
        return 0
    expected = d["request_rate_per_min"] * params["tick_minutes"]
    return int(rng.poisson(expected))