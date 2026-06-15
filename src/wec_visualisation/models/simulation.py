# models/simulation.py
from dataclasses import dataclass
import numpy as np
from scipy.special import gamma
from scipy.optimize import root_scalar

from src.wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator
from src.wec_visualisation.models.environment import SiteEnvironment, SSNGenerator
import src.wec_visualisation.config as config

@dataclass(frozen=True)
class StructuralReport:
    aerodynamical_load: float  # kN
    storm_load: float          # kN
    slenderness_ratio: float   # [-]
    breaking_utilization: float         # [-] Breaking factor
    buckeling_utilization: float         # [-] Breaking factor
    rna_mass: float            # [kg] Rotor Nacelle Assembly mass

@dataclass(frozen=True)
class FinancialReport:
    capex_components: dict[str,float]
    total_capex: float
    annual_opex: float
    annual_revenue: float
    npv_profit: float
    IRR: float
    margin: float
    payback_years: float

@dataclass 
class WindClimate:
    """Represents wind factors at nacelle height for a certain turbine at a certain SiteEnvironment"""
    wind_nacelle: float
    weibull_k: float
    weibull_C: float
    wind_speeds: np.ndarray
    available_hours: np.ndarray
    possible_hours: np.ndarray

    @property
    def energy_density_per_m2(self) -> np.ndarray:
        return 0.62 * self.wind_speeds**3 * self.possible_hours / 1000.0

    @property
    def total_potential_energy(self) -> float:
        return float(np.sum(self.energy_density_per_m2))

    @property
    def rated_wind_speed(self) -> float:
        return 12.0 - 0.15 * self.wind_nacelle

    @property
    def cut_in_speed(self) -> float:
        return int(self.rated_wind_speed * (0.01 ** (1.0 / 3.0)) * 10.0) / 10.0

    @property
    def cut_out_speed(self) -> float:
        cumulated_energy = np.cumsum(self.energy_density_per_m2)
        turn_off_limit = 0.8 * self.total_potential_energy
        capped_mask = cumulated_energy > turn_off_limit
        idx = np.argmax(capped_mask)
        return float(self.wind_speeds[idx])


class ClimateService:
    @staticmethod
    def calculate_wind_climate(env: SiteEnvironment, turbine: WindTurbine) -> WindClimate:
        """
        Calculate the wind climate characteristics at the turbine's nacelle height.
        
        Args:
            env: Site environment containing surface roughness and average wind data.
            turbine: Wind turbine configuration.
            
        Returns:
            WindClimate containing Weibull parameters and arrays of wind speeds [m/s] 
            and their associated operational hours per year [h].
        """
        wind_nacelle = env.calculate_wind_at_height(turbine.height)
        
        h = 1  # step value
        wind_speeds = np.arange(1, 61, h)
        k = env.k_factor
        C = wind_nacelle / gamma(1 + 1 / k)
        
        distribution = (k / C) * (wind_speeds / C) ** (k - 1) * np.exp(-((wind_speeds / C) ** k))
        possible_hours = distribution * 8760
        
        availability = 1.0 - (turbine.downtime if turbine.downtime < 1.0 else turbine.downtime / 100.0)
        available_hours = availability * possible_hours
        
        return WindClimate(
            wind_nacelle=wind_nacelle,
            weibull_k=k,
            weibull_C=C,
            wind_speeds=wind_speeds,
            available_hours=available_hours,
            possible_hours=possible_hours
        )



class EnergyService:
    @staticmethod
    def calculate_production(turbine: WindTurbine, climate: WindClimate) -> tuple:
        """
        Compute the annual energy production for a given turbine and wind climate.
        
        Args:
            turbine (WindTurbine): Wind turbine configuration including swept area and efficiencies.
            climate (WindClimate): WindClimate containing distribution of available hours and speeds.
            
        Returns:
            tuple: (generated_energy [MWh], rated_power [kW], capacity_factor [-]).
        """
        rated_speed = climate.rated_wind_speed
        cut_in = climate.cut_in_speed
        cut_out = climate.cut_out_speed
        
        rated_power = 0.62 * rated_speed**3 * turbine.swept_area / 1000.0 * turbine.capture_efficiency * turbine.drivetrain_efficiency
        
        conditions = [
            climate.wind_speeds <= cut_in,
            (climate.wind_speeds > cut_in) & (climate.wind_speeds <= rated_speed),
            (climate.wind_speeds > rated_speed) & (climate.wind_speeds <= cut_out),
            climate.wind_speeds > cut_out
        ]
        
        availability = 1.0 - (turbine.downtime if turbine.downtime < 1.0 else turbine.downtime / 100.0)
        
        alternatives = [
            0.0,
            climate.energy_density_per_m2 * turbine.swept_area * turbine.capture_efficiency * turbine.drivetrain_efficiency * availability,
            rated_power * climate.available_hours,
            0.0
        ]
        
        generated_energies = np.select(conditions, alternatives)
        generated_energy = float(np.sum(generated_energies) / 1000.0) # MWh


        capacity_factor = generated_energy / (rated_power * 8760.0 / 1000.0) if rated_power > 0 else 0.0

        return generated_energy, rated_power, capacity_factor


