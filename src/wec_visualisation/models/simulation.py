# models/simulation.py
from dataclasses import dataclass
import numpy as np
from scipy.special import gamma
from scipy.optimize import root_scalar

from wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator
from wec_visualisation.models.environment import SiteEnvironment, SSNGenerator
import wec_visualisation.config as config
from enum import Enum

@dataclass 
class SimulationConfiguration:
    """Configuration parameters for the simulation (E.G. linear scaling parameter for devex)"""

    ### WIND PARAMETERS
    rated_wind_base: float = 12.0 # rated wind with no interferance of nacelle_wind
    rated_wind_nacelle_scaler: float = 0.15 # scaler that reduces the rated wind speed with respect to the nacelle_wind
    cut_in_power_fraction: float = 0.01  # Turbine starts producing when wind power is 1% of rated power
    cut_out_energy_fraction: float = 0.8  # Turn off when 80% of total energy is reached in the distribution

    ### RNA MASS
    # Exponents for nacelle-mass based on drivetrain 
    exp_power_dd: float = 1.4         # Direct Drive
    exp_power_geared: float = 1.05    # Geared (High/Medium speed)
    
    # Exponents for mass of rotor
    exp_diameter_large: float = 2.2   # Offshore / Large onshore
    exp_diameter_small: float = 2.4   # Small onshore
    
    # Scaling factors for rotor 
    rotor_scale_blade: float = 0.77
    rotor_scale_hub: float = 0.51
    rotor_scale_small: float = 1.0
    
    # Offshore-specific mass_factors
    offshore_hub_mass_factor: float = 1.2
    offshore_nacelle_mass_factor: float = 1.2
    
    # Nacelle kw => mass scalar
    nacelle_mass_per_kw: float = 45.0
    
    # Threshold value, for larger WEC:s 
    large_rotor_threshold: float = 125.0
    
    ### CAPEX
    # offshore scalers
    marine_offshore_scale: float = 1.15 # Nacelle, rotor, tower
    foundation_offshore_scale:float = 2.5 # Foundation 
    installation_offshore_factor:float = 3.0 # Installation costs

    # Devex
    base_devex:float=200.0
    scale_power_devex:float = 50.0

    # cost base values [k€]
    rotor_base:float = 900.0
    rotor_exp: float = 2.3
    drivetrain_nacelle_base:float = 800.0
    tower_base:float = 700.0
    foundation_base:float = 300.0
    installation_base: float = 3500.0

    ### Opex [k€]
    base_maintenance: float = 600.0
    base_insurance: float = 100.0
    base_land: float = 360.0
    base_decommissioning:float=200.0
    opex_scaler: float = 1.0

    ### Structural
    storm_drag_coefficient: float = 0.766 # Previously 1.5
    buckling_safety_factor: float = 2.429 # Previously 1.0


class PresetConfigurations(Enum):
    """Different tested values for SimulationConfiguration"""
    v0 = SimulationConfiguration( # Unprocessed scalars
        rated_wind_base=12.0,
        rated_wind_nacelle_scaler=0.15,
        cut_in_power_fraction=0.01,
        cut_out_energy_fraction=0.8,
        exp_power_dd=1.4,
        exp_power_geared=1.05,
        exp_diameter_large=2.2,
        exp_diameter_small=2.4,
        rotor_scale_blade=0.77,
        rotor_scale_hub=0.51,
        rotor_scale_small=1.0,
        offshore_hub_mass_factor=1.2,
        offshore_nacelle_mass_factor=1.2,
        nacelle_mass_per_kw=45.0,
        large_rotor_threshold=125.0,
        marine_offshore_scale=1.15,
        foundation_offshore_scale=2.5,
        installation_offshore_factor=3.0,
        base_devex=200.0,
        scale_power_devex=50.0,
        rotor_base=900.0,
        rotor_exp=2.3,
        drivetrain_nacelle_base=800.0,
        tower_base=700.0,
        foundation_base=300.0,
        installation_base=3500.0,
        base_maintenance=600.0,
        base_insurance=100.0,
        base_land=360.0,
        base_decommissioning=200.0,
        opex_scaler=1.0,
        storm_drag_coefficient=0.766,
        buckling_safety_factor=2.429
    )
    v1 = SimulationConfiguration( # Processed with calibrate.py with 3MW_Onshore, NREL_5MW_Onshore, 8MW_Offshore, DTU_10MW_Offshore, IEA_15MW_Offshore
        rotor_base=479.633,
        rotor_exp=2.573,
        drivetrain_nacelle_base=1419.201,
        tower_base=81.198,
        foundation_base=390.009,
        installation_base=827.587,
        installation_offshore_factor=2.410,
        base_maintenance=25982.913,
        base_insurance=50.000,
        base_land=12836.031,
        base_decommissioning=10718.847,
        opex_scaler=0.100,
        exp_power_dd=1.000,
        exp_power_geared=2.500,
        exp_diameter_large=2.251,
        exp_diameter_small=2.473,
        rotor_scale_blade=5.000,
        rotor_scale_hub=0.101,
        rotor_scale_small=1.111,
        nacelle_mass_per_kw=149.989,
        cut_in_power_fraction=0.010,
        cut_out_energy_fraction=0.702,
        rated_wind_base=10.566,
        rated_wind_nacelle_scaler=0.000,
        storm_drag_coefficient=0.848,
        buckling_safety_factor=2.207
    )


