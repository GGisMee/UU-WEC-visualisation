import numpy as np
import datetime

class InputData:
    """Class for storing input data. Partially inputed (diam, height), partially generated from SSN
    Generated from init. 
    To update data with new info use update(...) function"""
    def __init__(self, name: str, SSN: str, diam:int, height:int) -> None:
        """Insert name and social security number. Will later be used for generating costs and other variables
        Also input diameter for windblades and height of WEC"""
        self.update(name, SSN, diam, height)

    def update(self, name: str, SSN: str, diam:int, height:int):
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
        """Delar upp SSN i Y,M,D,S
        Där S är 4 sista siffrorna"""
        if len(SSN) != 12:  # Vi vill ha YYYYMMDDSSSS format, dvs 12 tecken
            assert NameError, "Expected SSN format with 12 characters"
        if not SSN.isdigit():
            assert TypeError, "SSN number is not formatted as a number"
        Y = int(SSN[0:4])
        M = int(SSN[4:6])
        D = int(SSN[6:8])
        S = int(SSN[8:12])

        year = datetime.date.today().year
        Age = year - Y  # Approximatelly
        return Age, Y, M, D, S

    def get_parameters_economics(self):
        """Skapar parametrar som sedan kan användas för att generera värden"""
        """Uses extracted age variables to get some functional parameters"""
        self.n_param = self.M / 12 * (-1 if (self.Y % 2) == 0 else 1)
        self.e_param = self.D / 30 * (-1 if (self.D % 2) == 0 else 1)
        self.wo_param = 6 + self.M / 6

    def get_paramaters_energy(self):
        """Creates paramaters later used to calculate energy created by wind turbine
        Creates; k-factor, Avg wind speed at 10 m height [m/s], Roughness [mm], Downtime [%]
        Does so using SSN info"""
        self.k_factor = int(11+self.M)/10
        self.avg_U10 = round(6+self.D, -1)-self.height/50
        self.roughness:int = self.M*self.D 
        self.downtime = abs(2000-self.Y)+1

        # Maybe calculate these differently
        self.capture_efficiency = 0.54-self.M/100 
        self.efficiency_drivetrain = 0.94-(self.PIN - round(self.PIN,-2))/400 # efficiency of internal mechanical system

        # print(self.k_factor, self.avg_U10, self.roughness, self.downtime, self.capture_efficiency, self.efficiency_drivetrain)

class EnergyCalculations:
    def __init__(self, input_data: InputData):
        self.input_data = input_data

        self.z0 = self.input_data.roughness/1000
        self.wind_nacelle = (
            self.input_data.avg_U10* 
            np.log(self.input_data/self.z0)/
            np.log(10/self.z0)
        ) # From formula

    @staticmethod
    def calculate():
        wind_speeds = np.arange(1, 60)

        P()



if __name__ == "__main__":

    input_data = InputData(name="Hans Bernhoff", SSN="199903151234", diam=37, height=44)


