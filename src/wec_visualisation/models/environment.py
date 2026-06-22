# models/environment.py
from enum import Enum
from dataclasses import dataclass
import datetime
import numpy as np
import hashlib

# class Spread

class DefaultEnvironments(Enum):
    SANDBOX = "sandbox"
    ARCTIC_GALE = "arctic_gale"
    THE_GENTLE_BREEZE = "the_gentle_breeze"
    THE_COMMUNITY_COOPERATIVE = "the_community_cooperative"

    def create(self) -> "SiteEnvironment":
        # Matchar enum-värdet och returnerar rätt Mission
        match self:
            case DefaultEnvironments.SANDBOX:
                env = SiteEnvironment(
                    avg_wind_10 = 7.0,             # m/s (~8.5 m/s vid hubhöjd 65m)
                    roughness = 0.2,               # mm, öppet vatten/kust
                    survival_gust = 59.5,          # m/s (IEC klass II referens, ~1.4x Vref)
                    k_factor = 1.84,               # Lillgrund Weibull-fit
                    electricity_price = 55,        # €/MWh
                    green_certificate = 1.0,       # €/MWh
                    inflation = 0.02,              # 2.0 %
                    interest = 0.03,               # 3.0 %
                    is_offshore=False
                )
            
            case DefaultEnvironments.ARCTIC_GALE:
                return SiteEnvironment(
                    avg_wind_10 = 8.5,             # m/s, högre offshore-medelvind
                    roughness = 0.2,               # mm, öppet hav
                    survival_gust = 65.0,          # m/s, klass S/Tropical-nivå
                    k_factor = 2.0,                # lägre variabilitet på öppet hav
                    electricity_price = 60,        # €/MWh
                    green_certificate = 1.0,       # €/MWh
                    is_offshore= True
                )

            
            case DefaultEnvironments.THE_GENTLE_BREEZE:
                return SiteEnvironment(
                    avg_wind_10 = 4.5,             # m/s, låg vid 10m i skog
                    roughness = 500.0,             # mm, hög ytråhet (skog)
                    survival_gust = 50.0,          # m/s, IEC klass IIIA onshore-förhållanden
                    k_factor = 1.8,                # mer variabel vind inlandet
                    electricity_price = 50,        # €/MWh
                    green_certificate = 1.0,       # €/MWh
                    is_offshore=False
                )

            case DefaultEnvironments.THE_COMMUNITY_COOPERATIVE:
                return SiteEnvironment(
                    avg_wind_10 = 5.5,             # m/s, måttlig med stabil vind inlandet
                    roughness = 30.0,              # mm, platt landskap/jordbruksmark
                    survival_gust = 50.0,          # m/s, standard IEC klass IIIA/IIIB
                    k_factor = 2.4,                # mycket stabil vind
                    electricity_price = 48,        # €/MWh (matchar lägre budgetförutsättningar)
                    green_certificate = 1.0,       # €/MWh
                    is_offshore=False
                )
        return env

@dataclass
class SiteEnvironment:
    # Miljö & Vindresurser
    avg_wind_10: float  # Average wind speed at 10m [m/s]
    roughness: float  # Surface roughness length z0 [mm] (t.ex. 0.01 för hav)
    survival_gust: float  # Stormbyar för överlevnad [m/s] (t.ex. 60m/s)
    k_factor: float  # Weibull shape parameter k for wind distrobution
    is_offshore: bool


    # Economics & Marknad
    electricity_price: float # [€/MWh] 
    green_certificate: float = 1.0  # Miljöcertifikat [€/MWh] 
    inflation: float = 0.02  # [%] 
    interest: float = 0.03  # Ränta [%] 

    # Defaulted fields at the bottom
    wo_param: float = 7.0  # for determinating turbine cost
    financial_additional_part: float = 0.07  # [%] additional costs for loans, fees and so on for funding. Percentage of capex
    turbine_count: int = 1  # number of turbines in park (Set to 1 by default)

    def calculate_wind_at_height(self, height: float) -> float:
        """Information Expert: calculates wind speed at a specific hub height using logarithmic wind shear."""
        z0 = self.roughness / 1000.0
        return float(self.avg_wind_10 * np.log(height / z0) / np.log(10.0 / z0))

