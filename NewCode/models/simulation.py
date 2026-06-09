# models/simulation.py
from dataclasses import dataclass
import numpy as np
from scipy.special import gamma
from models.turbine import WindTurbine
from models.environment import SiteEnvironment
import config

@dataclass
class SimulationResult:
    # Vind & Effekt
    hub_wind_speed: float
    weibull_C: float
    weibull_k: float
    rated_wind_speed: float
    cut_in_speed: float
    cut_out_speed: float
    rated_power: float
    generated_energy: float      # AEP i MWh/år
    capacity_factor: float       # CF [%]
    
    # Krafter & Hållfasthet
    operational_thrust: float    # kN
    storm_thrust: float          # kN
    wall_thickness_op: float     # mm
    wall_thickness_storm: float  # mm
    safety_factor: float         # Budget (150mm) / max(op, storm)
    is_unsafe: bool
    
    # Ekonomi
    capex_components: dict       # {"turbine": X, "drivetrain": Y, "tower": Z, "foundation": W}
    total_capex: float           # k€
    annual_opex: float           # k€/år
    annual_revenue: float        # k€/år
    npv_profit: float            # k€
    margin: float                # %
    payback_years: float

class SimulationEngine:
    @staticmethod
    def simulate(turbine: WindTurbine, env: SiteEnvironment) -> SimulationResult:
        # 1. Vindberäkning med logaritmisk profil (Wind Shear)
        # z0 = env.roughness / 1000.0
        # hub_wind = env.avg_wind_u10 * ln(turbine.height / z0) / ln(10 / z0)
        
        # 2. Weibull-fördelning (Scipy Gamma)
        # C = hub_wind / gamma(1 + 1/env.k_factor)
        
        # 3. Effektkurva & Integrering (AEP)
        # Integrera effekt över 8760 timmar baserat på cut-in, rated och cut-out
        
        # 4. Hållfasthet (Krafter vid 11.5 m/s och 60 m/s storm)
        # Använd formler för böjmoment och räkna ut t_op samt t_storm.
        
        # 5. Ekonomikalkyl (CAPEX, OPEX och NPV med geometrisk serie för inflation/ränta)
        
        # 6. Returnera SimulationResult med alla värden
