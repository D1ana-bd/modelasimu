"""Mundo abstrato: cidade em grelha com o estádio no centro.

O resto do modelo só usa este objeto para saber distâncias, tempos,
para onde dar o próximo passo e se uma célula está na zona do evento.
Assim pode, no futuro, ser trocado por um mapa real (world/nyc_world.py)
sem mexer nos agentes.

Distâncias "Manhattan" (como ruas em quadrícula): |dx| + |dy| células.
"""

from __future__ import annotations

import numpy as np

Cell = tuple[int, int]


class GridWorld:
    def __init__(self, params: dict) -> None:
        w = params["world"]
        self.width: int = w["width"]
        self.height: int = w["height"]
        self.cell_km: float = w["cell_km"]
        self.min_trip_cells: int = w["min_trip_cells"]
        self.event_zone_radius: int = w["event_zone_radius"]
        self.tick_minutes: float = params["time"]["tick_minutes"]
        self.stadium: Cell = (self.width // 2, self.height // 2)

    # --------------------------------------------------------- medidas

    def distance(self, a: Cell, b: Cell) -> int:
        """Distância em células (Manhattan)."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def travel_time(self, a: Cell, b: Cell) -> float:
        """Tempo de viagem em minutos (um carro anda 1 célula por passo)."""
        return self.distance(a, b) * self.tick_minutes

    def distance_km(self, a: Cell, b: Cell) -> float:
        return self.distance(a, b) * self.cell_km

    # ----------------------------------------------------------- zonas

    def in_event_zone(self, cell: Cell) -> bool:
        """A célula está na zona do evento (até `event_zone_radius` do estádio)?"""
        return self.distance(cell, self.stadium) <= self.event_zone_radius

    # -------------------------------------------------------- movimento

    def step_towards(self, a: Cell, b: Cell) -> Cell:
        """Próxima célula no caminho de a para b (primeiro em x, depois em y)."""
        x, y = a
        if x != b[0]:
            x += 1 if b[0] > x else -1
        elif y != b[1]:
            y += 1 if b[1] > y else -1
        return (x, y)

    # ---------------------------------------------------------- sorteios

    def random_cell(self, rng: np.random.Generator) -> Cell:
        """Uma célula qualquer da cidade (uniforme)."""
        return (int(rng.integers(self.width)), int(rng.integers(self.height)))

    def random_destination(self, rng: np.random.Generator, origin: Cell) -> Cell:
        """Destino ao acaso, a pelo menos `min_trip_cells` da origem."""
        while True:
            cell = self.random_cell(rng)
            if self.distance(cell, origin) >= self.min_trip_cells:
                return cell

    def random_cell_near_stadium(self, rng: np.random.Generator, radius: int) -> Cell:
        """Célula ao acaso a no máximo `radius` células do estádio."""
        while True:
            cell = self.random_cell(rng)
            if self.distance(cell, self.stadium) <= radius:
                return cell