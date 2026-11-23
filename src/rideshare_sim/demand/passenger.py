"""Agente Passageiro."""

from __future__ import annotations

import mesa

from rideshare_sim.core.entities import PassengerType, RequestStatus


class Passenger(mesa.Agent):
    """Pede um carro; desiste se esperar pelo match mais do que a paciência."""

    def __init__(self, model, origin, destination, ptype: PassengerType, patience_min: float) -> None:
        super().__init__(model)
        self.origin = origin
        self.destination = destination
        self.ptype = ptype
        self.patience_min = patience_min
        self.status = RequestStatus.WAITING
        self.vehicle = None

        self.t_request: float = model.time_min
        self.t_match: float | None = None
        self.t_pickup: float | None = None
        self.t_dropoff: float | None = None
        self.t_abandon: float | None = None

    # ------------------------------------------------------------ KPIs

    @property
    def wait_for_pickup(self) -> float | None:
        if self.t_pickup is None:
            return None
        return self.t_pickup - self.t_request

    # ------------------------------------------------------- comportamento

    def step(self) -> None:
        """Se ainda não tem carro e a paciência acabou, desiste."""
        if self.status != RequestStatus.WAITING:
            return
        if self.model.time_min - self.t_request >= self.patience_min:
            self.status = RequestStatus.ABANDONED
            self.t_abandon = self.model.time_min
            self.model.grid.remove_agent(self)
            self.remove()  # sai do modelo (continua guardado em model.passengers)