# import customtkinter
import numpy as np
import datetime


class InputData:
    """Class for storing input data. Partially inputed (diam, height), partially generated from SSN
    Generated from init. 
    To update data with new info use update(...) function"""
    def __init__(self, name: str, SSN: str, diam:int, height:int) -> None:
        """Insert name and social security number. Will later be used for generating costs and other variables
        Also diamater for windblades and height of WEC"""
        self.update(name, SSN, diam, height)

    def update(self, name: str, SSN: str, diam:int, height:int):
        self.NAME = name
        self.SSN = SSN
        self.AGE, self.Y, self.M, self.D, self.PIN = self.partition(SSN)


        # Diamater and height data straight from user
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
        self.roughness = self.M*self.D 
        self.downtime = abs(2000-self.Y)+1

        # Maybe calculate these differently
        self.capture_efficiency = 0.54-self.M/100 
        self.efficiency_drivetrain = 0.94-(self.PIN - round(self.PIN,-2))/400 # efficiency of internal mechanical system

        # print(self.k_factor, self.avg_U10, self.roughness, self.downtime, self.capture_efficiency, self.efficiency_drivetrain)


class Economics:
    def __init__(self, input_data: InputData) -> None:
        self.input_data= input_data

    def capital_costs(self):
        """Permit and Wind energy conversion system costs (k€)"""
        rated_power = 2.8  # MW
        diam = 95  # m
        tower_H = 105  # m
        turbine_count = 16

        # PP = Part rated Power
        # proportional to sqrt(PP)
        permits = 4000 * (rated_power * turbine_count / 80) ** 0.5
        PROJECTS = 1200  # Fixed

        ### Costs WECs (Wind energy conversion system)
        # prop to diam^3.5
        turbine = 900 * (self.input_data.wo_param / 7.5) ** 3 * (diam / 90) ** 3.5

        # prop to power*diam
        drivetrain_nacell = (
            800 * (self.input_data.wo_param / 7) * rated_power / 3 * diam / 90
        )

        # prop to diam^2 * height^2
        tower = (
            700
            * (self.input_data.wo_param / 7) ** 2.5
            * (diam / 90) ** 2
            * (tower_H / 90) ** 2
            + 300
        )

        # prop to (diam*height)^0.5
        foundation_site = 300 * (diam / 90 * tower_H / 100) ** (1 / 2)

        return (
            permits + PROJECTS + turbine + drivetrain_nacell + tower + foundation_site
        )

    def grid_connections(self):
        """Calculates costs for grid connections (k€)"""

        turbine_count = 16
        rated_power = 2.8

        substation = rated_power * turbine_count * 50
        site_installations = 1000
        print(substation)
        return substation + site_installations

    def operational_maintenence(self):
        """Operational and maintenence costs per year (k€/year)"""
        rated_power = 2.8
        turbine_count = 16
        # prop to PP
        maintenance = 600 * (rated_power * turbine_count / 84)
        PR = (
            20 * (rated_power * turbine_count / 84) ** 0.3
        )  # local icehockey club sponsoring
        # prop to sqrt(PP)
        insurance = 100*(rated_power*turbine_count/84)**0.5
        # prop to number of WECs
        land_cost = 360 * turbine_count / 28
        fund_decomissioning = 200*rated_power*turbine_count/84
        
        return maintenance+PR+insurance+land_cost+fund_decomissioning

    def annual_savings(self):
        """Calculates savings per year, by taking annual income - operatiol_maintanence costs
        In k€ / year"""
        generated_power = 124,706 # I9*turbine_count*0.95 # MWh, ask if it should be connected to sheet 2 or sheet 1
        PRICE_ELECTRICITY = 29 # euro / MWh
        GREEN_CERTIFICATE = 1 # euro / MWh
        annual_income = generated_power* (PRICE_ELECTRICITY+GREEN_CERTIFICATE) / 1000 # k€/MWh
        return annual_income - self.operational_maintenence()

    def calculate_profits(self) -> tuple[float,float]:
        """Calculates total profit and margin for the windturbine park
        Returns: profits: float (k€), margin:float"""
        total_capex = self.capital_costs()+self.grid_connections()+self.operational_maintenence()
        annual_savings = self.annual_savings() # k€
        turbine_count = 16
        proximity_number = 0.5

        interest = 0.03 
        inflation = 0.02
        ### calculate lifetime
        lifetime = 22 # in years
        lifetime_reduction = -7*proximity_number/turbine_count
        lifetime -= lifetime_reduction * min(1, self.input_data.height/self.input_data.diam) # scale depending on height
        financial_costs = 0.07*total_capex # k€

        k_factor = (1+inflation)/(1+interest) # quote of interest / inflation

        # Scale savings using geometrical series formula with k_factor over lifetime years
        # In k€
        net_present_value = annual_savings*(k_factor-k_factor**(lifetime+1))/(1-k_factor)

        profits = net_present_value-total_capex # k€
        margin = profits/total_capex 
        return profits, margin








def main():
    print("Hello from uu-proj!")
    data = InputData("Gustav Gamstedt", "199801281234")
    economics = Economics(data)
    economics.operational_maintenence()


if __name__ == "__main__":
    main()
