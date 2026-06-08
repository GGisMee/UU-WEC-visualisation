import datetime

class InputData:
    """
    Container for wind turbine simulation input data.

    Parameters are partially provided by the user (diameter, height) and 
    partially derived from the user's Social Security Number (SSN) to 
    simulate personalized environmental and economic factors.

    Parameters
    ----------
    name : str
        The name of the user or project.
    SSN : str
        Social Security Number in YYYYMMDDXXXX format.
    diam : int
        Diameter of the wind turbine rotor in meters.
    height : int
        Height of the wind turbine tower in meters.

    Attributes
    ----------
    NAME : str
        Stored name.
    SSN : str
        Stored SSN.
    AGE : int
        Approximate age derived from SSN.
    Y : int
        Birth year from SSN.
    M : int
        Birth month from SSN.
    D : int
        Birth day from SSN.
    PIN : int
        The last 4 digits (personal identification number) from SSN.
    diam : int
        Rotor diameter.
    height : int
        Tower height.
    n_param : float
        Economic parameter derived from birth month and year parity.
    e_param : float
        Economic parameter derived from birth day.
    wo_param : float
        Economic parameter derived from birth month.
    k_factor : float
        Weibull shape parameter (k) for wind speed distribution.
    avg_U10 : float
        Average wind speed at 10m height [m/s].
    roughness : float
        Surface roughness length [mm].
    downtime : float
        Estimated annual downtime [%].
    capture_efficiency : float
        Aerodynamic capture efficiency (Cp).
    efficiency_drivetrain : float
        Mechanical and electrical efficiency of the drivetrain.
    """
    def __init__(self, name: str, SSN: str, diam: int, height: int) -> None:
        self.update(name, SSN, diam, height)

    def update(self, name: str, SSN: str, diam: int, height: int):
        """
        Update the simulation parameters with new input values.

        Parameters
        ----------
        name : str
            The name of the user or project.
        SSN : str
            Social Security Number in YYYYMMDDXXXX format.
        diam : int
            Diameter of the wind turbine rotor in meters.
        height : int
            Height of the wind turbine tower in meters.
        """
        self.NAME = name
        self.SSN = SSN
        self.AGE, self.Y, self.M, self.D, self.PIN = self.partition(SSN)

        # Diameter and height data straight from user
        self.diam = diam
        self.height = height

        self.get_parameters_economics()
        self.get_paramaters_energy()

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

    def get_parameters_economics(self):
        """
        Derive economic functional parameters from birth date components.
        """
        self.n_param = self.M / 12 * (-1 if (self.Y % 2) == 0 else 1)
        self.e_param = self.D / 30 * (-1 if (self.D % 2) == 0 else 1)
        self.wo_param = 6 + self.M / 6

    def get_paramaters_energy(self):
        """
        Derive energy simulation parameters from SSN components.

        Calculates k-factor, average wind speed, roughness, downtime, 
        and efficiencies based on the user's SSN.
        """
        self.k_factor = int(11+self.M)/10
        self.avg_U10 = int((6+self.D/10)*10)/10-self.height/50
        self.roughness:int = self.M*self.D 
        self.downtime = abs(2000-self.Y)+1

        # Maybe calculate these differently
        self.capture_efficiency = 0.54-self.M/100 
        self.efficiency_drivetrain = 0.94-(self.PIN - round(self.PIN,-2))/400 # efficiency of internal mechanical system

        # print(self.k_factor, self.avg_U10, self.roughness, self.downtime, self.capture_efficiency, self.efficiency_drivetrain))