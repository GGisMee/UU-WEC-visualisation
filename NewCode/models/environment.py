# models/environment.py
from dataclasses import dataclass


@dataclass
class SiteEnvironment:
    # Miljö & Vindresurser
    avg_wind_u10: float  # Average wind speed at 10m [m/s]
    roughness: float  # Surface roughness length z0 [mm] (t.ex. 0.01 för hav)
    survival_gust: float  # Stormbyar för överlevnad [m/s] (t.ex. 60m/s)
    k_factor: float  # Weibull shape parameter k for wind distrobution

    # Effektivitetsparametrar (Härleds oftast från SSN)
    downtime: float  # Årlig downtime [%]
    capture_efficiency: float  # Cp (0.0 - 0.5)
    drivetrain_efficiency: float  # Verkningsgrad för generator/växellåda (0.0 - 1.0)

    # Economic parameters for cost calculations
    wo_param: float # for determinating turbine cost

    # Ekonomi & Marknad
    electricity_price: float  # [€/MWh]
    green_certificate: float  # Miljöcertifikat [€/MWh] (standard 1.0)
    inflation: float  # [%] (standard 2.0)
    interest: float  # Ränta [%] (standard 3.0)
    lifetime: int  # Livslängd i år
    financial_costs_additional: float # [%] additional costs for loans, fees and so on for funding.
    installation_costs:int = 3500 # k€

    turbine_count:int = 1 # number of turbines in park (Set to 1 by default)
