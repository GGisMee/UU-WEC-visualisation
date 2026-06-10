# utils/ssn.py
from models.environment import SiteEnvironment
import datetime

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

