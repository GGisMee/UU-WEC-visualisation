# import customtkinter
import numpy as np
from user_input import InputData
from energy_calculations import EnergyCalculations, CalculationResults


class Economics:
    def __init__(self, user_input_data: InputData, energy_output_data: CalculationResults) -> None:
        self.input_data= user_input_data
        self.output_data = energy_output_data
        self.turbine_count = 1
        self.PRICE_ELECTRICITY = 29 # euro / MWh
        self.GREEN_CERTIFICATE = 1 # euro / MWh

    def capital_costs(self):
        """Permit and Wind energy conversion system costs (k€)"""
        rated_power = self.output_data.rated_power/1000 # MW
        diam = self.input_data.diam # m
        tower_H = self.input_data.height # m

        # Skipped because only one WEC
        # PP = Part rated Power
        # proportional to sqrt(PP)
        # permits = 4000 * (rated_power * self.turbine_count / 80) ** 0.5
        # PROJECTS = 1200  # Fixed

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
            turbine + drivetrain_nacell + tower + foundation_site
        )

    def grid_connections(self):
        """Calculates costs for grid connections (k€)"""

        rated_power = self.output_data.rated_power/1000

        substation = rated_power * self.turbine_count * 50
        site_installations = 1000
        print(substation)
        return substation + site_installations

    def operational_maintenance(self):
        """Operational and maintenance costs per year (k€/year)"""
        rated_power = self.output_data.rated_power/1000
        # prop to PP
        maintenance = 600 * (rated_power * self.turbine_count / 84)
        # Removed below to fount for only one
        # PR = 20 * (rated_power * self.turbine_count / 84) ** 0.3  # local icehockey club sponsoring
        # prop to sqrt(PP)
        insurance = 100*(rated_power*self.turbine_count/84)**0.5
        # prop to number of WECs
        land_cost = 360 * self.turbine_count / 28
        fund_decomissioning = 200*rated_power*self.turbine_count/84
        
        return maintenance+insurance+land_cost+fund_decomissioning

    def annual_savings(self):
        """Calculates savings per year, by taking annual income - operational_maintenance costs
        In k€ / year"""
        generated_power = self.output_data.generated_energy * 0.95*self.turbine_count # [MWh] I9*turbine_count*0.95 
        annual_income = generated_power* (self.PRICE_ELECTRICITY+self.GREEN_CERTIFICATE) / 1000 # k€/MWh
        return annual_income - self.operational_maintenance()

    def calculate_profits(self, total_capex, annual_savings) -> tuple[float,float]:
        """Calculates total profit and margin for the windturbine park
        Returns: profits: float (k€), margin:float"""

        interest = 0.03 
        inflation = 0.02
        ### calculate lifetime
        lifetime = 22 # in years


        # proximity_number = 0.5
        # Ingen reduction då vi bara räknar på en
        # lifetime_reduction = 7*proximity_number/self.turbine_count
        # lifetime -= lifetime_reduction * min(1, self.input_data.height/self.input_data.diam) # scale depending on height
        financial_costs = 0.07*total_capex # k€

        k_factor = (1+inflation)/(1+interest) # quote of interest / inflation

        # Scale savings using geometrical series formula with k_factor over lifetime years
        # In k€
        net_present_value = annual_savings * (k_factor * (1 - k_factor**lifetime)) / (1 - k_factor)

        profits = net_present_value-total_capex-financial_costs # k€
        margin = profits/total_capex 
        return profits, margin 

    def update(self):
        capital_costs = self.capital_costs()
        # Skippar pga en turbin
        # grid_connections_costs = self.grid_connections()
        total_capex =capital_costs # Removed because only on one: +grid_connections_costs
        annual_savings = self.annual_savings() # k€
        profits, margin = self.calculate_profits(total_capex, annual_savings)

        print(profits, margin)

        
def main():
    print("Hello from uu-proj!")
    input_data = InputData("Gustav Gamstedt", "199801281234", diam=95, height=105)
    energy_calculations = EnergyCalculations(input_data)
    economics = Economics(input_data, energy_calculations.output_data)
    economics.update()

if __name__ == "__main__":
    main()
