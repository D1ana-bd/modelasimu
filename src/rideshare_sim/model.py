"""Modelo Mesa: junta o mundo, a procura, a oferta e a política.

O tempo é medido em minutos com t = 0 no fim do jogo: a simulação começa
em `start_min` (antes do jogo acabar) e termina em `end_min`.

Ordem de cada passo (1 passo = `tick_minutes`):
    1. CHEGADAS      → pedidos normais (cidade) + pico do evento (estádio)
    2. PACIÊNCIA     → passageiros sem carro que esperaram demais desistem
    3. MATCHING      → a plataforma atribui carros livres a passageiros à espera
    4. REPOSICIONAR  → se a política o permitir, carros livres vão para o evento
    5. MOVIMENTO     → os carros com destino andam uma célula
    6. REGISTO       → dados para os gráficos
"""

from __future__ import annotations

import copy
from pathlib import Path

import mesa
import yaml

from rideshare_sim.core.entities import PassengerType, RequestStatus
from rideshare_sim.core.metrics import MODEL_REPORTERS
from rideshare_sim.demand.arrivals import city_requests, event_requests
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
        city_rate_per_min: float | None = None,
        peak_rate_per_min: float | None = None,
        patience_mean_min: float | None = None,
    ) -> None:
        params = copy.deepcopy(params or load_params())
        if n_vehicles is not None:
            params["supply"]["n_vehicles"] = int(n_vehicles)
        if city_rate_per_min is not None:
            params["demand"]["city_rate_per_min"] = city_rate_per_min
        if peak_rate_per_min is not None:
            params["demand"]["event"]["peak_rate_per_min"] = peak_rate_per_min
        if patience_mean_min is not None:
            params["demand"]["patience_mean_min"] = patience_mean_min

        super().__init__(rng=params["seed"] if seed is None else seed)
        self.params = params
        self.tick_minutes = params["time"]["tick_minutes"]
        self.start_min = params["time"]["start_min"]
        self.end_min = params["time"]["end_min"]

        # mundo
        self.world = GridWorld(params)
        self.grid = mesa.space.MultiGrid(self.world.width, self.world.height, torus=False)

        # agentes
        self.vehicles = create_fleet(self)
        self.passengers: list[Passenger] = []   # todos, incluindo os que já saíram

        # política
        policy = params["policy"]
        self.match = match_immediate            # match_batch entra em feature/batch-matching
        self.batch_window_ticks = policy["batch_window_ticks"] if policy["matching"] == "batch" else 1
        self.relocation_enabled = policy["relocation"]["enabled"]

        self.datacollector = mesa.DataCollector(model_reporters=MODEL_REPORTERS)
        self.datacollector.collect(self)

    # ------------------------------------------------------------- tempo

    @property
    def time_min(self) -> float:
        """Minutos em relação ao fim do jogo (negativo = antes do fim)."""
        return self.start_min + self.steps * self.tick_minutes

    # -------------------------------------------------------------- passo

    def step(self) -> None:
        self._spawn_passengers()                       # 1. chegadas

        for p in self.waiting_passengers():            # 2. paciência
            p.step()

        if self.steps % self.batch_window_ticks == 0:  # 3. matching
            self._dispatch()

        self._relocate()                               # 4. reposicionamento

        for v in self.vehicles:                        # 5. movimento
            v.step()

        self.datacollector.collect(self)               # 6. registo

        if self.time_min >= self.end_min:
            self.running = False

    # ---------------------------------------------------------- auxiliares

    def waiting_passengers(self) -> list[Passenger]:
        return [p for p in self.passengers if p.status == RequestStatus.WAITING]

    def _new_passenger(self, origin, ptype: PassengerType) -> None:
        d = self.params["demand"]
        patience = min(self.rng.exponential(d["patience_mean_min"]), d["patience_max_min"])
        destination = self.world.random_destination(self.rng, origin)
        p = Passenger(self, origin, destination, ptype, patience)
        self.grid.place_agent(p, origin)
        self.passengers.append(p)

    def _spawn_passengers(self) -> None:
        # procura normal: em qualquer ponto da cidade
        for _ in range(city_requests(self.time_min, self.params, self.rng)):
            self._new_passenger(self.world.random_cell(self.rng), PassengerType.CITY)
        # pico do evento: no estádio
        for _ in range(event_requests(self.time_min, self.params, self.rng)):
            self._new_passenger(self.world.stadium, PassengerType.EVENT)

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

    def _relocate(self) -> None:
        """Passo 4. Implementado em feature/relocation (supply/relocation.py)."""
        if self.relocation_enabled:
            raise NotImplementedError("O reposicionamento entra em feature/relocation.")


def run_replication(params: dict | None = None, seed: int | None = None) -> RideshareModel:
    """Corre uma replicação até ao fim e devolve o modelo (para calcular os KPIs)."""
    model = RideshareModel(params=params, seed=seed)
    while model.running:
        model.step()
    return model