@dataclass(frozen=True)
class StructuralReport:
    """Results of structural calculations"""
    aerodynamical_load: float  # kN
    storm_load: float          # kN
    slenderness_ratio: float   # [-]
    breaking_utilization: float         # [-] Breaking factor
    buckling_utilization: float         # [-] Buckling factor
    rna_mass: float            # [kg] Rotor Nacelle Assembly mass

@dataclass(frozen=True)
class FinancialReport:
    """Results of financial calculations"""
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

    config: SimulationConfiguration

    @property
    def energy_density_per_m2(self) -> np.ndarray:
        """Energy per meter squared at blades"""
        return config.WIND_DENSITY_COEFFICIENT * self.wind_speeds**3 * self.possible_hours / 1000.0

    @property
    def total_potential_energy(self) -> float:
        return float(np.sum(self.energy_density_per_m2))

    @property
    def rated_wind_speed(self) -> float:
        return self.config.rated_wind_base - self.config.rated_wind_nacelle_scaler * self.wind_nacelle

    @property
    def cut_in_speed(self) -> float:
        # P ~ V^3. We cut in when available power is a specific fraction of rated power.
        fraction_root = self.config.cut_in_power_fraction ** (1.0 / 3.0)
        return self.rated_wind_speed * fraction_root

    @property
    def cut_out_speed(self) -> float:
        cumulated_energy = np.cumsum(self.energy_density_per_m2)
        turn_off_limit = self.config.cut_out_energy_fraction * self.total_potential_energy
        capped_mask = cumulated_energy > turn_off_limit
        idx = np.argmax(capped_mask)
        return float(self.wind_speeds[idx])