class StructuralService:
    @staticmethod
    def calculate_loads(turbine: WindTurbine, rated_wind_speed: float, survival_gust: float) -> tuple[float, float]:
        """
        Calculate the structural loads acting on the turbine tower.
        
        Args:
            turbine: Wind turbine configuration.
            rated_wind_speed: Rated wind speed [m/s] for calculating aerodynamic load.
            survival_gust: Storm survival gust [m/s] for calculating storm load.
            
        Returns:
            Tuple of (aerodynamical_load [kN], storm_load [kN]).
        """
        # C_T = 8/9, Air density = 1.2 kg/m^3
        aerodynamical_load = 0.5 * 1.2 * (8.0 / 9.0) * turbine.swept_area * rated_wind_speed**2 / 1000.0
        storm_load = 0.5 * 1.2 * 1.5 * turbine.solidity * turbine.swept_area * survival_gust**2 / 1000.0
        return aerodynamical_load, storm_load



    @staticmethod
    def buckeling(turbine: WindTurbine, max_load: float, rna_mass: float) -> float:
        E = 210000e6          # [Pa] Young's modulus for steel
        steel_density = 7850  # [kg/m³] Structural steel density
        g = 9.82              # [m/s²] Gravitational acceleratio
        steps = 100 # Devide WECs height into parts to calculate at different heights
        z_levels = np.linspace(0, turbine.height, steps)
        wall_thickness = turbine.wall_thickness

        R_base = turbine.bottom_diameter / 2
        R_top = turbine.top_diameter / 2
        R_z = R_base - ((R_base - R_top) / turbine.height) * z_levels

        moment_z = max_load * (turbine.height - z_levels) # [kNm]
        I_z = np.pi/4 * (R_z**4 - (R_z - wall_thickness)**4) # [m]

        # 2. CROSS-SECTIONAL PROPERTIES [cite: 81, 84]
        area = np.pi * (R_z**2 - (R_z - wall_thickness)**2)        # [m²] Steel cross-sectional area
        w_z = I_z/R_z # [m³] Section modulus (thin-walled approximation)
        
        # 3. GRAVITY / SELF-WEIGHT INTEGRATION
        segment_length = turbine.height / (steps - 1)
        section_volume = area * segment_length  # [m³] Volume per segment
        tower_mass_above = np.flip(np.cumsum(np.flip(section_volume))) * steel_density  # [kg] Cumulative tower mass from top down
        
        # 4. APPLIED LOADS [cite: 81]
        vertical_load_z = (rna_mass + tower_mass_above) * g          # [N] Total vertical force at height z
        
        # 5. ACTUAL STRESSES 
        sigma_c = vertical_load_z / area   # [Pa] Axial compressive stress from weight
        sigma_b = 1000*moment_z / w_z           # [Pa] Bending compressive stress from wind
        
        # 6. NASA SP-8007 IMPERFECTION REDUCTION [cite: 198, 250]
        phi = (1.0 / 16.0) * np.sqrt(R_z / wall_thickness)                  # [-] Slankhetsparameter (dimensionless) 
        gamma_c = 1.0 - 0.901 * (1.0 - np.exp(-phi))         # [-] Correlation factor for axial compression [cite: 198]
        gamma_b = 1.0 - 0.731 * (1.0 - np.exp(-phi))         # [-] Correlation factor for bending [cite: 250]
        
        # 7. CRITICAL BUCKLING STRESSES (Capacity) [cite: 160, 247]
        sigma_cr_c = 0.6 * gamma_c * E * (wall_thickness / R_z)    # [Pa] Allowable axial stress 
        sigma_cr_b = 0.6 * gamma_b * E * (wall_thickness / R_z)    # [Pa] Allowable bending stress 
        
        # 8. INTERACTION CHECK (Rc + Rb <= 1.0) [cite: 438]
        R_c = sigma_c / sigma_cr_c         # [-] Stress ratio for compression 
        R_b = sigma_b / sigma_cr_b         # [-] Stress ratio for bending 
        interaction = R_c + R_b            # [-] Total buckling interaction [cite: 438]
        
        # Find critical location
        max_interaction = np.max(interaction)
        
        return float(max_interaction)

        

    @staticmethod
    def breaking(turbine: WindTurbine, max_load: float) -> float:
        break_stress = 235e6 # [Pa] For steel
        steps = 100
        z_levels = np.linspace(0, turbine.height, steps)
        wall_thickness = turbine.wall_thickness

        R_base = turbine.bottom_diameter / 2.0
        R_top = turbine.top_diameter / 2.0
        R_z = R_base - ((R_base - R_top) / turbine.height) * z_levels

        moment_z = max_load * (turbine.height - z_levels) # [kNm]
        
        # Moment of inertia
        I_z = np.pi/4 * (R_z**4 - (R_z - wall_thickness)**4)
        max_stress = np.max((1000 * moment_z * R_z) / I_z)
        breaking_utilization = max_stress / break_stress # value < 1 => breaks
        return float(breaking_utilization)

    @staticmethod
    def calculate_rna_mass(turbine: WindTurbine, rated_power: float) -> float:
        """
        Estimates the Rotor Nacelle Assembly (RNA) mass using empirical scaling.
        
        Args:
            turbine: Wind turbine configuration.
            rated_power: Rated power [kW].
            
        Returns:
            RNA mass [kg].
        """
        # 1. Rotor Mass (Blades + Hub)
        # NREL empirical scaling: ~0.13 * D^2.4
        # We use a slightly higher coefficient (~0.5) so a 130m rotor is roughly 60 tons.
        rotor_mass = 0.5 * (turbine.rotor_diameter ** 2.4)
        
        # 2. Nacelle Mass
        # Base mass of 45 kg per kW of rated power, scaled by the drivetrain modifier
        base_nacelle_mass = 45.0 * rated_power
        actual_nacelle_mass = base_nacelle_mass * turbine.nacelle_mass_modifier
        return float(rotor_mass + actual_nacelle_mass)

    @staticmethod
    def evaluate_integrity(turbine: WindTurbine, climate: WindClimate, env: SiteEnvironment, rated_power: float) -> StructuralReport:
        aerodynamical_load, storm_load = StructuralService.calculate_loads(turbine, climate.rated_wind_speed, env.survival_gust)
        max_load = max(aerodynamical_load, storm_load)
        
        breaking_utilization = StructuralService.breaking(turbine, max_load)
        rna_mass = StructuralService.calculate_rna_mass(turbine, rated_power)
        buckeling_utilization = StructuralService.buckeling(turbine, max_load, rna_mass)
        
        return StructuralReport(
            aerodynamical_load=aerodynamical_load,
            storm_load=storm_load,
            slenderness_ratio=turbine.slenderness_ratio,
            breaking_utilization=breaking_utilization,
            buckeling_utilization=buckeling_utilization,
            rna_mass=rna_mass
        )


