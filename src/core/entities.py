from dataclasses import dataclass

@dataclass
class Request:
    id: int
    t_request: float        # minutos desde o fim do jogo
    origin: int             # ID da zona TLC
    destination: int
    patience: float         # espera máxima por match (min)
    t_match: float | None = None
    t_pickup: float | None = None
    t_dropoff: float | None = None
    status: str = "waiting" # waiting | matched | riding | served | abandoned

@dataclass
class Vehicle:
    id: int
    zone: int
    status: str = "idle"    # idle | to_pickup | busy | relocating
    capacity: int = 1
    km_empty: float = 0.0
    km_loaded: float = 0.0