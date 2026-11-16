"""KPIs: em tempo real (para os gráficos) e no fim de cada replicação."""

from __future__ import annotations

import numpy as np

from rideshare_sim.core.entities import RequestStatus, VehicleStatus


# ------------------------------------------------ em tempo real (DataCollector)

def _count(model, status) -> int:
    return sum(1 for p in model.passengers if p.status == status)


MODEL_REPORTERS = {
    "Waiting": lambda m: _count(m, RequestStatus.WAITING),
    "Served": lambda m: _count(m, RequestStatus.SERVED),
    "Abandoned": lambda m: _count(m, RequestStatus.ABANDONED),
    "Idle vehicles": lambda m: sum(v.status == VehicleStatus.IDLE for v in m.vehicles),
    "Busy vehicles": lambda m: sum(v.status != VehicleStatus.IDLE for v in m.vehicles),
}


# ------------------------------------------------------ no fim da replicação

def compute_kpis(model) -> dict:
    passengers = model.passengers
    vehicles = model.vehicles
    n = len(passengers)

    served = [p for p in passengers if p.status == RequestStatus.SERVED]
    abandoned = [p for p in passengers if p.status == RequestStatus.ABANDONED]
    waits = np.array([p.wait_for_pickup for p in passengers if p.t_pickup is not None])

    total_ticks = model.steps
    utilization = (sum(v.busy_ticks for v in vehicles) / (len(vehicles) * total_ticks)
                   if vehicles and total_ticks else 0.0)

    km_empty = sum(v.km_empty for v in vehicles)
    km_loaded = sum(v.km_loaded for v in vehicles)
    km_total = km_empty + km_loaded

    left_queue = [p.t_match for p in passengers if p.t_match is not None]
    left_queue += [p.t_abandon for p in abandoned]

    return {
        "n_requests": n,
        "n_served": len(served),
        "n_abandoned": len(abandoned),
        "n_unresolved": n - len(served) - len(abandoned),
        "pct_abandoned": 100 * len(abandoned) / n if n else 0.0,
        "wait_mean_min": float(waits.mean()) if waits.size else np.nan,
        "wait_p90_min": float(np.percentile(waits, 90)) if waits.size else np.nan,
        "utilization": utilization,
        "km_empty": km_empty,
        "km_loaded": km_loaded,
        "pct_km_empty": 100 * km_empty / km_total if km_total else 0.0,
        "emissions_kg_co2": km_total * model.params["kpi"]["emission_kg_co2_per_km"],
        "clearance_time_min": max(left_queue) if left_queue else 0.0,
        "end_time_min": model.time_min,
    }