class FinancialService:
    @staticmethod
    def calculate_capex(env: SiteEnvironment, turbine: WindTurbine, rated_power: float) -> tuple[float, dict[str, float]]:
        """
        Calculate total capital expenditure (CAPEX) for the turbine park.
        
        Args:
            env: Site environment with installation and financial variables.
            turbine: Turbine geometry and modifiers.
            rated_power_kw: Total rated power of a single turbine [kW].
            
        Returns:
            total_capex [k€] and a tuple of its components:
            (turbine_costs, drivetrain_nacelle, tower, foundation_site) [k€].
        """


        # Sätt offshore-faktorer
        if env.is_offshore:
            mar_factor = 1.15       # Marinised turbine
            found_factor = 2.5      # significantly more costly fundament in water
            install_factor = 3.0    # More expensive: ships and logistics 
        else:
            mar_factor = 1.0
            found_factor = 1.0
            install_factor = 1.0

        devex = 200+50*(rated_power/1000) # permits for setting up base and building

        # Applicera marinisering på själva verket
        rotor_cost = 900.0 * (turbine.rotor_diameter / 90.0) ** 3 * mar_factor
        drivetrain_nacelle = 800.0 * (rated_power / 3.0) * turbine.drivetrain_modifier * mar_factor
        tower = 700.0 * ((turbine.height/ 90.0) * (turbine.rotor_diameter/ 90.0) ** 2) * turbine.nacelle_mass_modifier * mar_factor
        
        # Applicera fundament-faktor
        foundation_site = (300.0 * ((turbine.height/ 90.0) * (turbine.rotor_diameter / 90.0) ** 2)) * found_factor
        
        # Applicera installations-faktor
        installation = env.installation_costs * install_factor

        total_capex = devex + rotor_cost + drivetrain_nacelle + tower + foundation_site + env.installation_costs
        
        components = {
            "devex": devex,
            "rotor": rotor_cost,
            "drivetrain": drivetrain_nacelle,
            "tower": tower,
            "foundation": foundation_site,
            "installation": env.installation_costs
        }
        
        return total_capex, components

    @staticmethod
    def calculate_opex(env: SiteEnvironment, turbine: WindTurbine, rated_power_kw: float) -> float:
        total_power_mw = (rated_power_kw / 1000.0) * env.turbine_count
        maintenance = 600.0 * (total_power_mw / 20.0) * turbine.opex_modifier
        insurance = 100.0 * (total_power_mw / 20.0) ** 0.5
        land_cost = 360.0 * env.turbine_count / 20.0
        fund_decommissioning = 200.0 * total_power_mw / 20.0
        
        return float(maintenance + insurance + land_cost + fund_decommissioning)

    @staticmethod
    def calculate_annual_earnings(env: SiteEnvironment, generated_energy: float, annual_opex: float) -> tuple[float, float]:
        annual_revenue = generated_energy * env.turbine_count * (env.electricity_price + env.green_certificate) / 1000.0
        annual_savings = annual_revenue - annual_opex
        return annual_savings, annual_revenue

    @staticmethod
    def calculate_profits(env: SiteEnvironment, total_capex: float, annual_savings: float, lifetime_years: int) -> tuple[float, float]:
        financial_costs = env.financial_additional_part * total_capex
        k_factor = (1.0 + env.inflation) / (1.0 + env.interest)
        
        if abs(k_factor - 1.0) > 1e-6:
            net_present_value = (
                annual_savings * (k_factor * (1.0 - k_factor**lifetime_years)) / (1.0 - k_factor)
            )
        else:
            net_present_value = annual_savings * lifetime_years
            
        profits = net_present_value - total_capex - financial_costs
        margin = profits / total_capex if total_capex > 0 else 0.0
        return profits, margin

    @staticmethod
    def calculate_irr(total_capex: float, annual_savings: float, years: int) -> float:
        if annual_savings <= 0 or total_capex <= 0:
            return 0.0
        try:
            cash_flows = np.insert(np.full(years, annual_savings), 0, -total_capex)
            npv_fn = lambda r: np.sum(cash_flows / (1.0 + r) ** np.arange(len(cash_flows)))
            
            a, b = -0.99, 5.0
            if npv_fn(a) * npv_fn(b) < 0:
                sol = root_scalar(npv_fn, bracket=[a, b], method='brentq')
                return float(sol.root)
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def evaluate_finance(env: SiteEnvironment, turbine: WindTurbine, rated_power_kw: float, generated_energy_mwh: float) -> FinancialReport:
        total_capex, capex_components = FinancialService.calculate_capex(env, turbine, rated_power_kw)
        annual_opex = FinancialService.calculate_opex(env, turbine, rated_power_kw)
        annual_savings, annual_revenue = FinancialService.calculate_annual_earnings(env, generated_energy_mwh, annual_opex)
        profits, margin = FinancialService.calculate_profits(env, total_capex, annual_savings, turbine.lifetime)
        irr = FinancialService.calculate_irr(total_capex, annual_savings, turbine.lifetime)
        payback_years = total_capex / annual_savings if annual_savings > 0 else float('inf')
        
        return FinancialReport(
            capex_components=capex_components,
            total_capex=total_capex,
            annual_opex=annual_opex,
            annual_revenue=annual_revenue,
            npv_profit=profits,
            IRR=irr,
            margin=margin,
            payback_years=payback_years
        )


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
    slenderness_ratio: float # [-]
    breaking_utilization: float # [-]
    buckeling_utilization: float # [-]
    rna_mass: float # [kg]

    # Ekonomi
    capex_components: dict[str,float] # Dict representing costs for devex, rotor, drivetrain, tower, foundation, installation [k€]
    total_capex: float  # k€
    annual_opex: float  # k€/år
    annual_revenue: float  # k€/år
    npv_profit: float  # k€
    IRR: float # [%]
    margin: float  # [%]
    payback_years: float # [y]


