"""Estados e tipos dos agentes (iguais aos do modelo conceptual)."""

from enum import Enum


class PassengerType(str, Enum):
    """De onde vem o pedido."""

    CITY = "city"    # procura normal, em qualquer ponto da cidade
    EVENT = "event"  # pico do evento, no estádio


class RequestStatus(str, Enum):
    """Ciclo do passageiro."""

    WAITING = "waiting"      # à espera de match
    MATCHED = "matched"      # já tem carro, à espera que chegue
    RIDING = "riding"        # em viagem
    SERVED = "served"        # chegou ao destino
    ABANDONED = "abandoned"  # desistiu (vai de metro / a pé)


class VehicleStatus(str, Enum):
    """Ciclo do carro."""

    IDLE = "idle"              # livre
    TO_PICKUP = "to_pickup"    # a caminho da recolha
    BUSY = "busy"              # com passageiro
    RELOCATING = "relocating"  # a reposicionar-se, vazio