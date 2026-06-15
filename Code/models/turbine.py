# models/turbine.py
from dataclasses import dataclass, field
import numpy as np
from enum import Enum
from scipy.interpolate import CubicSpline

class Gearbox(Enum):
    HIGH_SPEED = "High-Speed"
    MEDIUM_SPEED= "Medium-Speed"
    NONE = "None (Direct Drive)"


class Generator(Enum):
    DFIG = "DFIG"
    SYNCHRONOUS = "Synchronous"
    ASYNCHRONOUS = "Asynchronous"


# Uppslagstabell som mappar enums till dina beräkningsfaktorer
DRIVETRAIN_SPECS = {
    (Gearbox.HIGH_SPEED, Generator.DFIG):          {"drivetrain_efficiency": 0.94, "downtime": 0.05, "drivetrain_modifier": 1.00, "opex_modifier": 1.00, "nacelle_mass_modifier": 1.00},
    (Gearbox.MEDIUM_SPEED, Generator.SYNCHRONOUS): {"drivetrain_efficiency": 0.95, "downtime": 0.03, "drivetrain_modifier": 1.08, "opex_modifier": 0.80, "nacelle_mass_modifier": 0.85},
    (Gearbox.NONE, Generator.SYNCHRONOUS):         {"drivetrain_efficiency": 0.96, "downtime": 0.02, "drivetrain_modifier": 1.25, "opex_modifier": 0.50, "nacelle_mass_modifier": 1.50},
    (Gearbox.HIGH_SPEED, Generator.ASYNCHRONOUS):   {"drivetrain_efficiency": 0.88, "downtime": 0.06, "drivetrain_modifier": 0.90, "opex_modifier": 1.15, "nacelle_mass_modifier": 1.05},
    (Gearbox.MEDIUM_SPEED, Generator.ASYNCHRONOUS): {"drivetrain_efficiency": 0.89, "downtime": 0.05, "drivetrain_modifier": 1.00, "opex_modifier": 1.10, "nacelle_mass_modifier": 1.00},
    
    # Orealistiska/Straffade kombinationer
    (Gearbox.NONE, Generator.DFIG):                {"drivetrain_efficiency": 0.70, "downtime": 0.20, "drivetrain_modifier": 3.00, "opex_modifier": 2.00, "nacelle_mass_modifier": 2.50},
    (Gearbox.MEDIUM_SPEED, Generator.DFIG):        {"drivetrain_efficiency": 0.90, "downtime": 0.06, "drivetrain_modifier": 1.15, "opex_modifier": 1.10, "nacelle_mass_modifier": 1.10},
    (Gearbox.NONE, Generator.ASYNCHRONOUS):         {"drivetrain_efficiency": 0.50, "downtime": 0.30, "drivetrain_modifier": 4.00, "opex_modifier": 3.00, "nacelle_mass_modifier": 4.00},
}
@dataclass
class WindTurbine:
    rotor_diameter: float  # [m] Rotordiameter
    height: float  # [m] Navhöjd (tornhöjd)
    solidity: float  # [%] Soliditet (bladyta mot svept area)
    blades: int  # Antal blad (2, 3 eller 4)
    gearbox: Gearbox # "None (Direct Drive)", "Medium-Speed", "High-Speed"
    generator: Generator # "Synchronous", "Asynchronous", "DFIG"
    top_diameter: float = 3.25 # [m] top tower diameter
    bottom_diameter: float = 5.0 # [m] bottom tower diameter
    wall_thickness: float = 0.05 # [m] thickness of walls in tower
    lifetime:int = 25 # [y] lifetime of WEC
    _cp_spline: CubicSpline = field(init=False, repr=False)

    def __post_init__(self):
        # Initiera spline för capture efficiency
        sigma_pts = np.array([0.0,   0.015, 0.025, 0.040, 0.060, 0.100, 0.200])
        cp_pts    = np.array([0.0,   0.25,  0.38,  0.48,  0.42,  0.25,  0.00])

        # 2. skapa interpolatorn med cubicspline
        # bc_type='clamped' tvingas derivatan till 0 vid ändpunkterna för snyggare kurva
        self._cp_spline = CubicSpline(sigma_pts, cp_pts, bc_type='clamped') # type: ignore


    @property
    def drivetrain_specs(self):
        """Hämtar beräkningsfaktorer för vald drivlina."""
        return DRIVETRAIN_SPECS[self.gearbox, self.generator]

    @property
    def swept_area(self) -> float:
        """Beräknar svept area i m²."""
        return np.pi * (self.rotor_diameter / 2.0) ** 2


    @property
    def drivetrain_efficiency(self) -> float:
        """Drivlinans verkningsgrad."""
        return self.drivetrain_specs["drivetrain_efficiency"]

    @property
    def downtime(self) -> float:
        """Planerat/oplanerat stillestånd (downtime)."""
        return self.drivetrain_specs["downtime"]

    @property
    def drivetrain_modifier(self) -> float:
        """Kostnadsmodifikator för CAPEX (drivlina)."""
        return self.drivetrain_specs["drivetrain_modifier"]

    @property
    def opex_modifier(self) -> float:
        """Kostnadsmodifikator för OPEX (drift och underhåll)."""
        return self.drivetrain_specs["opex_modifier"]

    @property
    def nacelle_mass_modifier(self) -> float:
        """Massmodifikator för tornets dimensionering / nacellevikt."""
        return self.drivetrain_specs["nacelle_mass_modifier"]

    @property
    def capture_efficiency(self) -> float:
        """Returns capture efficiency calculated from solidity
        Cubic interpolated for solidity between 0 and 0.1 with (sigma_pts, cp_pts) above.
        Then linearly declining to 0.04 at solidity=0.5, lastly 0.04."""
        v = self._cp_spline(self.solidity) # type:ignore
        if self.solidity > 0.1:
            value_at_01 = self._cp_spline(0.1) # type:ignore
            t = (self.solidity-0.1)/(0.5-0.1) # [0,1] from first solidity=0.1 to solidity=0.5
            res = value_at_01+t*(0.04-value_at_01) # Linear interpolation
        else:
            res = v # Cubic interpol
        return res if res >= 0.04 else 0.04
        
