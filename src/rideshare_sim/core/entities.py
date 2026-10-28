"""Entidades do modelo: pedidos (passageiros) e veículos.

Todas as horas estão em minutos desde o fim do jogo (t = 0).
As zonas são identificadas pelo LocationID das zonas TLC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RequestStatus(str, Enum):
    """Estados possíveis de um pedido (ciclo do passageiro)."""

    WAITING = "waiting"      # à espera de match
    MATCHED = "matched"      # já tem carro, à espera que chegue
    RIDING = "riding"        # em viagem
    SERVED = "served"        # chegou ao destino
    ABANDONED = "abandoned"  # desistiu (vai de metro)


class VehicleStatus(str, Enum):
    """Estados possíveis de um veículo (ciclo do veículo)."""

    IDLE = "idle"              # livre
    TO_PICKUP = "to_pickup"    # a caminho da recolha
    BUSY = "busy"              # com passageiro(s)
    RELOCATING = "relocating"  # a reposicionar-se, vazio


@dataclass
class Request:
    """Um pedido de viagem feito por um passageiro."""

    id: int
    t_request: float          # hora do pedido (min)
    origin: int               # zona de origem (LocationID)
    destination: int          # zona de destino (LocationID)
    patience: float           # espera máxima por match (min)

    status: RequestStatus = RequestStatus.WAITING
    vehicle_id: int | None = None
    t_match: float | None = None
    t_pickup: float | None = None
    t_dropoff: float | None = None
    shared: bool = False      # viajou em pooling?
    detour_min: float = 0.0   # desvio sofrido por causa do pooling (min)

    @property
    def wait_for_match(self) -> float | None:
        """Tempo entre o pedido e o match (min)."""
        if self.t_match is None:
            return None
        return self.t_match - self.t_request

    @property
    def wait_for_pickup(self) -> float | None:
        """Tempo total entre o pedido e a recolha (min). É o KPI de espera."""
        if self.t_pickup is None:
            return None
        return self.t_pickup - self.t_request


@dataclass
class Vehicle:
    """Um veículo TVDE com o respetivo motorista."""

    id: int
    zone: int                 # zona atual (LocationID)
    capacity: int = 1         # 1 sem pooling, 2 com pooling

    status: VehicleStatus = VehicleStatus.IDLE
    passengers: list[int] = field(default_factory=list)  # ids dos pedidos a bordo
    km_empty: float = 0.0     # km sem passageiros (recolha + reposicionamento)
    km_loaded: float = 0.0    # km com passageiros
    busy_time: float = 0.0    # minutos fora do estado IDLE (para a utilização)

    @property
    def is_free(self) -> bool:
        return self.status == VehicleStatus.IDLE

    @property
    def has_space(self) -> bool:
        return len(self.passengers) < self.capacity