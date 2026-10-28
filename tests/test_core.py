"""Testes de fumo do núcleo do simulador (verificação).

Confirmam que o motor faz o que esperamos em casos que conseguimos
calcular à mão, antes de entrarem os dados reais.
Correr com:  pytest
"""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest
import yaml

from rideshare_sim.core.entities import Request, RequestStatus, Vehicle
from rideshare_sim.core.metrics import compute_kpis
from rideshare_sim.core.simulation import Simulation, run_replication
from rideshare_sim.supply.matching import match_immediate

CONFIG = Path(__file__).resolve().parents[1] / "config" / "base.yaml"


@pytest.fixture
def params() -> dict:
    """Parâmetros base, copiados para cada teste poder alterá-los à vontade."""
    with open(CONFIG) as f:
        return copy.deepcopy(yaml.safe_load(f))


def test_request_balance(params):
    """Nenhum pedido se perde: servidos + abandonados + em curso = total."""
    kpis = compute_kpis(run_replication(params, seed=1), params)
    assert kpis["n_served"] + kpis["n_abandoned"] + kpis["n_unresolved"] == kpis["n_requests"]


def test_same_seed_same_result(params):
    """Reprodutibilidade: a mesma semente dá exatamente os mesmos KPIs."""
    a = compute_kpis(run_replication(params, seed=7), params)
    b = compute_kpis(run_replication(params, seed=7), params)
    assert a == b


def test_single_request_by_hand(params):
    """1 pedido, 1 carro, viagens de 5 min: recolha aos t+5 e chegada aos t+10."""
    sim = Simulation(
        params=params,
        rng=np.random.default_rng(0),
        generate_requests=lambda p, rng: [
            Request(id=0, t_request=1.0, origin=1, destination=10, patience=30)
        ],
        create_fleet=lambda p, rng: [Vehicle(id=0, zone=2)],
        travel_time=lambda a, b, t: 5.0,
        distance_km=lambda a, b, t: 2.0,
        match=match_immediate,
    )
    result = sim.run()
    r, v = result.requests[0], result.vehicles[0]

    assert r.status == RequestStatus.SERVED
    assert r.t_match == pytest.approx(1.0)
    assert r.t_pickup == pytest.approx(6.0)
    assert r.t_dropoff == pytest.approx(11.0)
    assert v.zone == 10                      # o carro fica na zona de destino
    assert v.km_empty == pytest.approx(2.0)
    assert v.km_loaded == pytest.approx(2.0)


def test_no_vehicles_nobody_served(params):
    """Caso extremo: sem carros, ninguém é servido.

    Quase todos desistem; os poucos com paciência muito longa podem ainda
    estar à espera quando a simulação para no horizonte (n_unresolved).
    """
    params["placeholder"]["n_vehicles"] = 0
    kpis = compute_kpis(run_replication(params, seed=1), params)
    assert kpis["n_served"] == 0
    assert kpis["n_abandoned"] + kpis["n_unresolved"] == kpis["n_requests"]


def test_huge_fleet_nobody_abandons(params):
    """Caso extremo: com carros de sobra, ninguém desiste e a espera é só a recolha."""
    params["placeholder"]["n_vehicles"] = 5000
    kpis = compute_kpis(run_replication(params, seed=1), params)
    assert kpis["n_abandoned"] == 0
    assert kpis["wait_mean_min"] <= params["placeholder"]["travel_time_min"]


def test_batch_matches_only_at_window_ends(params):
    """Matching em lote: os matches só acontecem no fim de cada janela de 30 s."""
    params["policy"]["matching"] = "batch"
    result = run_replication(params, seed=1)
    window = params["policy"]["batch_window_s"] / 60
    match_times = [r.t_match for r in result.requests if r.t_match is not None]

    assert match_times
    for t in match_times:
        assert (t / window) == pytest.approx(round(t / window))