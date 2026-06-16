# models/turbine.py
from dataclasses import dataclass, field
import numpy as np
from enum import Enum
from scipy.interpolate import CubicSpline
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    pass


class Gearbox(Enum):
    HIGH_SPEED = "High-Speed"
    MEDIUM_SPEED= "Medium-Speed"
    NONE = "None (Direct Drive)"


class Generator(Enum):
    DFIG = "DFIG"
    SYNCHRONOUS = "Synchronous"
    ASYNCHRONOUS = "Asynchronous"


class DrivetrainSpecs(TypedDict):
    """Data class for drivetrain specifications for combinations of gearbox and generator."""
    drivetrain_efficiency: float
    downtime: float
    drivetrain_modifier: float
    opex_modifier: float
    nacelle_mass_modifier: float
    description: str

# Lookup table mapping (Gearbox, Generator)-combinations to DrivetrainSpecs 
DRIVETRAIN_SPECS: dict[tuple[Gearbox, Generator], DrivetrainSpecs] = {
    (Gearbox.HIGH_SPEED, Generator.DFIG):          {"drivetrain_efficiency": 0.94, "downtime": 0.05, "drivetrain_modifier": 1.00, "opex_modifier": 1.00, "nacelle_mass_modifier": 1.00, "description": "A high gear ratio steps up the low rotor speed (ω) to high velocities. This mechanical amplification allows for a smaller generator size and lower weight. However, the high speed increases friction losses and heat within the gear teeth."},
    (Gearbox.MEDIUM_SPEED, Generator.SYNCHRONOUS): {"drivetrain_efficiency": 0.95, "downtime": 0.03, "drivetrain_modifier": 1.08, "opex_modifier": 0.80, "nacelle_mass_modifier": 0.85, "description": "A moderate gear ratio reduces mechanical stress and kinetic energy inside the transmission. Paired with a synchronous generator, it achieves good magnetic flux linkage at lower shaft speeds. This setup balances the torque-speed trade-off without requiring an oversized stator diameter."},
    (Gearbox.NONE, Generator.SYNCHRONOUS):         {"drivetrain_efficiency": 0.96, "downtime": 0.02, "drivetrain_modifier": 1.25, "opex_modifier": 0.50, "nacelle_mass_modifier": 1.50, "description": "The generator rotor is locked directly to the low-speed turbine shaft. To induce grid voltage at this low speed, the synchronous generator needs a massive diameter with many magnetic pole pairs. This eliminates gearbox wear completely but increases structural weight in the nacelle."},
    (Gearbox.HIGH_SPEED, Generator.ASYNCHRONOUS):   {"drivetrain_efficiency": 0.88, "downtime": 0.06, "drivetrain_modifier": 0.90, "opex_modifier": 1.15, "nacelle_mass_modifier": 1.05, "description": "A maximum gear ratio provides the high speed needed to create magnetic slip in the induction machine. While this high velocity keeps the generator volume small, the extra gear stages introduce higher friction. The setup shows how mechanical speed can compensate for a basic generator topology."},
    (Gearbox.MEDIUM_SPEED, Generator.ASYNCHRONOUS): {"drivetrain_efficiency": 0.89, "downtime": 0.05, "drivetrain_modifier": 1.00, "opex_modifier": 1.10, "nacelle_mass_modifier": 1.00, "description": "Operating this induction generator at a moderate speed reduces high-frequency drivetrain vibrations. However, lowering the input shaft velocity compresses the available magnetic slip range. Consider how this shifting operating point affects the torque-speed curve and power conversion."},
    
    # Orealistiska/Straffade kombinationer
    (Gearbox.NONE, Generator.DFIG):                {"drivetrain_efficiency": 0.70, "downtime": 0.20, "drivetrain_modifier": 3.00, "opex_modifier": 2.00, "nacelle_mass_modifier": 2.50, "description":"Without a gearbox, the DFIG rotor spins at the very low velocity of the main shaft. DFIG machines rely on high relative speeds between stator and rotor fields to induce voltage. Consider how the generator size must scale to achieve rated power when input RPM is this low."},
    (Gearbox.MEDIUM_SPEED, Generator.DFIG):        {"drivetrain_efficiency": 0.90, "downtime": 0.06, "drivetrain_modifier": 1.15, "opex_modifier": 1.10, "nacelle_mass_modifier": 1.10, "description":"This setup lowers the generator input speed by using a smaller gear ratio. Since a DFIG is optimized for a specific, higher velocity window, a medium input speed shifts the system away from its design point. Look at how a lower mechanical step-up impacts the excitation efficiency."},
    (Gearbox.NONE, Generator.ASYNCHRONOUS):         {"drivetrain_efficiency": 0.50, "downtime": 0.30, "drivetrain_modifier": 4.00, "opex_modifier": 3.00, "nacelle_mass_modifier": 4.00, "description":"Connecting an asynchronous machine directly to the slow turbine rotor removes the speed multiplier. Asynchronous induction relies heavily on high slip speeds to create a strong magnetic field. To couple electromagnetically at low RPM, the design requires an extreme number of pole pairs."},
}
@dataclass
class WindTurbine:
    rotor_diameter: float  # [m] Rotor diameter
    height: float  # [m] Hub height (tower height)
    solidity: float  # [%] Solidity (blade area to swept area)
    blades: int  # Number of blades (2, 3 or 4)
    gearbox: Gearbox # "None (Direct Drive)", "Medium-Speed", "High-Speed"
    generator: Generator # "Synchronous", "Asynchronous", "DFIG"
    top_diameter: float = 3.25 # [m] top tower diameter
    bottom_diameter: float = 5.0 # [m] bottom tower diameter
    wall_thickness: float = 0.05 # [m] thickness of walls in tower
    lifetime:int = 25 # [y] lifetime of WEC
    _cp_spline: CubicSpline = field(init=False, repr=False)

    def __post_init__(self):
        # Initialize spline for capture efficiency
        sigma_pts = np.array([0.0,   0.015, 0.025, 0.040, 0.060, 0.100, 0.200])
        cp_pts    = np.array([0.0,   0.25,  0.38,  0.48,  0.42,  0.25,  0.00])

        # 2. Create the interpolator using CubicSpline
        # bc_type='clamped' forces the derivative to 0 at the endpoints for a smoother curve
        self._cp_spline = CubicSpline(sigma_pts, cp_pts, bc_type='clamped') # type: ignore


    @property
    def drivetrain_specs(self):
        """Retrieves calculation factors for the chosen drivetrain."""
        return DRIVETRAIN_SPECS[self.gearbox, self.generator]

    @property
    def swept_area(self) -> float:
        """Calculates swept area in m²."""
        return np.pi * (self.rotor_diameter / 2.0) ** 2


    @property
    def drivetrain_efficiency(self) -> float:
        """Drivetrain efficiency."""
        return self.drivetrain_specs["drivetrain_efficiency"]

    @property
    def downtime(self) -> float:
        """Planned/unplanned downtime."""
        return self.drivetrain_specs["downtime"]

    @property
    def drivetrain_modifier(self) -> float:
        """Cost modifier for CAPEX (drivetrain)."""
        return self.drivetrain_specs["drivetrain_modifier"]

    @property
    def opex_modifier(self) -> float:
        """Cost modifier for OPEX (operation and maintenance)."""
        return self.drivetrain_specs["opex_modifier"]

    @property
    def nacelle_mass_modifier(self) -> float:
        """Mass modifier for tower dimensioning / nacelle weight."""
        return self.drivetrain_specs["nacelle_mass_modifier"]


    @property
    def generator_gearbox_description(self) -> str:
        """Description of Gearbox Generator combination."""
        return self.drivetrain_specs["description"]


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


    @property
    def slenderness_ratio(self) -> float:
        return self.height / (2 * (self.bottom_diameter / 2))

    @property
    def tower_mass(self) -> float:
        r_bottom = self.bottom_diameter / 2
        r_top = self.top_diameter / 2
        volume = np.pi * self.height * self.wall_thickness * (r_bottom + r_top - self.wall_thickness)
        return volume * 7850  # kg/m^3

