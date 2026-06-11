# models/environment.py
from enum import Enum
from dataclasses import dataclass

class DefaultEnvironments(Enum):
    

@dataclass
class SiteEnvironment:
    
    # Miljö & Vindresurser
    avg_wind_10: float  # Average wind speed at 10m [m/s]
    roughness: float  # Surface roughness length z0 [mm] (t.ex. 0.01 för hav)
    survival_gust: float  # Stormbyar för överlevnad [m/s] (t.ex. 60m/s)
    k_factor: float  # Weibull shape parameter k for wind distrobution

    # Effektivitetsparametrar (Härleds oftast från SSN)
    lifetime: int # Livslängd i år
    downtime: float  # Årlig downtime [%]
    capture_efficiency: float  # Cp (0.0 - 0.5)
    drivetrain_efficiency: float  # Verkningsgrad för generator/växellåda (0.0 - 1.0)

    # Ekonomi & Marknad
    electricity_price: float # [€/MWh] 
    green_certificate: float = 1.0  # Miljöcertifikat [€/MWh] 
    inflation: float = 0.02  # [%] 
    interest: float = 0.03  # Ränta [%] 

    # Defaulted fields at the bottom
    wo_param: float = 7.0  # for determinating turbine cost
    financial_additional_part: float = 0.07  # [%] additional costs for loans, fees and so on for funding.
    installation_costs: int = 3500  # k€
    turbine_count: int = 1  # number of turbines in park (Set to 1 by default)

