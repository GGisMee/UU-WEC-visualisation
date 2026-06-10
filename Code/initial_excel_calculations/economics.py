# import customtkinter
from dataclasses import dataclass
import numpy as np
from initial_excel_calculations.user_input import InputData
from initial_excel_calculations.energy_calculations import EnergyCalculations, CalculationResults

@dataclass
class FinanceConstants:
    """A set of constant values that are used in the financial calculations."""
    interest: float = 0.03 # [%] interest
    inflation: float = 0.02 # [%] inflation
    lifetime: int = 22 # [years] lifetime of the turbine
    financial_costs_additional: float = 0.07 # [%] additional costs for loans, fees and so on for funding.
    price_electricity: float = 29  # [euro / MWh] price of electricity
    green_certificate: float = 1  # [euro / MWh] value of green certificates
    

class Economics:
    """
    Financial model for evaluating wind turbine profitability.

    Calculates capital expenditure (CAPEX), operational expenditure (OPEX),
    annual savings, and overall project profitability metrics.

    Parameters
    ----------
    user_input_data : InputData
        Object containing user-specific parameters and dimensions.
    energy_output_data : CalculationResults
        Results from the energy simulation (power, energy, etc.).

    Attributes
    ----------
    input_data : InputData
        Stored input parameters.
    output_data : CalculationResults
        Stored energy results.
    turbine_count : int
        Number of turbines in the project (default is 1).
    finansial_costs : FinanceConstants
        Set of constant values used in the financial calculations.
    """
    def __init__(
        self, user_input_data: InputData, energy_output_data: CalculationResults
    ) -> None:
        self.input_data = user_input_data
        self.output_data = energy_output_data
        self.turbine_count = 1
        self.finansial_costs = FinanceConstants()

    def capital_costs(self) -> float:
        """
        Calculate total capital expenditure (CAPEX) for the turbine.

        Includes costs for the turbine, drivetrain, nacelle, tower,
        and foundation.

        Returns
        -------
        float
            Total capital costs in k€.
        """
        rated_power = self.output_data.rated_power / 1000  # MW
        diam = self.input_data.diam  # m
        tower_H = self.input_data.height  # m

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

        return turbine + drivetrain_nacell + tower + foundation_site

    def installation_costs(self) -> float:
        """
        Calculate costs for grid connections, roads, cables and site installations.

        Returns
        -------
        float
            Installation costs in k€.
        """
        return 3500  # k€

    def operational_maintenance(self) -> float:
        """
        Calculate annual operational and maintenance (O&M) costs.

        Includes maintenance, insurance, land lease, and decommissioning funds.

        Returns
        -------
        float
            Annual O&M costs in k€/year.
        """
        rated_power = self.output_data.rated_power / 1000
        # prop to PP
        maintenance = 600 * (rated_power * self.turbine_count / 84)
        # Removed below to fount for only one
        # PR = 20 * (rated_power * self.turbine_count / 84) ** 0.3  # local icehockey club sponsoring
        # prop to sqrt(PP)
        insurance = 100 * (rated_power * self.turbine_count / 84) ** 0.5
        # prop to number of WECs
        land_cost = 360 * self.turbine_count / 28
        fund_decomissioning = 200 * rated_power * self.turbine_count / 84

        return maintenance + insurance + land_cost + fund_decomissioning

    def annual_savings(self) -> float:
        """
        Calculate net annual savings.

        Computed as: (Generated Energy * Total Price) - O&M Costs.

        Returns
        -------
        float
            Annual net savings in k€/year.
        """
        generated_power = (
            self.output_data.generated_energy * 0.95 * self.turbine_count
        )  # [MWh] I9*turbine_count*0.95
        annual_income = (
            generated_power * (self.finansial_costs.price_electricity + self.finansial_costs.green_certificate) / 1000
        )  # k€/MWh
        return annual_income - self.operational_maintenance()

    def calculate_profits(
        self, total_capex: float, annual_savings: float
    ) -> tuple[float, float]:
        """
        Calculate total project profit and margin over its lifetime.

        Uses a Net Present Value (NPV) approach considering inflation and interest.

        Parameters
        ----------
        total_capex : float
            Total capital costs. 
        annual_savings : float
            Annual net savings.

        Returns
        -------
        profits : float
            Total lifetime profit in k€.
        margin : float
            Profitability margin (Profits / CAPEX).
        """

        interest = self.finansial_costs.interest
        inflation = self.finansial_costs.inflation
        ### calculate lifetime
        lifetime = self.finansial_costs.lifetime  # in years

        # proximity_number = 0.5
        # Ingen reduction då vi bara räknar på en
        # lifetime_reduction = 7*proximity_number/self.turbine_count
        # lifetime -= lifetime_reduction * min(1, self.input_data.height/self.input_data.diam) # scale depending on height
        financial_costs = self.finansial_costs.financial_costs_additional * total_capex  # k€, additional to capex. For loans, fees and so on for funding.

        k_factor = (1 + inflation) / (1 + interest)  # quote of interest / inflation

        # Scale savings using geometrical series formula with k_factor over lifetime years
        # In k€
        net_present_value = (
            annual_savings * (k_factor * (1 - k_factor**lifetime)) / (1 - k_factor)
        )

        profits = net_present_value - total_capex - financial_costs  # k€
        margin = profits / total_capex
        return profits, margin

    def update(self):
        """
        Perform a full economic update and print results.
        """
        capital_costs = self.capital_costs()
        total_capex = capital_costs + self.installation_costs()

        annual_savings = self.annual_savings()  # k€
        profits, margin = self.calculate_profits(total_capex, annual_savings)

        print(f"Profits: {profits:.2f} k€, Margin: {margin * 100:.2f}%")


def main():
    """Testfunktion för filen"""
    input_data = InputData("Gustav Gamstedt", "200301019949", diam=81, height=97)
    energy_calculations = EnergyCalculations(input_data)
    economics = Economics(input_data, energy_calculations.output_data)
    economics.update()


if __name__ == "__main__":
    main()