@dataclass
class SSNSpread:
    """A dataclass for storing how much each environment variable can spread out from normal value when SSN is applied. Stored as fractions (0.05 ~ 5%)"""
    avg_wind_10_spread: float = 0.10
    roughness_spread: float = 0.2
    survival_gust_spread: float = 0.05
    k_factor_spread: float = 0.05
    electricity_price_spread: float = 0.1
    green_certificate_spread: float = 0.05
    inflation_spread: float = 0.20
    interest_spread: float = 0.15

class SSNGenerator:
    @staticmethod
    def validate(ssn: str) -> bool:
        """Returnerar True om personnumret är i formatet YYYYMMDDXXXX."""
        return len(ssn) == 12 and ssn.isdigit()

    @staticmethod
    def apply_ssn_to_env(ssn: str, env: SiteEnvironment) -> SiteEnvironment:
        """Modifierar och returnerar ett SiteEnvironment-objekt baserat på SSN."""
        if not SSNGenerator.validate(ssn):
            raise ValueError("Invalid SSN format. Use YYYYMMDDXXXX.")
        ssn_int = int(ssn) # Safe because of validation above
        spreads = SSNSpread()
        env.avg_wind_10 = SSNGenerator.apply_spread(env.avg_wind_10, spreads.avg_wind_10_spread, ssn_int, "avg_wind_10")
        env.roughness = SSNGenerator.apply_spread(env.roughness, spreads.roughness_spread, ssn_int, "roughness")
        env.survival_gust = SSNGenerator.apply_spread(env.survival_gust, spreads.survival_gust_spread, ssn_int, "survival_gust")
        env.k_factor = SSNGenerator.apply_spread(env.k_factor, spreads.k_factor_spread, ssn_int, "k_factor")
        env.electricity_price = SSNGenerator.apply_spread(env.electricity_price, spreads.electricity_price_spread, ssn_int, "electricity_price")
        env.green_certificate = SSNGenerator.apply_spread(env.green_certificate, spreads.green_certificate_spread, ssn_int, "green_certificate")
        env.inflation = SSNGenerator.apply_spread(env.inflation, spreads.inflation_spread, ssn_int, "inflation")
        env.interest = SSNGenerator.apply_spread(env.interest, spreads.interest_spread, ssn_int, "interest")
        return env



    @staticmethod
    def apply_spread(start_value:float, spread:float, SSN:int,name:str) -> float:
        """Applies spread to start_value using SSN as seed value and name to differentiate between different variables spread"""
        interval = 2*SSNGenerator.generate_random(SSN,name)-1 # creates interval [-1,1]
        interval = 1+interval*spread # becomes [1-spread, 1+spread]
        return float(start_value * interval)


    @staticmethod
    def generate_random(i: int, name: str) -> float:
        """Generates a deterministic float in range [0,1] based on seed (i) and name."""
        seed_str = f"{i}_{name}"
        hash_obj = hashlib.sha256(seed_str.encode('utf-8'))
        hash_int = int.from_bytes(hash_obj.digest()[:8], 'little')
        return hash_int / (2**64 - 1) 


    @staticmethod
    def partition(SSN: str) -> tuple[int, int, int, int, int]:
        """
        CURRENTLY NOT IN USE. 
        Split the SSN into year, month, day, and personal identification number.

        Parameters
        ----------
        SSN : str
            The 12-digit Social Security Number (YYYYMMDDXXXX).

        Returns
        -------
        Age : int
            Approximate age based on current year.
        Y : int
            Birth year.
        M : int
            Birth month.
        D : int
            Birth day.
        S : int
            Last 4 digits (PIN).

        Raises
        ------
        ValueError
            If the SSN is not 12 digits or contains non-numeric characters.
        """
        if len(SSN) != 12:  # Vi vill ha YYYYMMDDSSSS format, dvs 12 tecken
            raise ValueError("Expected SSN format with 12 characters")
        if not SSN.isdigit():
            raise ValueError("SSN number is not formatted as a number")
        Y = int(SSN[0:4])
        M = int(SSN[4:6])
        D = int(SSN[6:8])
        S = int(SSN[8:12])

        year = datetime.date.today().year
        Age = year - Y  # Approximatelly
        return Age, Y, M, D, S

if __name__ == '__main__':
    # env = SiteEnvironment(None,None,None,None,22,None,None,None)
    # SSNGenerator.apply_ssn_to_env("200301019949", env)
    # print(env)
    pass