class ClimateService:
    @staticmethod
    def calculate_wind_climate(env: SiteEnvironment, turbine: WindTurbine, config: SimulationConfiguration) -> WindClimate:
        """
        Calculate the wind climate characteristics at the turbine's nacelle height.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment containing surface roughness and average wind data.
        turbine : WindTurbine
            Wind turbine configuration.
        config : SimulationConfiguration
            Simulation configuration.
            
        Returns
        -------
        WindClimate
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
            possible_hours=possible_hours,
            config=config
        )



class EnergyService:
    @staticmethod
    def calculate_production(turbine: WindTurbine, climate: WindClimate) -> tuple:
        """
        Compute the annual energy production for a given turbine and wind climate.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration including swept area and efficiencies.
        climate : WindClimate
            WindClimate containing distribution of available hours and speeds.
            
        Returns
        -------
        tuple
            A tuple containing:
            - generated_energy : float
                Total annual generated energy [MWh].
            - rated_power : float
                Rated power [kW].
            - capacity_factor : float
                Capacity factor ratio [-].
        """
        rated_speed = climate.rated_wind_speed
        cut_in = climate.cut_in_speed
        cut_out = climate.cut_out_speed
        
        rated_power = config.WIND_DENSITY_COEFFICIENT * rated_speed**3 * turbine.swept_area / 1000.0 * turbine.capture_efficiency * turbine.drivetrain_efficiency
        
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
    def calculate_loads(turbine: WindTurbine, rated_wind_speed: float, survival_gust: float, sim_config: SimulationConfiguration) -> tuple[float, float]:
        """
        Calculate the structural loads acting on the turbine tower.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration.
        rated_wind_speed : float
            Rated wind speed [m/s] for calculating aerodynamic load.
        survival_gust : float
            Storm survival gust [m/s] for calculating storm load.
        sim_config : SimulationConfiguration
            Simulation configuration.
            
        Returns
        -------
        tuple
            A tuple containing:
            - aerodynamical_load : float
                Aerodynamic load on the tower [kN].
            - storm_load : float
                Storm load on the tower [kN].
        """
        aerodynamical_load = 0.5 * config.AIR_DENSITY * config.C_T * turbine.swept_area * rated_wind_speed**2 / 1000.0
        storm_load = 0.5 * config.AIR_DENSITY * sim_config.storm_drag_coefficient * turbine.solidity * turbine.swept_area * survival_gust**2 / 1000.0
        return aerodynamical_load, storm_load



    @staticmethod
    def buckling(turbine: WindTurbine, max_load: float, rna_mass: float, sim_config: SimulationConfiguration) -> float:
        """
        Calculate the buckling utilization factor based on maximum load and mass.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration.
        max_load : float
            Maximum structural load acting on the tower [kN].
        rna_mass : float
            Rotor Nacelle Assembly mass [kg].
        sim_config : SimulationConfiguration
            Simulation configuration.
            
        Returns
        -------
        float
            Buckling utilization factor. Values > 1.0 indicate structural failure.
        """
        E = config.YOUNGS_MODULUS_STEEL
        steel_density = config.STEEL_DENSITY
        g = config.GRAVITY
        steps = 100 # Divide WECs height into parts to calculate at different heights
        z_levels = np.linspace(0, turbine.height, steps) # height points from bottom to top
        wall_thickness = turbine.wall_thickness

        R_base = turbine.bottom_diameter / 2
        R_top = turbine.top_diameter / 2
        R_z = R_base - ((R_base - R_top) / turbine.height) * z_levels

        moment_z = max_load * (turbine.height - z_levels) # [kNm]
        I_z = np.pi/4 * (R_z**4 - (R_z - wall_thickness)**4) # [m]

        # 2. CROSS-SECTIONAL PROPERTIES [cite: 81, 84]
        area_z = np.pi * (R_z**2 - (R_z - wall_thickness)**2)        # [m²] Steel cross-sectional area
        w_z = I_z/R_z # [m³] Section modulus (thin-walled approximation)
        
        # 3. GRAVITY / SELF-WEIGHT INTEGRATION
        segment_length = turbine.height / (steps - 1)
        section_volume = area_z * segment_length  # [m³] Volume per segment
        tower_mass_above = np.flip(np.cumsum(np.flip(section_volume))) * steel_density  # [kg] Cumulative tower mass from top down
        
        # 4. APPLIED LOADS [cite: 81]
        vertical_load_z = (rna_mass + tower_mass_above) * g          # [N] Total vertical force at height z
        
        # 5. ACTUAL STRESSES 
        sigma_c = vertical_load_z / area_z   # [Pa] Axial compressive stress from weight
        sigma_b = 1000*moment_z / w_z           # [Pa] Bending compressive stress from wind
        
        # 6. NASA SP-8007 IMPERFECTION REDUCTION [cite: 198, 250]
        phi = (1.0 / 16.0) * np.sqrt(R_z / wall_thickness)                  # [-] Slenderness parameter (dimensionless) 
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
        
        return float(max_interaction * sim_config.buckling_safety_factor)

        

    @staticmethod
    def breaking(turbine: WindTurbine, max_load: float) -> float:
        """
        Calculate the breaking utilization factor based on maximum load.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration.
        max_load : float
            Maximum structural load acting on the tower [kN].
            
        Returns
        -------
        float
            Breaking utilization factor. Values > 1.0 indicate structural failure.
        """
        break_stress = config.STEEL_YIELD_STRESS
        steps = 100
        z_levels = np.linspace(0, turbine.height, steps)
        wall_thickness = turbine.wall_thickness

        R_base = turbine.bottom_diameter / 2
        R_top = turbine.top_diameter / 2
        R_z = R_base - ((R_base - R_top) / turbine.height) * z_levels

        moment_z = max_load * (turbine.height - z_levels) # [kNm]
        
        # Moment of inertia
        I_z = np.pi/4 * (R_z**4 - (R_z - wall_thickness)**4)
        max_stress = np.max((1000 * moment_z * R_z) / I_z)
        breaking_utilization = max_stress / break_stress # value > 1 => breaks
        return float(breaking_utilization)

    @staticmethod
    def calculate_rna_mass(turbine: WindTurbine, env:SiteEnvironment, sim_config:SimulationConfiguration, rated_power: float) -> float:
        """
        Estimates the Rotor Nacelle Assembly (RNA) mass using empirical scaling.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration.
        env : SiteEnvironment
            Site environment configuration.
        sim_config : SimulationConfiguration
            Simulation configuration.
        rated_power : float
            Rated power [kW].
            
        Returns
        -------
        float
            RNA mass [kg].
        """

        # exponant for nacelle power scaling
        exp_power = sim_config.exp_power_dd if turbine.gearbox == Gearbox.NONE else sim_config.exp_power_geared

        nacelle_scale = 1 # when not offshore
        if env.is_offshore: # Offshore turbines
            exp_diameter = sim_config.exp_diameter_large
            rotor_scale = sim_config.rotor_scale_blade+sim_config.rotor_scale_hub*sim_config.offshore_hub_mass_factor # 1.2 extra mass for offshore hub
            nacelle_scale = sim_config.offshore_nacelle_mass_factor # extra mass for offshore nacelle
        elif turbine.rotor_diameter > sim_config.large_rotor_threshold: # Larger onshore turbines
            exp_diameter = sim_config.exp_diameter_large
            rotor_scale = sim_config.rotor_scale_blade+sim_config.rotor_scale_hub
        else: # Smaller onshore turbines
            exp_diameter = sim_config.exp_diameter_small
            rotor_scale = sim_config.rotor_scale_small

        # 1. Rotor Mass (Blades + Hub)
        # NREL empirical scaling: ~0.13 * D^2.4
        # We use a slightly higher coefficient (~0.5) so a 130m rotor is roughly 60 tons.
        rotor_mass = rotor_scale * (turbine.rotor_diameter ** exp_diameter)
        
        # 2. Nacelle Mass
        # Base mass of 45 kg per kW of rated power, scaled by the drivetrain modifier
        mass_per_kw = sim_config.nacelle_mass_per_kw
        nacelle_mass = mass_per_kw*nacelle_scale*turbine.nacelle_mass_modifier* (rated_power/1000)**exp_power
        return float(rotor_mass + nacelle_mass)

    @staticmethod
    def evaluate_integrity(turbine: WindTurbine, env: SiteEnvironment,sim_config:SimulationConfiguration, climate:WindClimate, rated_power: float) -> StructuralReport:
        """
        Evaluate the structural integrity of the turbine tower and compute loads.
        
        Parameters
        ----------
        turbine : WindTurbine
            Wind turbine configuration.
        env : SiteEnvironment
            Site environment configuration.
        sim_config : SimulationConfiguration
            Simulation configuration.
        climate : WindClimate
            Wind climate configuration.
        rated_power : float
            Rated power [kW].
            
        Returns
        -------
        StructuralReport
            Report object containing load calculations and utilization factors.
        """
        aerodynamical_load, storm_load = StructuralService.calculate_loads(turbine, climate.rated_wind_speed, env.survival_gust, sim_config)
        max_load = max(aerodynamical_load, storm_load)
        
        breaking_utilization = StructuralService.breaking(turbine, max_load)
        rna_mass = StructuralService.calculate_rna_mass(turbine,env,sim_config, rated_power)
        buckling_utilization = StructuralService.buckling(turbine, max_load, rna_mass, sim_config)
        
        return StructuralReport(
            aerodynamical_load=aerodynamical_load,
            storm_load=storm_load,
            slenderness_ratio=turbine.slenderness_ratio,
            breaking_utilization=breaking_utilization,
            buckling_utilization=buckling_utilization,
            rna_mass=rna_mass
        )


class FinancialService:
    @staticmethod
    def calculate_capex(env: SiteEnvironment, turbine: WindTurbine,sim_config:SimulationConfiguration, rated_power: float) -> tuple[float, dict[str, float]]:
        """
        Calculate total capital expenditure (CAPEX) for the turbine park.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment with installation and financial variables.
        turbine : WindTurbine
            Turbine geometry and modifiers.
        sim_config : SimulationConfiguration
            Simulation configuration.
        rated_power : float
            Total rated power of a single turbine [kW].
            
        Returns
        -------
        tuple
            A tuple containing:
            - total_capex : float
                Total capital expenditure [k€].
            - components : dict[str, float]
                Dictionary of individual CAPEX components [k€].
        """

        marine_factor = 1.0
        foundation_factor = 1.0
        install_factor = 1.0

        # Set offshore factors
        if env.is_offshore:
            # config
            marine_factor = sim_config.marine_offshore_scale
            foundation_factor = sim_config.foundation_offshore_scale
            install_factor = sim_config.installation_offshore_factor

        devex = sim_config.base_devex+sim_config.scale_power_devex*(rated_power/1000) # permits for setting up base and building

        rotor_cost = sim_config.rotor_base* (turbine.rotor_diameter / 90.0) ** (sim_config.rotor_exp) * marine_factor
        drivetrain_nacelle = sim_config.drivetrain_nacelle_base * (rated_power / 3000.0) * turbine.drivetrain_cost_modifier * marine_factor
        tower = sim_config.tower_base* (turbine.height*turbine.wall_thickness*turbine.bottom_diameter) * turbine.nacelle_mass_modifier * marine_factor # includes height, thickness, bottom diameter with volume 
        
        foundation_site = (sim_config.foundation_base * ((turbine.height/ 90.0) * (turbine.rotor_diameter / 90.0) ** 2)) * foundation_factor
        
        installation = sim_config.installation_base* install_factor* (rated_power/3000) 

        total_capex = devex + rotor_cost + drivetrain_nacelle + tower + foundation_site + installation
        
        components = {
            "devex": devex,
            "rotor": rotor_cost,
            "drivetrain": drivetrain_nacelle,
            "tower": tower,
            "foundation": foundation_site,
            "installation": installation
        }
        
        return total_capex, components

    @staticmethod
    def calculate_opex(env: SiteEnvironment, turbine: WindTurbine,sim_config:SimulationConfiguration, rated_power: float) -> float:
        """
        Calculate total operational expenditure (OPEX) for the turbine park.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment configuration.
        turbine : WindTurbine
            Turbine configuration.
        sim_config : SimulationConfiguration
            Simulation configuration.
        rated_power : float
            Total rated power of a single turbine [kW].
            
        Returns
        -------
        float
            Total OPEX [k€].
        """
        total_power_mw = (rated_power / 1000.0) * env.turbine_count
        maintenance =  sim_config.base_maintenance* (total_power_mw / 20.0) * turbine.opex_modifier
        insurance = sim_config.base_insurance* (total_power_mw / 20.0) ** 0.5
        land_cost = sim_config.base_land* env.turbine_count / 20.0
        fund_decommissioning = sim_config.base_decommissioning* total_power_mw / 20.0
        total_opex = float(maintenance + insurance + land_cost + fund_decommissioning)
        return total_opex*(total_power_mw/20)**0.8*sim_config.opex_scaler

    @staticmethod
    def calculate_annual_earnings(env: SiteEnvironment, generated_energy: float, annual_opex: float) -> tuple[float, float]:
        """
        Calculate annual earnings for the turbine park.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment configuration.
        generated_energy : float
            Generated energy from the park [MWh].
        annual_opex : float
            Total annual operational expenditure [k€].
            
        Returns
        -------
        tuple
            A tuple containing:
            - annual_savings : float
                Net annual savings [k€].
            - annual_revenue : float
                Total annual revenue [k€].
        """
        annual_revenue = generated_energy * env.turbine_count * (env.electricity_price + env.green_certificate) / 1000.0
        annual_savings = annual_revenue - annual_opex
        return annual_savings, annual_revenue

    @staticmethod
    def calculate_profits(env: SiteEnvironment, total_capex: float, annual_savings: float, lifetime_years: int) -> tuple[float, float]:
        """
        Calculate the total lifetime profit and margin for the park.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment configuration.
        total_capex : float
            Total capital expenditure [k€].
        annual_savings : float
            Net annual savings [k€].
        lifetime_years : int
            Turbine lifetime in years.
            
        Returns
        -------
        tuple
            A tuple containing:
            - profits : float
                Net present value (NPV) profit [k€].
            - margin : float
                Profit margin relative to CAPEX [-].
        """
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
        """
        Calculate the internal rate of return (IRR).
        
        Parameters
        ----------
        total_capex : float
            Total capital expenditure [k€].
        annual_savings : float
            Net annual savings [k€].
        years : int
            Turbine lifetime in years.
            
        Returns
        -------
        float
            Internal rate of return (IRR) [-].
        """
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
    def evaluate_finance(env: SiteEnvironment, turbine: WindTurbine,sim_config:SimulationConfiguration, rated_power_kw: float, generated_energy_mwh: float) -> FinancialReport:
        """
        Evaluate the overall financial performance of the turbine park.
        
        Parameters
        ----------
        env : SiteEnvironment
            Site environment configuration.
        turbine : WindTurbine
            Wind turbine configuration.
        sim_config : SimulationConfiguration
            Simulation configuration.
        rated_power_kw : float
            Total rated power [kW].
        generated_energy_mwh : float
            Total generated energy [MWh].
            
        Returns
        -------
        FinancialReport
            Report object containing financial metrics and calculations.
        """
        total_capex, capex_components = FinancialService.calculate_capex(env, turbine,sim_config, rated_power_kw)
        annual_opex = FinancialService.calculate_opex(env, turbine,sim_config, rated_power_kw)
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
    # Wnd & Power results from Simulation
    wind_nacelle: float # m/s
    weibull_C: float
    weibull_k: float
    rated_wind_speed: float # m/s
    cut_in_speed: float # m/s
    cut_out_speed: float # m/s
    rated_power: float # kW
    generated_energy: float  # MWh/år
    capacity_factor: float  # [%]

    # Forces & Structural Integrity
    aerodynamical_load: float  # kN
    storm_load: float  # kN
    slenderness_ratio: float # [-]
    breaking_utilization: float # [-]
    buckling_utilization: float # [-]
    rna_mass: float # [kg]

    # Economics
    capex_components: dict[str,float] # Dict representing costs for devex, rotor, drivetrain, tower, foundation, installation [k€]
    total_capex: float  # k€
    annual_opex: float  # k€/år
    annual_revenue: float  # k€/år
    npv_profit: float  # k€
    IRR: float # [%]
    margin: float  # [%]
    payback_years: float # [y]

    wind_speeds: np.ndarray
    weibull_probabilities: np.ndarray
    power_curve: np.ndarray

class SimulationEngine:
    @staticmethod
    def simulate(turbine: WindTurbine, env: SiteEnvironment, sim_config: SimulationConfiguration = SimulationConfiguration()) -> SimulationResult:
        """Processes turbine and env data and calculates SimulationResult.
        Calculates wind climate behaviour, energy production, structural integrity and finances.
        
        Parameters
        ----------
        turbine : WindTurbine
            Data about the turbine itself.
        env : SiteEnvironment
            Data about the environment where the turbine is working.
        sim_config : SimulationConfiguration, optional
            Configuration settings for the simulation formulas and constants.
        
        Returns
        -------
        SimulationResult
            An object containing all the calculated metrics for the simulation.
        """
        # 1. Wind climate calculations
        climate = ClimateService.calculate_wind_climate(env, turbine, sim_config)
        
        # 2. Energy production (single turbine)
        generated_energy, rated_power, capacity_factor= EnergyService.calculate_production(turbine, climate)
        
        # 3. Structural evaluation (single turbine geometry)
        structural_report = StructuralService.evaluate_integrity(turbine, env, sim_config,climate, rated_power)
        
        # 4. Financial evaluation (for the park)
        financial_report = FinancialService.evaluate_finance(env, turbine, sim_config, rated_power, generated_energy)
        
        # 5. capacity factor calculation
        
        # 6. Generate curves for plotting
        power_curve = np.zeros_like(climate.wind_speeds, dtype=float)
        cut_in = climate.cut_in_speed
        cut_out = climate.cut_out_speed
        rated_speed = climate.rated_wind_speed
        
        for i, v in enumerate(climate.wind_speeds):
            if v < cut_in:
                power_curve[i] = 0.0
            elif v <= rated_speed:
                power_curve[i] = config.WIND_DENSITY_COEFFICIENT * v**3 * turbine.swept_area / 1000.0 * turbine.capture_efficiency * turbine.drivetrain_efficiency
            elif v <= cut_out:
                power_curve[i] = rated_power
            else:
                power_curve[i] = 0.0
                
        power_curve = power_curve * env.turbine_count
        weibull_probabilities = climate.possible_hours / 8760.0

        return SimulationResult(
            wind_speeds=climate.wind_speeds,
            weibull_probabilities=weibull_probabilities,
            power_curve=power_curve,
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
            buckling_utilization=structural_report.buckling_utilization,
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
            turbine = WindTurbine(rotor_diameter=81, height=97, solidity=0.03,  gearbox= Gearbox.NONE, generator=Generator.DFIG, lifetime=22)
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
            turbine = WindTurbine(rotor_diameter=131, height=120, solidity=0.04,gearbox= Gearbox.MEDIUM_SPEED, generator=Generator.SYNCHRONOUS)

    
    print(env)
    print(turbine)
    print('\n', SimulationEngine.simulate(turbine, env))