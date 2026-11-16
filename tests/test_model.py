"""Testes de verificação do modelo Mesa.

Correr com:  pytest
"""

from __future__ import annotations

import pytest

from rideshare_sim.core.entities import RequestStatus, VehicleStatus
from rideshare_sim.core.metrics import compute_kpis
from rideshare_sim.demand.passenger import Passenger
from rideshare_sim.model import RideshareModel, load_params, run_replication
from rideshare_sim.supply.vehicle import Vehicle


@pytest.fixture
def params() -> dict:
    return load_params()


def test_request_balance(params):
    """Nenhum pedido se perde: servidos + abandonados + em curso = total."""
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_served"] + k["n_abandoned"] + k["n_unresolved"] == k["n_requests"]


def test_same_seed_same_result(params):
    """Reprodutibilidade: a mesma semente dá exatamente os mesmos KPIs."""
    a = compute_kpis(run_replication(params, seed=7))
    b = compute_kpis(run_replication(params, seed=7))
    assert a == b


def test_single_trip_by_hand(params):
    """1 carro a 3 células do estádio, destino a 4 células: recolha aos 3 passos, chegada aos 7."""
    params["supply"]["n_vehicles"] = 0
    params["demand"]["request_rate_per_min"] = 0
    model = RideshareModel(params=params, seed=0)
    sx, sy = model.world.stadium

    v = Vehicle(model)
    model.grid.place_agent(v, (sx + 3, sy))
    model.vehicles.append(v)

    p = Passenger(model, destination=(sx, sy + 4), patience_min=30)
    model.grid.place_agent(p, (sx, sy))
    model.passengers.append(p)

    tick = model.tick_minutes
    for _ in range(10):
        model.step()

    assert p.status == RequestStatus.SERVED
    assert p.t_pickup == pytest.approx(3 * tick)
    assert p.t_dropoff == pytest.approx(7 * tick)
    assert v.pos == (sx, sy + 4)                       # o carro fica no destino
    assert v.status == VehicleStatus.IDLE
    assert v.km_empty == pytest.approx(3 * model.world.cell_km)
    assert v.km_loaded == pytest.approx(4 * model.world.cell_km)


def test_no_vehicles_nobody_served(params):
    """Caso extremo: sem carros, ninguém é servido e todos acabam por desistir."""
    params["supply"]["n_vehicles"] = 0
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_served"] == 0
    assert k["n_abandoned"] == k["n_requests"]


def test_huge_fleet_nobody_abandons(params):
    """Caso extremo: com carros de sobra, ninguém desiste."""
    params["supply"]["n_vehicles"] = 3000
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_abandoned"] == 0


def test_more_vehicles_less_waiting(params):
    """Monotonia: mais carros não pode aumentar a espera média."""
    params["supply"]["n_vehicles"] = 100
    few = compute_kpis(run_replication(params, seed=3))
    params["supply"]["n_vehicles"] = 400
    many = compute_kpis(run_replication(params, seed=3))
    assert many["wait_mean_min"] <= few["wait_mean_min"]
    assert many["pct_abandoned"] <= few["pct_abandoned"]