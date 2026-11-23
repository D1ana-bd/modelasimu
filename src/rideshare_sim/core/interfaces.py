"""Contratos entre as partes do modelo.

Cada lado pode mudar a implementação à vontade, desde que respeite
estas assinaturas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import numpy as np

if TYPE_CHECKING:
    from rideshare_sim.demand.passenger import Passenger
    from rideshare_sim.supply.vehicle import Vehicle

Cell = tuple[int, int]


class World(Protocol):
    """O "mundo": onde estão as coisas, quanto tempo se demora e onde é a zona do evento."""

    stadium: Cell

    def distance(self, a: Cell, b: Cell) -> int: ...
    def travel_time(self, a: Cell, b: Cell) -> float: ...
    def distance_km(self, a: Cell, b: Cell) -> float: ...
    def in_event_zone(self, cell: Cell) -> bool: ...
    def step_towards(self, a: Cell, b: Cell) -> Cell: ...
    def random_cell(self, rng: np.random.Generator) -> Cell: ...
    def random_destination(self, rng: np.random.Generator, origin: Cell) -> Cell: ...


class NewRequests(Protocol):
    """Procura → modelo: quantos pedidos novos aparecem neste passo (cidade ou evento).

    `time_min` é o tempo em minutos, com t = 0 no fim do jogo.
    """

    def __call__(self, time_min: float, params: dict, rng: np.random.Generator) -> int: ...


class Match(Protocol):
    """Oferta → modelo: que carro vai buscar que passageiro.

    Passageiros sem carro ficam para a próxima decisão.
    """

    def __call__(
        self, waiting: list[Passenger], free: list[Vehicle], world: World
    ) -> list[tuple[Passenger, Vehicle]]: ...


class Relocate(Protocol):
    """Oferta → modelo: que carros livres vão para a zona do evento (e para que célula).

    Chamado em cada passo; devolve pares (carro, célula de destino).
    Implementado em feature/relocation.
    """

    def __call__(
        self, free: list[Vehicle], time_min: float, params: dict, world: World
    ) -> list[tuple[Vehicle, Cell]]: ...
