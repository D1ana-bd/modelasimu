"""Mundo abstrato: grelha com o estádio no centro.

O resto do modelo só usa este objeto para saber distâncias, tempos e
para onde dar o próximo passo. Assim, mais tarde, pode ser trocado por
um mundo com o mapa real (world/nyc_world.py) sem mexer nos agentes.

Distâncias em "Manhattan" (como ruas em quadrícula): |dx| + |dy| células.
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
        self.tick_minutes: float = params["tick_minutes"]
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

    def random_destination(self, rng: np.random.Generator) -> Cell:
        """Destino ao acaso na grelha, a pelo menos `min_trip_cells` do estádio."""
        while True:
            cell = (int(rng.integers(self.width)), int(rng.integers(self.height)))
            if self.distance(cell, self.stadium) >= self.min_trip_cells:
                return cell

    def random_cell_near_stadium(self, rng: np.random.Generator, radius: int) -> Cell:
        """Célula ao acaso a no máximo `radius` células do estádio."""
        while True:
            dx, dy = (int(v) for v in rng.integers(-radius, radius + 1, size=2))
            cell = (self.stadium[0] + dx, self.stadium[1] + dy)
            if (0 <= cell[0] < self.width and 0 <= cell[1] < self.height
                    and self.distance(cell, self.stadium) <= radius):
                return cell