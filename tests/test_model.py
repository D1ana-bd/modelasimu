"""Testes de verificação do modelo Mesa.

Correr com:  pytest -v
"""

from __future__ import annotations

import pytest

from rideshare_sim.core.entities import PassengerType, RequestStatus, VehicleStatus
from rideshare_sim.core.metrics import compute_kpis
from rideshare_sim.demand.arrivals import event_rate_per_min
from rideshare_sim.demand.passenger import Passenger
from rideshare_sim.model import RideshareModel, load_params, run_replication
from rideshare_sim.supply.vehicle import Vehicle
from rideshare_sim.world.grid_world import GridWorld


@pytest.fixture
def params() -> dict:
    return load_params()


# ------------------------------------------------------------ testes gerais

def test_request_balance(params):
    """Nenhum pedido se perde: servidos + abandonados + em curso = total."""
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_served"] + k["n_abandoned"] + k["n_unresolved"] == k["n_requests"]


def test_same_seed_same_result(params):
    """Reprodutibilidade: a mesma semente dá exatamente os mesmos KPIs."""
    a = compute_kpis(run_replication(params, seed=7))
    b = compute_kpis(run_replication(params, seed=7))
    assert a == b


def test_runs_until_end_time(params):
    """A simulação acaba exatamente em `end_min` (120 min depois do fim do jogo)."""
    model = run_replication(params, seed=1)
    assert model.time_min == pytest.approx(params["time"]["end_min"])


def test_single_trip_by_hand(params):
    """1 carro a 3 células do passageiro, destino a 4 células: recolha aos 3 passos, chegada aos 7."""
    params["supply"]["n_vehicles"] = 0
    params["demand"]["city_rate_per_min"] = 0
    params["demand"]["event"]["enabled"] = False
    model = RideshareModel(params=params, seed=0)
    sx, sy = model.world.stadium

    v = Vehicle(model)
    model.grid.place_agent(v, (sx + 3, sy))
    model.vehicles.append(v)

    p = Passenger(model, (sx, sy), (sx, sy + 4), PassengerType.CITY, patience_min=30)
    model.grid.place_agent(p, (sx, sy))
    model.passengers.append(p)

    start, tick = model.start_min, model.tick_minutes
    for _ in range(10):
        model.step()

    assert p.status == RequestStatus.SERVED
    assert p.t_pickup == pytest.approx(start + 3 * tick)
    assert p.t_dropoff == pytest.approx(start + 7 * tick)
    assert v.pos == (sx, sy + 4)                       # o carro fica no destino
    assert v.status == VehicleStatus.IDLE
    assert v.km_empty == pytest.approx(3 * model.world.cell_km)
    assert v.km_loaded == pytest.approx(4 * model.world.cell_km)


def test_no_vehicles_nobody_served(params):
    """Caso extremo: sem carros, ninguém é servido (desistem ou ainda esperam no fim)."""
    params["supply"]["n_vehicles"] = 0
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_served"] == 0
    assert k["n_abandoned"] + k["n_unresolved"] == k["n_requests"]


def test_huge_fleet_nobody_abandons(params):
    """Caso extremo: com carros de sobra, ninguém desiste."""
    params["supply"]["n_vehicles"] = 3000
    k = compute_kpis(run_replication(params, seed=1))
    assert k["n_abandoned"] == 0


def test_more_vehicles_less_waiting(params):
    """Monotonia: mais carros não pode aumentar a espera nem as desistências."""
    params["supply"]["n_vehicles"] = 100
    few = compute_kpis(run_replication(params, seed=3))
    params["supply"]["n_vehicles"] = 300
    many = compute_kpis(run_replication(params, seed=3))
    assert many["wait_mean_min"] <= few["wait_mean_min"]
    assert many["pct_abandoned"] <= few["pct_abandoned"]


# ------------------------------------------------- cidade e zona do evento

def test_event_zone_by_hand(params):
    """Zona do evento: o estádio e células a 3 de distância estão dentro; a 4 estão fora."""
    world = GridWorld(params)
    sx, sy = world.stadium
    assert world.in_event_zone((sx, sy))
    assert world.in_event_zone((sx + 2, sy + 1))       # distância 3
    assert not world.in_event_zone((sx + 2, sy + 2))   # distância 4


def test_event_rate_shape(params):
    """Pico do evento: 0 antes do fim do jogo, máximo aos 10 min, 0 aos 60 min."""
    peak = params["demand"]["event"]["peak_rate_per_min"]
    assert event_rate_per_min(-1, params) == 0
    assert event_rate_per_min(10, params) == pytest.approx(peak)
    assert event_rate_per_min(60, params) == 0


def test_event_passengers_only_after_game_at_stadium(params):
    """Pedidos do evento só aparecem depois do fim do jogo e sempre no estádio."""
    model = run_replication(params, seed=2)
    event = [p for p in model.passengers if p.ptype == PassengerType.EVENT]
    assert event
    assert all(p.t_request >= 0 for p in event)
    assert all(p.origin == model.world.stadium for p in event)


def test_normal_day_has_no_event_passengers(params):
    """E0 (dia normal): sem evento, só há pedidos da cidade."""
    params["demand"]["event"]["enabled"] = False
    model = run_replication(params, seed=2)
    assert model.passengers
    assert all(p.ptype == PassengerType.CITY for p in model.passengers)


def test_city_demand_spread_across_city(params):
    """A procura normal aparece em toda a cidade, a maior parte fora da zona do evento."""
    model = run_replication(params, seed=2)
    city = [p for p in model.passengers if p.ptype == PassengerType.CITY]
    outside = sum(not model.world.in_event_zone(p.origin) for p in city)
    assert len({p.origin for p in city}) > 100
    assert outside / len(city) > 0.9
