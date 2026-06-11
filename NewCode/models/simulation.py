# models/simulation.py
from dataclasses import dataclass
import numpy as np
from scipy.special import gamma
from scipy.optimize import root_scalar
from NewCode.models.turbine import WindTurbine
from NewCode.models.environment import SiteEnvironment
import NewCode.config
from collections import namedtuple
from NewCode.utils.ssn import SSNGenerator

@dataclass
class SimulationResult:
    # Vind & Effekt
    wind_nacelle: float # m/s
    weibull_C: float
    weibull_k: float
    rated_wind_speed: float # m/s
    cut_in_speed: float # m/s
    cut_out_speed: float # m/s
    rated_power: float # kW
    generated_energy: float  # MWh/år
    capacity_factor: float  # [%]

    # Krafter & Hållfasthet
    aerodynamical_load: float  # kN
    storm_load: float  # kN
    wall_thickness_op: float  # mm
    wall_thickness_storm: float  # mm
    safety_factor: float  # Budget (150mm) / max(op, storm)
    is_unsafe: bool

    # Ekonomi
    capex_components: tuple # (X, Y, Z, W) representing costs for turbine, drivetrain, tower, foundation [k€]
    total_capex: float  # k€
    annual_opex: float  # k€/år
    annual_revenue: float  # k€/år
    npv_profit: float  # k€
    IRR: float # [%]
    margin: float  # [%]
    payback_years: float # [y]


