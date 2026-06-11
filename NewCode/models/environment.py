# models/environment.py
from enum import Enum
from dataclasses import dataclass
import datetime


class DefaultEnvironments(Enum):
    SANDBOX = "sandbox"
    ARCTIC_GALE = "arctic_gale"
    THE_GENTLE_BREEZE = "the_gentle_breeze"
    THE_COMMUNITY_COOPERATIVE = "the_community_cooperative"

    def create(self) -> SiteEnvironment:
        # Matchar enum-värdet och returnerar rätt Mission
        match self:
            case DefaultEnvironments.SANDBOX:
                env = SiteEnvironment(

                )
            
            case DefaultEnvironments.ARCTIC_GALE:
                return SiteEnvironment()

            
            case DefaultEnvironments.SANDBOX:
                return SiteEnvironment()

            case DefaultEnvironments.THE_COMMUNITY_COOPERATIVE:
                return SiteEnvironment()

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




class SSNGenerator:
    @staticmethod
    def validate(ssn: str) -> bool:
        """Returnerar True om personnumret är i formatet YYYYMMDDXXXX."""
        return len(ssn) == 12 and ssn.isdigit()

    @staticmethod
    def apply_ssn_to_env(ssn: str, env: SiteEnvironment):
        """Modifierar och returnerar ett SiteEnvironment-objekt baserat på SSN."""
        if not SSNGenerator.validate(ssn):
            raise ValueError("Invalid SSN format. Use YYYYMMDDXXXX.")

        Age,Y,M,D,PIN = SSNGenerator.partition(ssn)

        env.wo_param = 6 + M / 6

        env.k_factor =(11+M)/10
       
        env.avg_wind_10 = abs(int((6+D/10)*10)/10-int(31.9+int(PIN/100)/2)*1.2/50)
        env.roughness = M*D 
        env.downtime = abs(2000-Y)+1

        env.capture_efficiency = 0.54-M/100 
        env.drivetrain_efficiency = 0.94-(PIN - round(PIN,-2))/400 # efficiency of internal mechanical system

        


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
    env = SiteEnvironment(None,None,None,None,22,None,None,None, electricity_price=30)
    SSNGenerator.apply_ssn_to_env("200301019949", env)
    print(env)