def simulate(turbine: WindTurbine, env: SiteEnvironment) -> SimulationResult:
    # 1. Wind climate calculations
    climate = ClimateService.calculate_wind_climate(env, turbine)
    
    # 2. Energy production (single turbine)
    generated_energy, rated_power, capacity_factor= EnergyService.calculate_production(turbine, climate)
    
    # 3. Structural evaluation (single turbine geometry)
    structural_report = StructuralService.evaluate_integrity(turbine, climate, env, rated_power)
    
    # 4. Financial evaluation (for the park)
    financial_report = FinancialService.evaluate_finance(env, turbine, rated_power, generated_energy)
    
    # 5. capacity factor calculation

    print(f"Profits: {financial_report.npv_profit} k€, Margin: {financial_report.margin*100}%")

    return SimulationResult(
        wind_nacelle=climate.wind_nacelle,
        weibull_C=climate.weibull_C,
        weibull_k=climate.weibull_k,
        rated_wind_speed=climate.rated_wind_speed,
        cut_in_speed=climate.cut_in_speed,
        cut_out_speed=climate.cut_out_speed,
        rated_power=rated_power * env.turbine_count,
        generated_energy=generated_energy * env.turbine_count,
        capacity_factor=capacity_factor,
        aerodynamical_load=structural_report.aerodynamical_load,
        storm_load=structural_report.storm_load,
        slenderness_ratio=structural_report.slenderness_ratio,
        breaking_utilization=structural_report.breaking_utilization,
        buckeling_utilization=structural_report.buckeling_utilization,
        rna_mass=structural_report.rna_mass,
        capex_components=financial_report.capex_components,
        total_capex=financial_report.total_capex,
        annual_opex=financial_report.annual_opex,
        annual_revenue=financial_report.annual_revenue,
        npv_profit=financial_report.npv_profit,
        IRR=financial_report.IRR,
        margin=financial_report.margin,
        payback_years=financial_report.payback_years
    )


