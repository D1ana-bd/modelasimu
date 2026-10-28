"""Motor do simulador (eventos discretos, SimPy).

Junta a procura, a oferta e as regras da plataforma e põe o tempo a andar.
O tempo está em minutos desde o fim do jogo (t = 0).

Processos:
    - chegada de pedidos  → cada pedido entra na fila de pendentes
    - paciência           → se não houver match a tempo, o pedido é abandonado
    - viagem              → o carro vai buscar o passageiro, leva-o e fica livre
    - despacho            → a plataforma decide os matches
                            (imediato: a cada evento; lote: a cada janela)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import simpy

from rideshare_sim.core.entities import (
    Request,
    RequestStatus,
    Vehicle,
    VehicleStatus,
)


@dataclass
class SimulationResult:
    """O que sai de uma replicação: as entidades no estado final."""

    requests: list[Request]
    vehicles: list[Vehicle]
    end_time: float


class Simulation:
    """Uma replicação da simulação."""

    def __init__(
        self,
        params: dict,
        rng: np.random.Generator,
        generate_requests,
        create_fleet,
        travel_time,
        distance_km,
        match,
    ) -> None:
        self.params = params
        self.env = simpy.Environment()

        self.travel_time = travel_time
        self.distance_km = distance_km
        self.match = match

        self.requests: list[Request] = generate_requests(params, rng)
        self.vehicles: list[Vehicle] = create_fleet(params, rng)
        self.pending: list[Request] = []

        policy = params["policy"]
        self.batch_mode = policy["matching"] == "batch"
        self.batch_window_min = policy["batch_window_s"] / 60

        self.n_resolved = 0                 # servidos + abandonados
        self.all_resolved = self.env.event()

    # ------------------------------------------------------------------ run

    def run(self) -> SimulationResult:
        self.env.process(self._request_source())
        if self.batch_mode:
            self.env.process(self._batch_ticker())

        horizon = self.env.timeout(self.params["horizon_min"])
        self.env.run(until=self.env.any_of([self.all_resolved, horizon]))

        return SimulationResult(self.requests, self.vehicles, self.env.now)

    # ------------------------------------------------------------ processos

    def _request_source(self):
        """Faz chegar cada pedido à sua hora."""
        for request in self.requests:
            yield self.env.timeout(request.t_request - self.env.now)
            self.pending.append(request)
            self.env.process(self._patience(request))
            if not self.batch_mode:
                self._dispatch()

    def _patience(self, request: Request):
        """Se o pedido ainda não tiver carro quando a paciência acabar, desiste."""
        yield self.env.timeout(request.patience)
        if request.status == RequestStatus.WAITING:
            request.status = RequestStatus.ABANDONED
            self.pending.remove(request)
            self._resolve()

    def _batch_ticker(self):
        """Matching em lote: a plataforma decide a cada janela de tempo."""
        while not self.all_resolved.triggered:
            yield self.env.timeout(self.batch_window_min)
            self._dispatch()

    def _trip(self, request: Request, vehicle: Vehicle):
        """Recolha + viagem até ao destino; no fim o carro fica livre."""
        start = self.env.now

        # carro vai buscar o passageiro (km vazios)
        t_to_pickup = self.travel_time(vehicle.zone, request.origin, self.env.now)
        vehicle.km_empty += self.distance_km(vehicle.zone, request.origin, self.env.now)
        yield self.env.timeout(t_to_pickup)

        request.t_pickup = self.env.now
        request.status = RequestStatus.RIDING
        vehicle.zone = request.origin
        vehicle.status = VehicleStatus.BUSY
        vehicle.passengers.append(request.id)

        # viagem até ao destino (km com passageiro)
        t_ride = self.travel_time(request.origin, request.destination, self.env.now)
        vehicle.km_loaded += self.distance_km(request.origin, request.destination, self.env.now)
        yield self.env.timeout(t_ride)

        request.t_dropoff = self.env.now
        request.status = RequestStatus.SERVED
        vehicle.zone = request.destination
        vehicle.passengers.remove(request.id)
        vehicle.status = VehicleStatus.IDLE
        vehicle.busy_time += self.env.now - start
        self._resolve()

        if not self.batch_mode:
            self._dispatch()

    # -------------------------------------------------------------- decisão

    def _dispatch(self) -> None:
        """Pede à regra de matching os pares (pedido, carro) e lança as viagens."""
        free = [v for v in self.vehicles if v.is_free]
        if not self.pending or not free:
            return

        for request, vehicle in self.match(self.pending, free, self.env.now, self.travel_time):
            request.status = RequestStatus.MATCHED
            request.t_match = self.env.now
            request.vehicle_id = vehicle.id
            vehicle.status = VehicleStatus.TO_PICKUP
            self.pending.remove(request)
            self.env.process(self._trip(request, vehicle))

    def _resolve(self) -> None:
        """Conta um pedido terminado; quando são todos, a simulação acaba."""
        self.n_resolved += 1
        if self.n_resolved == len(self.requests) and not self.all_resolved.triggered:
            self.all_resolved.succeed()


def run_replication(params: dict, seed: int) -> SimulationResult:
    """Corre uma replicação com as peças atuais de procura e oferta."""
    from rideshare_sim.demand.arrivals import generate_requests
    from rideshare_sim.supply import travel_times
    from rideshare_sim.supply.fleet import create_fleet
    from rideshare_sim.supply.matching import match_immediate

    travel_times.configure(params)
    rng = np.random.default_rng(seed)

    match = match_immediate  # match_batch entra em feature/supply-model

    sim = Simulation(
        params=params,
        rng=rng,
        generate_requests=generate_requests,
        create_fleet=create_fleet,
        travel_time=travel_times.travel_time,
        distance_km=travel_times.distance_km,
        match=match,
    )
    return sim.run()