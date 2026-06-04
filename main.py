# import customtkinter
import numpy as np
import datetime


class StudentData:
    def __init__(self, name: str, SSN: str) -> None:
        """Insert name and social security number. Will later be used for generating costs and other variables"""
        self.NAME = name
        self.SSN = SSN
        self.AGE, self.Y, self.M, self.D, self.S = self.partition(SSN)
        self.format_parameters()

    def format_parameters(self):
        """Skapar parametrar som sedan kan användas för att generera värden"""
        """Uses extracted age variables to get some functional parameters"""
        self.n_param = self.M / 12 * (-1 if (self.Y % 2) == 0 else 1)
        self.e_param = self.D / 30 * (-1 if (self.D % 2) == 0 else 1)
        self.wo_param = 6 + self.M / 6

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


class Economics:
    def __init__(self, studentData: StudentData) -> None:
        self.studentData = studentData

    def capital_costs(self):
        """Permit and Wind energy conversion system costs"""
        rat_power = 2.8  # MW
        diam = 95  # m
        tower_H = 105  # m
        number_of_turbines = 16

        permits = 4000 * np.sqrt(rat_power * number_of_turbines / 80)
        PROJECTS = 1200
        # Costs WECs (Wind energy conversion system)
        turbine = 900 * (self.studentData.wo_param / 7.5) ** 3 * (diam / 90) ** 3.5

        drivetrain_nacell = (
            800 * (self.studentData.wo_param / 7) * rat_power / 3 * diam / 90
        )

        tower = (
            700
            * (self.studentData.wo_param / 7) ** 2.5
            * (diam / 90) ** 2
            * (tower_H / 90) ** 2
            + 300
        )

        foundation_site = 300 * (diam / 90 * tower_H / 100) ** (1 / 2)

        return (
            permits + PROJECTS + turbine + drivetrain_nacell + tower + foundation_site
        )

    def grid_connections():
        """Calculates costs for grid connections"""

        number_of_turbines = 16
        substation = C4 * W21 / 50


def main():
    print("Hello from uu-proj!")
    data = StudentData("Gustav Gamstedt", "199801281234")
    economics = Economics(data)
    economics.capital_costs()


if __name__ == "__main__":
    main()
