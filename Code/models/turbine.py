# models/turbine.py
from dataclasses import dataclass
import numpy as np
from enum import Enum

class Gearbox(Enum):
    HIGH_SPEED = "High-Speed"
    MEDIUM_SPEED= "Medium-Speed"
    NONE = "None"

class Generator(Enum):
    DFIG = "DFIG"
    SYNCHRONOUS = "Synchronous"
    ASYNCHRONOUS = "Asynchronous"


# Uppslagstabell som mappar enums till dina beräkningsfaktorer
DRIVETRAIN_SPECS = {
    (Gearbox.HIGH_SPEED, Generator.DFIG):          {"drivetrain_efficiency": 0.94, "downtime": 0.05, "capex_mod": 1.00, "opex_mod": 1.00, "mass_mod": 1.00},
    (Gearbox.MEDIUM_SPEED, Generator.SYNCHRONOUS): {"drivetrain_efficiency": 0.95, "downtime": 0.03, "capex_mod": 1.08, "opex_mod": 0.80, "mass_mod": 0.85},
    (Gearbox.NONE, Generator.SYNCHRONOUS):         {"drivetrain_efficiency": 0.96, "downtime": 0.02, "capex_mod": 1.25, "opex_mod": 0.50, "mass_mod": 1.50},
    (Gearbox.HIGH_SPEED, Generator.ASYNCHRONOUS):   {"drivetrain_efficiency": 0.88, "downtime": 0.06, "capex_mod": 0.90, "opex_mod": 1.15, "mass_mod": 1.05},
    (Gearbox.MEDIUM_SPEED, Generator.ASYNCHRONOUS): {"drivetrain_efficiency": 0.89, "downtime": 0.05, "capex_mod": 1.00, "opex_mod": 1.10, "mass_mod": 1.00},
    
    # Orealistiska/Straffade kombinationer
    (Gearbox.NONE, Generator.DFIG):                {"drivetrain_efficiency": 0.70, "downtime": 0.20, "capex_mod": 3.00, "opex_mod": 2.00, "mass_mod": 2.50},
    (Gearbox.MEDIUM_SPEED, Generator.DFIG):        {"drivetrain_efficiency": 0.90, "downtime": 0.06, "capex_mod": 1.15, "opex_mod": 1.10, "mass_mod": 1.10},
    (Gearbox.NONE, Generator.ASYNCHRONOUS):         {"drivetrain_efficiency": 0.50, "downtime": 0.30, "capex_mod": 4.00, "opex_mod": 3.00, "mass_mod": 4.00},
}
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
