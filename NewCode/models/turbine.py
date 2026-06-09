# models/turbine.py
from dataclasses import dataclass
import numpy as np


@dataclass
class WindTurbine:
    diameter: float  # [m] Rotordiameter
    height: float  # [m] Navhöjd (tornhöjd)
    solidity: float  # [%] Soliditet (bladyta mot svept area)
    blades: int  # Antal blad (2, 3 eller 4)
    gearbox: str  # "None (Direct Drive)", "Medium-Speed", "High-Speed"
    generator: str  # "Synchronous", "Asynchronous", "DFIG"

    @property
    def swept_area(self) -> float:
        """Beräknar svept area i m²."""
        return np.pi * (self.diameter / 2.0) ** 2