class SimulationEngine:
    @staticmethod
    def simulate(turbine: WindTurbine, env: SiteEnvironment) -> SimulationResult:
        
        # 1. Vindberäkningar
        wind_nacelle, weibull_k, weibull_C, wind_speeds, possible_hours, available_hours = SimulationEngine._wind_distrobution(turbine, env)
        

        # 2. Energiberäkningar
        energy_per_m2, cut_in, rated_speed, cut_out = SimulationEngine._operational_limits(turbine, env, wind_speeds, possible_hours, wind_nacelle)

        generated_energy, rated_power = SimulationEngine.energy_production(turbine, env, wind_speeds, cut_in, cut_out, rated_speed, energy_per_m2, available_hours)

        # 3. Hållfasthetsberäkningar
        aurodynamical_load, storm_load, wall_thickness_op, wall_thickness_storm = SimulationEngine.structural_forces(turbine, rated_speed, env)

        # 4. Ekonomikalkyl (CAPEX, OPEX och NPV med geometrisk serie för inflation/ränta)
        total_capex, capital_cost_components = SimulationEngine._capital_costs(turbine, env, rated_power)
        
        annual_opex, operational_maintenance_cost_components = SimulationEngine._operational_maintenance(env, rated_power)
        annual_savings, annual_revenue= SimulationEngine._annual_earnings(env, generated_energy, annual_opex)

        # Profits here are NPV
        profits, margin = SimulationEngine._calculate_profits(total_capex, annual_savings, env)
        IRR = SimulationEngine.IRR(total_capex, annual_savings, env.lifetime)

        #! 5. Beräkna säkerhetsfaktor och is_unsafe (Kolla på denna)
        safety_factor = 150.0 / max(wall_thickness_op, wall_thickness_storm)
        is_unsafe = safety_factor < 1.0


        print(f"Profits: {profits} k€, Margin: {margin*100}%")
        # 5. Returnera SimulationResult med alla värden
        return SimulationResult(
            wind_nacelle=wind_nacelle,
            weibull_C=weibull_C,
            weibull_k=weibull_k,
            rated_wind_speed=rated_speed,
            cut_in_speed=cut_in,
            cut_out_speed=cut_out,
            rated_power=rated_power * env.turbine_count,
            generated_energy=generated_energy * env.turbine_count,
            capacity_factor=1,
            aerodynamical_load=aurodynamical_load,
            storm_load=storm_load,
            wall_thickness_op=wall_thickness_op,
            wall_thickness_storm=wall_thickness_storm,
            safety_factor=safety_factor,
            is_unsafe=is_unsafe,
            capex_components=capital_cost_components,
            total_capex=total_capex,
            annual_opex=annual_opex,
            annual_revenue=annual_revenue,
            npv_profit=profits,
            IRR = IRR,
            margin=margin,
            payback_years=total_capex/annual_savings
        )

    @staticmethod
    def _wind_distrobution(turbine: WindTurbine, env: SiteEnvironment):
        z0 = env.roughness / 1000.0
        wind_nacelle: float = (
            env.avg_wind_10 * np.log(turbine.height / z0) / np.log(10 / z0)
        )

        h = 1  # step value. Increase for better resolution
        wind_speeds = np.arange(1, 61, h)

        # Calculate distrobution
        k = env.k_factor
        C: float = wind_nacelle / gamma(1 + 1 / k)  # give characteristic windspeed
        distrobution: np.ndarray = (
            (k / C) * (wind_speeds / C) ** (k - 1) * np.exp(-((wind_speeds / C) ** k))
        )

        # Hours of the year
        possible_hours = distrobution * 8760
        availability = 1.0 - (env.downtime if env.downtime < 1.0 else env.downtime / 100.0)
        available_hours = availability * possible_hours

        return wind_nacelle, k,C,wind_speeds, possible_hours, available_hours

    @staticmethod
    def _operational_limits(turbine:WindTurbine, env:SiteEnvironment, wind_speeds, possible_hours, wind_nacelle):        
        energy_per_m2 = 0.62 * wind_speeds**3 * possible_hours / 1000  # KWh/m^2
        tot_possible_energy_per_m2 = np.sum(energy_per_m2)
        cumulated_energy = np.cumsum(energy_per_m2)

        # Corrected rated speed formula
        rated_speed = 12.0 - 0.15 * wind_nacelle

        # capped by turn off limit
        turn_off_limit = 0.8 * tot_possible_energy_per_m2
        capped_mask = cumulated_energy > turn_off_limit
        idx = np.argmax(capped_mask)
        cut_out = wind_speeds[idx]

        cut_in = int(rated_speed * 0.01 ** (1 / 3) * 10) / 10  # [m/s] speeds below are to slow

        return energy_per_m2, cut_in, rated_speed, cut_out

    @staticmethod
    def energy_production(turbine:WindTurbine, env:SiteEnvironment, wind_speeds, cut_in, cut_out, rated_speed, energy_per_m2, available_hours):
        swept_area = np.pi * (turbine.diameter / 2) ** 2

        rated_power = 0.62 * rated_speed**3 * swept_area / 1000 * env.capture_efficiency*env.drivetrain_efficiency
        
        conditions = [
            wind_speeds <= cut_in,  # values below cut_in, therefore set to 0 below
            (wind_speeds > cut_in) & (wind_speeds <= rated_speed),  # variable energies
            (wind_speeds > rated_speed)
            & (wind_speeds <= cut_out),  # Between rated and cut_out, therefore constant
            wind_speeds > cut_out,  # values above cut_out
        ]

        availability = 1.0 - (env.downtime if env.downtime < 1.0 else env.downtime / 100.0)

        alternatives = [
            0,  # Shut off, zone 1
            energy_per_m2
            * swept_area
            * env.capture_efficiency
            * env.drivetrain_efficiency
            * availability,  # zone 2
            rated_power
            * available_hours,  # zone 3, Since between rated and cutout. Energy output will just be rated_power*available_hours. Constant.
            0,  # zone 4, Shut off
        ]

        generated_energies = np.select(
            conditions, alternatives
        )  # Energy for different windspeeds in kWh

        generated_energy = (
            np.sum(generated_energies) / 1000
        )  # Total energy per year in MWh

        return generated_energy, rated_power

    @staticmethod
    def structural_forces(turbine:WindTurbine, rated_speed, env:SiteEnvironment):
        swept_area = np.pi * (turbine.diameter / 2) ** 2

        # C_T=8/9, 1.2 from density of air.
        aerodynamical_load = (
            1 / 2 * 1.2 * 8 / 9 * swept_area * rated_speed**2 / 1000
        )  # [kN] force excerted on tower from wind

        storm_load = (
            1 / 2 * 1.2 * 1.5 * turbine.solidity * swept_area * env.survival_gust**2 / 1000
        )  #  @survival_gust [kN]. load under storm

        wall_thickness_operation = (
            aerodynamical_load
            * turbine.height
            / (np.pi * (turbine.height / 40) ** 2 * 160)
            * 2
        )
        wall_thickness_storm = (
            storm_load
            * turbine.height
            / (np.pi * (turbine.height / 40) ** 2 * 160)
            * 2
        )

        return aerodynamical_load, storm_load, wall_thickness_operation, wall_thickness_storm


    @staticmethod
    def _capital_costs(turbine:WindTurbine,env:SiteEnvironment, rated_power) ->tuple[float,tuple[float,float,float,float]]:
        """
        Calculate total capital expenditure (CAPEX) for the turbine.

        Includes costs for the turbine, drivetrain, nacelle, tower,
        and foundation.

        Returns
        -------
        float:
            sum of following scaled by number of WEC:s
        tuple:
            Tuple of costs for (k€)
            2. turbine
            3. drivetrain
            4. nacelle
            5. tower and foundation.
        """
        rated_power = rated_power / 1000  # MW
        diam = turbine.diameter  # m
        tower_H = turbine.height  # m

        # Skipped because only one WEC
        # PP = Part rated Power
        # proportional to sqrt(PP)
        # permits = 4000 * (rated_power * self.turbine_count / 80) ** 0.5
        # PROJECTS = 1200  # Fixed

        ### Costs WECs (Wind energy conversion system)
        # prop to diam^3.5
        turbine_costs = 900 * (env.wo_param / 7.5) ** 3 * (diam / 90) ** 3.5

        # prop to power*diam
        drivetrain_nacell = (
            800 * (env.wo_param / 7) * rated_power / 3 * diam / 90
        )

        # prop to diam^2 * height^2
        tower = (
            700
            * (env.wo_param / 7) ** 2.5
            * (diam / 90) ** 2
            * (tower_H / 90) ** 2
            + 300
        )

        # prop to (diam*height)^0.5
        foundation_site = 300 * (diam / 90 * tower_H / 100) ** (1 / 2)

        total_capex = (turbine_costs+drivetrain_nacell+tower+foundation_site) * env.turbine_count

        return total_capex, (turbine_costs, drivetrain_nacell, tower, foundation_site)


    @staticmethod
    def _operational_maintenance(env:SiteEnvironment, rated_power) -> tuple:
        """
        Calculate annual operational and maintenance (O&M) costs.

        Includes maintenance, insurance, land lease, and decommissioning funds.

        Returns
        -------
        tuple:
            Tuple of costs for (in k€)
            1. Total of below 
            2. maintenance
            3. insurance
            4. land lease and decommissioning.
        """
        total_power_MW = (rated_power / 1000) * env.turbine_count
        # prop to PP
        maintenance = 600 * (total_power_MW / 20)
        # prop to sqrt(PP)
        insurance = 100 * (total_power_MW / 20) ** 0.5
        # prop to number of WECs
        land_cost = 360 * env.turbine_count / 20
        fund_decomissioning = 200 * total_power_MW / 20

        annual_opex = maintenance+insurance+land_cost+fund_decomissioning

        return maintenance, insurance, land_cost, fund_decomissioning

    @staticmethod
    def _annual_earnings(env:SiteEnvironment, generated_energy, operational_maintenance_costs) -> tuple[float, float]:
        """
        Calculate net annual savings as well as annual income


        Returns
        -------
        float
            Annual net savings in k€/year. 
            Computed as: Annual Income - O&M Costs.
        float
            Annual income from energy (k€/year)

        """
        # Gross annual income (no 0.95 factor applied here, and turbine_count already factored in generated_energy)
        annual_income = generated_energy * env.turbine_count * (env.electricity_price + env.green_certificate) / 1000  # k€
        return annual_income - operational_maintenance_costs, annual_income

    @staticmethod
    def _calculate_profits(total_capex: float, annual_savings: float, env:SiteEnvironment) -> tuple[float, float]:
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

        interest = env.interest
        inflation = env.inflation
        ### calculate lifetime
        lifetime = env.lifetime  # in years

        # proximity_number = 0.5
        # Ingen reduction då vi bara räknar på en
        # lifetime_reduction = 7*proximity_number/self.turbine_count
        # lifetime -= lifetime_reduction * min(1, self.input_data.height/self.input_data.diam) # scale depending on height
        financial_costs = env.financial_additional_part* total_capex  # k€, additional to capex. For loans, fees and so on for funding.

        k_factor = (1 + inflation) / (1 + interest)  # quote of interest / inflation

        # Scale savings using geometrical series formula with k_factor over lifetime years
        # In k€
        net_present_value = (
            annual_savings * (k_factor * (1 - k_factor**lifetime)) / (1 - k_factor)
        )

        profits = net_present_value - total_capex - financial_costs  # k€
        margin = profits / total_capex
        return profits, margin

    @staticmethod
    def IRR(total_capex, annual_savings, years):
        """
        Calculate the Internal Rate of Return (IRR) for an investment.

        Parameters
        ----------
        total_capex : float
            Total capital expenditure in k€.
        annual_savings : float
            Annual net savings in k€.
        years : int
            Investment period in years.

        Returns
        -------
        IRR : float
            Internal rate of return as a decimal (e.g., 0.1 for 10%).
        """

        cash_flows = np.array((annual_savings*years-total_capex))

        npv = lambda r: np.sum(cash_flows/(1+r)**np.arange(len(cash_flows)))
        IRR = root_scalar(npv, bracket=[-0.99, 1], method='bentq')
        return IRR