class SimulationEngine:
    @staticmethod
    def simulate(turbine: WindTurbine, env: SiteEnvironment) -> SimulationResult:
        return simulate(turbine, env)


if __name__ == "__main__":
    test_case = 1
    match test_case:
        case 0:
            env = SiteEnvironment(
                avg_wind_10 = 7.0,
                roughness = 0.2,
                survival_gust = 60,
                k_factor = 2.0,
                is_offshore = False,
                turbine_count = 1,
                electricity_price = 29,
                green_certificate = 1.0,
                financial_additional_part = 0.07,
            )
            SSNGenerator.apply_ssn_to_env("200301019949", env)
            turbine = WindTurbine(rotor_diameter=81, height=97, solidity=0.03, blades = 3,  gearbox= Gearbox.NONE, generator=Generator.DFIG, lifetime=22)
            print(env)
            print(turbine)
            print('\n', SimulationEngine.simulate(turbine, env))
        case 1:
            env = SiteEnvironment(
                avg_wind_10 = 7.0,
                roughness = 0.10,
                survival_gust = 60.0,
                k_factor = 2.0,
                is_offshore = False,
                turbine_count = 1,
                electricity_price = 40.0,
                green_certificate = 2.0,
                financial_additional_part = 0.07,
            )
            turbine = WindTurbine(rotor_diameter=131, height=120, solidity=0.04, blades = 3,  gearbox= Gearbox.MEDIUM_SPEED, generator=Generator.SYNCHRONOUS)
        case 2:
            env = SiteEnvironment(
                avg_wind_10=7.0,
                roughness=0.1,
                survival_gust=59.5,
                

            )
            turbine = 2

    
    print(env)
    print(turbine)
    print('\n', SimulationEngine.simulate(turbine, env))