"""Regras de matching.

match_immediate: baseline.
match_batch: entra em feature/batch-matching.
"""

from __future__ import annotations


def match_immediate(waiting, free, world):
    """O passageiro que espera há mais tempo fica com o carro livre mais próximo."""
    available = list(free)
    pairs = []
    for p in sorted(waiting, key=lambda p: p.t_request):
        if not available:
            break
        nearest = min(available, key=lambda v: world.travel_time(v.pos, p.pos))
        pairs.append((p, nearest))
        available.remove(nearest)
    return pairs