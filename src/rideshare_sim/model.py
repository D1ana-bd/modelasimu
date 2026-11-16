"""Modelo Mesa: junta o mundo, a procura, a oferta e a política.

Ordem de cada passo (1 passo = `tick_minutes`):
    1. chegam pedidos novos ao estádio
    2. passageiros à espera verificam a paciência (desistem ou não)
    3. a plataforma faz o matching
    4. os carros andam uma célula
    5. recolhem-se os dados para os gráficos
"""

from __future__ import annotations

import copy
from pathlib import Path

import mesa
import yaml

from rideshare_sim.core.entities import RequestStatus, VehicleStatus
from rideshare_sim.core.metrics import MODEL_REPORTERS
from rideshare_sim.demand.arrivals import new_requests
from rideshare_sim.demand.passenger import Passenger
from rideshare_sim.supply.fleet import create_fleet
from rideshare_sim.supply.matching import match_immediate
from rideshare_sim.world.grid_world import GridWorld

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "base.yaml"


def load_params(path: Path | str = DEFAULT_CONFIG) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


class RideshareModel(mesa.Model):
    def __init__(
        self,
        params: dict | None = None,
        seed: int | None = None,
        # atalhos para os sliders da visualização (None = usa o valor do config)
        n_vehicles: int | None = None,
        request_rate_per_min: float | None = None,
        patience_mean_min: float | None = None,
    ) -> None:
        params = copy.deepcopy(params or load_params())
        if n_vehicles is not None:
            params["supply"]["n_vehicles"] = int(n_vehicles)
        if request_rate_per_min is not None:
            params["demand"]["request_rate_per_min"] = request_rate_per_min
        if patience_mean_min is not None:
            params["demand"]["patience_mean_min"] = patience_mean_min

        super().__init__(rng=params["seed"] if seed is None else seed)
        self.params = params
        self.tick_minutes = params["tick_minutes"]

        # mundo
        self.world = GridWorld(params)
        self.grid = mesa.space.MultiGrid(self.world.width, self.world.height, torus=False)

        # agentes
        self.vehicles = create_fleet(self)
        self.passengers: list[Passenger] = []   # todos, incluindo os que já saíram

        # política
        policy = params["policy"]
        self.match = match_immediate            # match_batch entra em feature/batch-matching
        self.batch_window_ticks = policy["batch_window_ticks"]

        self.datacollector = mesa.DataCollector(model_reporters=MODEL_REPORTERS)
        self.datacollector.collect(self)

    # ------------------------------------------------------------- tempo

    @property
    def time_min(self) -> float:
        """Minutos desde o fim do jogo."""
        return self.steps * self.tick_minutes

    # -------------------------------------------------------------- passo

    def step(self) -> None:
        self._spawn_passengers()

        for p in self.waiting_passengers():
            p.step()

        if self.steps % self.batch_window_ticks == 0:
            self._dispatch()

        for v in self.vehicles:
            v.step()

        self.datacollector.collect(self)

        if self._finished():
            self.running = False

    # ---------------------------------------------------------- auxiliares

    def waiting_passengers(self) -> list[Passenger]:
        return [p for p in self.passengers if p.status == RequestStatus.WAITING]

    def _spawn_passengers(self) -> None:
        d = self.params["demand"]
        for _ in range(new_requests(self.time_min, self.params, self.rng)):
            patience = min(self.rng.exponential(d["patience_mean_min"]), d["patience_max_min"])
            p = Passenger(self, self.world.random_destination(self.rng), patience)
            self.grid.place_agent(p, self.world.stadium)
            self.passengers.append(p)

    def _dispatch(self) -> None:
        waiting = self.waiting_passengers()
        free = [v for v in self.vehicles if v.is_free]
        if not waiting or not free:
            return
        for p, v in self.match(waiting, free, self.world):
            p.status = RequestStatus.MATCHED
            p.t_match = self.time_min
            p.vehicle = v
            v.assign(p)

    def _finished(self) -> bool:
        if self.time_min >= self.params["horizon_min"]:
            return True
        arrivals_over = self.time_min >= self.params["demand"]["request_duration_min"]
        in_progress = any(p.status in (RequestStatus.WAITING, RequestStatus.MATCHED,
                                       RequestStatus.RIDING) for p in self.passengers)
        return arrivals_over and not in_progress


def run_replication(params: dict | None = None, seed: int | None = None) -> RideshareModel:
    """Corre uma replicação até ao fim e devolve o modelo (para calcular os KPIs)."""
    model = RideshareModel(params=params, seed=seed)
    while model.running:
        model.step()
    return model
