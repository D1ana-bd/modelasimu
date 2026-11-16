"""Agente Carro."""

from __future__ import annotations

import mesa

from rideshare_sim.core.entities import RequestStatus, VehicleStatus


class Vehicle(mesa.Agent):
    """Anda uma célula por passo: vai buscar o passageiro e leva-o ao destino."""

    def __init__(self, model) -> None:
        super().__init__(model)
        self.status = VehicleStatus.IDLE
        self.passenger = None
        self.target = None
        self.km_empty = 0.0
        self.km_loaded = 0.0
        self.busy_ticks = 0

    @property
    def is_free(self) -> bool:
        return self.status == VehicleStatus.IDLE

    # ------------------------------------------------------- comportamento

    def assign(self, passenger) -> None:
        """A plataforma atribui-lhe um passageiro."""
        self.status = VehicleStatus.TO_PICKUP
        self.passenger = passenger
        self.target = passenger.pos

    def step(self) -> None:
        if self.status == VehicleStatus.IDLE:
            return
        self.busy_ticks += 1

        world = self.model.world
        if self.pos != self.target:
            new_pos = world.step_towards(self.pos, self.target)
            km = world.distance_km(self.pos, new_pos)
            if self.status == VehicleStatus.BUSY:
                self.km_loaded += km
            else:
                self.km_empty += km
            self.model.grid.move_agent(self, new_pos)

        if self.pos == self.target:
            self._arrive()

    def _arrive(self) -> None:
        p = self.passenger
        now = self.model.time_min

        if self.status == VehicleStatus.TO_PICKUP:
            p.status = RequestStatus.RIDING
            p.t_pickup = now
            self.model.grid.remove_agent(p)  # o passageiro entra no carro
            self.status = VehicleStatus.BUSY
            self.target = p.destination

        elif self.status == VehicleStatus.BUSY:
            p.status = RequestStatus.SERVED
            p.t_dropoff = now
            p.remove()
            self.status = VehicleStatus.IDLE
            self.passenger = None
            self.target = None