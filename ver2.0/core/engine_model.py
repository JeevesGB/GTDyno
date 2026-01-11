from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class EngineModel:
    car_id: str
    layout: str
    valvetrain: str
    aspiration: str
    sound_file: int

    displacement: int
    idle_rpm: int
    max_rpm: int
    redline_rpm: int
    clutch_release_rpm: int = 0
    power_multiplier: int = 100

    curve: List[Tuple[int, float]] = field(default_factory=list)

    def sorted_curve(self):
        return sorted(self.curve, key=lambda p: p[0])
