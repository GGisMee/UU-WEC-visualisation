# models/environment.py
from enum import Enum
from dataclasses import dataclass
import datetime
import numpy as np

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
        """
        Calculates wind speed at a specific hub height using logarithmic wind shear.
        
        Parameters
        ----------
        height : float
            Hub height of the turbine [m].
            
        Returns
        -------
        float
            Wind speed at the specified height [m/s].
        """
        z0 = self.roughness / 1000.0
        return float(self.avg_wind_10 * np.log(height / z0) / np.log(10.0 / z0))

class SSNGenerator:
    @staticmethod
    def validate(ssn: str) -> bool:
        """
        Returns True if the social security number is in the format YYYYMMDDXXXX.
        
        Parameters
        ----------
        ssn : str
            The 12-digit Social Security Number.
            
        Returns
        -------
        bool
            True if valid, False otherwise.
        """
        return len(ssn) == 12 and ssn.isdigit()

    @staticmethod
    def apply_ssn_to_env(ssn: str, env: SiteEnvironment):
        """
        Modifies and returns a SiteEnvironment object based on the given SSN.
        
        Parameters
        ----------
        ssn : str
            The 12-digit Social Security Number.
        env : SiteEnvironment
            The environment object to be modified.
            
        Raises
        ------
        ValueError
            If the SSN is invalid.
        """
        if not SSNGenerator.validate(ssn):
            raise ValueError("Invalid SSN format. Use YYYYMMDDXXXX.")

        Age,Y,M,D,PIN = SSNGenerator.partition(ssn)

        env.wo_param = 6 + M / 6

        env.k_factor =(11+M)/10
       
        env.avg_wind_10 = abs(int((6+D/10)*10)/10-int(31.9+int(PIN/100)/2)*1.2/50)
        env.roughness = M*D 


    @staticmethod
    def partition(SSN: str) -> tuple[int, int, int, int, int]:
        """
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
        if len(SSN) != 12:  # We want YYYYMMDDSSSS format, meaning 12 characters
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

    @staticmethod
    def generate_random_pm(i:int,name:str) -> float:
        """
        Generates a 'random' float in range [-1,1], which value persists when i and name are the same.
        
        Parameters
        ----------
        i : int
            Index or seed integer.
        name : str
            Seed string.
            
        Returns
        -------
        float
            Random value in range [-1, 1].
        """
        return 2*SSNGenerator.generate_random(i,name)-1


    @staticmethod
    def generate_random(i:int,name:str) -> float:
        """
        Generates a 'random' float in range [0,1], which value persists when i and name are the same.
        
        Parameters
        ----------
        i : int
            Index or seed integer.
        name : str
            Seed string.
            
        Returns
        -------
        float
            Random value in range [0, 1].
        """
        return (hash((i, name)) % 10**10) / 10**10 

if __name__ == '__main__':
    # env = SiteEnvironment(None,None,None,None,22,None,None,None)
    # SSNGenerator.apply_ssn_to_env("200301019949", env)
    # print(env)
    pass