if __name__ == "__main__":
    test_case = 1
    match test_case:

        case 0:
            env = SiteEnvironment(
                avg_wind_10 = None,
                roughness = None,
                survival_gust = None,
                k_factor = None,
                downtime = None,
                capture_efficiency = None,
                drivetrain_efficiency = None,
                turbine_count = 1,
                electricity_price = 29,
                green_certificate =1,
                financial_additional_part = 0.07,
                lifetime = 22,
            )
            SSNGenerator.apply_ssn_to_env("200301019949", env)
            #! Får fixa enums eller något för gearbox_type och generator
            turbine = WindTurbine(diameter=81, height=97, solidity=0.03, blades = 3,  gearbox= "None", generator="DFIG")
            print(env)
            print(turbine)
            print('\n', SimulationEngine.simulate(turbine, env))
        case 1:
            env = SiteEnvironment(
                avg_wind_10 = 7,
                roughness = 0.10,
                survival_gust = 60,
                k_factor = 2.0,
                downtime = 0.02,
                capture_efficiency = 0.44,
                drivetrain_efficiency = 0.92,
                turbine_count = 1,
                electricity_price = 40,
                green_certificate =2,
                financial_additional_part = 0.07,
                lifetime = 22,
            )
            #! Får fixa enums eller något för gearbox_type och generator
            turbine = WindTurbine(diameter=131, height=120, solidity=0.04, blades = 3,  gearbox= "None", generator="DFIG")
            print(env)
            print(turbine)
            print('\n', SimulationEngine.simulate(turbine, env))
        

