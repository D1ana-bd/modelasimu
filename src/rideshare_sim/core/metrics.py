"""Cálculo dos KPIs de uma replicação.

Transforma o estado final das entidades nos indicadores do Tema 14:
espera, pedidos abandonados, desvios, utilização, km vazios, emissões
e tempo até a fila de pedidos esvaziar.
"""

from __future__ import annotations

import numpy as np

from rideshare_sim.core.entities import RequestStatus
from rideshare_sim.core.simulation import SimulationResult


def compute_kpis(result: SimulationResult, params: dict) -> dict:
    """Calcula os KPIs de uma replicação. Devolve um dicionário (uma linha de resultados)."""
    requests = result.requests
    vehicles = result.vehicles
    n = len(requests)

    served = [r for r in requests if r.status == RequestStatus.SERVED]
    abandoned = [r for r in requests if r.status == RequestStatus.ABANDONED]
    unresolved = n - len(served) - len(abandoned)  # ainda em curso no fim do horizonte

    # espera: do pedido até à recolha, só para quem foi recolhido
    waits = np.array([r.wait_for_pickup for r in requests if r.t_pickup is not None])
    match_waits = np.array([r.wait_for_match for r in requests if r.t_match is not None])

    # desvios: só para quem viajou em pooling
    detours = np.array([r.detour_min for r in requests if r.shared])

    # utilização: fração do tempo em que os carros não estiveram livres
    fleet_time = len(vehicles) * result.end_time
    utilization = sum(v.busy_time for v in vehicles) / fleet_time if fleet_time > 0 else 0.0

    # quilómetros e emissões
    km_empty = sum(v.km_empty for v in vehicles)
    km_loaded = sum(v.km_loaded for v in vehicles)
    km_total = km_empty + km_loaded
    emission_factor = params["kpi"]["emission_kg_co2_per_km"]

    # tempo até a fila esvaziar: último momento em que um pedido saiu da fila
    # (por match ou por desistência)
    left_queue = [r.t_match for r in requests if r.t_match is not None]
    left_queue += [r.t_request + r.patience for r in abandoned]
    clearance_time = max(left_queue) if left_queue else 0.0

    return {
        "n_requests": n,
        "n_served": len(served),
        "n_abandoned": len(abandoned),
        "n_unresolved": unresolved,
        "pct_abandoned": 100 * len(abandoned) / n if n else 0.0,
        "wait_mean_min": float(waits.mean()) if waits.size else np.nan,
        "wait_p90_min": float(np.percentile(waits, 90)) if waits.size else np.nan,
        "match_wait_mean_min": float(match_waits.mean()) if match_waits.size else np.nan,
        "detour_mean_min": float(detours.mean()) if detours.size else 0.0,
        "pct_shared": 100 * len(detours) / len(served) if served else 0.0,
        "utilization": utilization,
        "km_empty": km_empty,
        "km_loaded": km_loaded,
        "pct_km_empty": 100 * km_empty / km_total if km_total else 0.0,
        "emissions_kg_co2": km_total * emission_factor,
        "clearance_time_min": clearance_time,
        "end_time_min": result.end_time,
    }