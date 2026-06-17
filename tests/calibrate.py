import sys
from pathlib import Path

# Ensure src is in PYTHONPATH so we can run this file directly
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent))

import json
import numpy as np
from typing import Callable, List, Tuple, Dict
from dataclasses import dataclass, replace
from scipy.optimize import least_squares

from wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator
from wec_visualisation.models.environment import SiteEnvironment
from wec_visualisation.models.simulation import SimulationEngine, SimulationConfiguration, SimulationResult

@dataclass
class ReferenceData:
    """Dataclass to hold the ground truth / expected values for calibration."""
    id: str
    rna_mass: float | None = None
    total_capex: float | None = None
    annual_opex: float | None = None
    generated_energy: float | None = None
    breaking_utilization: float | None = None
    buckeling_utilization: float | None = None
    capex_components: dict[str, float] | None = None

class Calibrator:
    """
    A clean, generic calibrator that handles running least_squares to fit SimulationConfiguration 
    parameters against ReferenceData metrics.
    """
    def __init__(self, test_cases: List[Tuple[WindTurbine, SiteEnvironment, ReferenceData]]):
        self.test_cases = test_cases
        self.base_config = SimulationConfiguration()

    def optimize(
        self, 
        name: str, 
        params: Dict[str, float], 
        bounds: Tuple[List[float], List[float]], 
        calc_residuals: Callable[[SimulationResult, ReferenceData], List[float]]
    ) -> Dict[str, float]:
        """
        Runs the least squares optimization cleanly without param_mappers or getattr.
        
        Args:
            name: Name of calibration run.
            params: Dictionary of configuration variable names -> their initial guesses.
            bounds: A tuple of ([lower_bounds], [upper_bounds]).
            calc_residuals: Function taking (SimulationResult, ReferenceData) and returning a list of residual errors.
        """
        print("\n" + "="*50)
        print(f"--- Running {name} Calibration ---")

        param_keys = list(params.keys())
        initial_guess = np.array(list(params.values()))

        def objective(params_array: np.ndarray) -> np.ndarray:
            """Objective function for the least squares optimization."""
            # Map the current array back into a dictionary
            updated_params = dict(zip(param_keys, params_array))
            
            # Dynamically replace variables in the base configuration
            current_config = replace(self.base_config, **updated_params)
            
            all_residuals = []
            for turbine, env, ref in self.test_cases:
                # Run the simulation
                res = SimulationEngine.simulate(turbine, env, config=current_config)
                
                # Execute the custom residual function
                errors = calc_residuals(res, ref)
                all_residuals.extend(errors)
                        
            return np.array(all_residuals)

        # Evaluate initial state
        initial_residuals = objective(initial_guess)
        initial_cost = 0.5 * np.sum(initial_residuals**2)
        print(f"BEFORE: Initial Cost (Sum of squared errors): {initial_cost:.6f}")
        
        # Run optimization
        result = least_squares(objective, x0=initial_guess, bounds=bounds)
        
        # Evaluate final state
        print(f"AFTER: Final Cost: {result.cost:.6f} (Reduced by {initial_cost - result.cost:.6f})")
        print(f"Success: {result.success}")
        
        # Format the result nicely back into a dictionary
        optimized_dict = dict(zip(param_keys, result.x))
        print("\nOptimized Parameters:")
        for k, v in optimized_dict.items():
            print(f"  {k}: {v:.3f} (started at {params[k]})")
            
        return optimized_dict


# ==========================================
# 1. FINANCE CALIBRATION
# ==========================================
def calibrate_finance(calibrator: Calibrator):
    
    params = {
        "rotor_base": 900.0,
        "drivetrain_nacelle_base": 800.0,
        "tower_base": 700.0,
        "foundation_base": 300.0,
        "installation_base": 3500.0,
        "installation_offshore_factor": 3.0,
        "base_maintanance": 600.0,
        "base_insurance": 100.0,
        "base_land": 360.0,
        "base_decommisioning": 200.0
    }
    bounds = ([0.0]*10, [np.inf]*10)
    
    # Custom, readable function for errors
    def calc_residuals(res: SimulationResult, ref: ReferenceData) -> List[float]:
        err = []
        if ref.total_capex:
            err.append((res.total_capex - ref.total_capex) / ref.total_capex)
        if ref.annual_opex:
            err.append((res.annual_opex - ref.annual_opex) / ref.annual_opex)
        if ref.capex_components:
            for component, expected_val in ref.capex_components.items():
                simulated_val = res.capex_components.get(component, 0.0)
                if expected_val != 0:
                    err.append((simulated_val - expected_val) / expected_val)
        return err

    calibrator.optimize("Finance", params, bounds, calc_residuals)


# ==========================================
# 2. RNA MASS CALIBRATION
# ==========================================
def calibrate_rna_mass(calibrator: Calibrator):
    
    params = {
        "exp_power_dd": 1.4,
        "exp_power_geared": 1.05,
        "exp_diameter_large": 2.2,
        "exp_diameter_small": 2.4,
        "rotor_scale_blade": 0.77,
        "rotor_scale_hub": 0.51,
        "rotor_scale_small": 1.0,
        "nacelle_mass_per_kw": 45.0
    }
    bounds = (
        [1.0, 0.5, 1.5, 1.5, 0.1, 0.1, 0.1, 10.0],
        [2.5, 2.5, 3.5, 3.5, 5.0, 5.0, 5.0, 150.0]
    )
    
    def calc_residuals(res: SimulationResult, ref: ReferenceData) -> List[float]:
        err = []
        if ref.rna_mass:
            err.append((res.rna_mass - ref.rna_mass) / ref.rna_mass)
        return err

    calibrator.optimize("RNA Mass", params, bounds, calc_residuals)


# ==========================================
# 3. WIND PARAMETERS CALIBRATION
# ==========================================
def calibrate_wind(calibrator: Calibrator):
    
    params = {
        "cut_in_power_fraction": 0.01,
        "cut_out_energy_fraction": 0.8,
        "rated_wind_base": 12.0,
        "rated_wind_nacelle_scaler": 0.15
    }
    bounds = ([0.001, 0.5, 8.0, 0.0], [0.1, 0.99, 16.0, 0.5])
    
    def calc_residuals(res: SimulationResult, ref: ReferenceData) -> List[float]:
        err = []
        if ref.generated_energy:
            err.append((res.generated_energy - ref.generated_energy) / ref.generated_energy)
        return err

    calibrator.optimize("Wind", params, bounds, calc_residuals)


# ==========================================
# 4. STRUCTURE CALIBRATION
# ==========================================
def calibrate_structure(calibrator: Calibrator):
    
    params = {
        "storm_drag_coefficient": 1.5,
        "buckling_safety_factor": 1.0
    }
    bounds = ([0.1, 0.1], [5.0, 5.0])
    
    def calc_residuals(res: SimulationResult, ref: ReferenceData) -> List[float]:
        err = []
        if ref.breaking_utilization:
            err.append((res.breaking_utilization - ref.breaking_utilization) / ref.breaking_utilization)
        if ref.buckeling_utilization:
            err.append((res.buckeling_utilization - ref.buckeling_utilization) / ref.buckeling_utilization)
        return err

    calibrator.optimize("Structure", params, bounds, calc_residuals)


# ==========================================
# JSON LOADER
# ==========================================
def load_test_cases_from_json(json_path: str) -> List[Tuple[WindTurbine, SiteEnvironment, ReferenceData]]:
    """Loads turbines, environments, and reference data from the JSON file."""
    
    with open(json_path, 'r') as f:
        datascenarios = json.load(f)
        
    cases = []
    for scenario in datascenarios:
        # 1. Build Environment
        env = SiteEnvironment(
            avg_wind_10=scenario["avg_wind_10"],
            roughness=scenario["roughness"],
            survival_gust=scenario["survival_gust"],
            k_factor=scenario["k_factor"],
            is_offshore=scenario["is_offshore"],
            inflation=scenario["inflation"],
            interest=scenario["interest"],
            # Add defaults for missing variables
            electricity_price=scenario.get("electricity_price", 55.0),
            green_certificate=scenario.get("green_certificate", 1.0)
        )
        
        turbine = WindTurbine(
            rotor_diameter=scenario["rotor_diameter"],
            height=scenario["height"],
            solidity=scenario["solidity"],
            gearbox=Gearbox(scenario["gearbox"]),
            generator=Generator(scenario["generator"]),
            top_diameter=scenario["top_diameter"],
            bottom_diameter=scenario["bottom_diameter"],
            wall_thickness=scenario["wall_thickness"],
            lifetime=scenario["lifetime"],
        )
        
        # 3. Build Reference Data
        ref = ReferenceData(
            id=scenario["id"],
            rna_mass=scenario.get("rna_mass"),
            total_capex=scenario.get("total_capex"),
            annual_opex=scenario.get("annual_opex"),
            generated_energy=scenario.get("generated_energy"),
            breaking_utilization=scenario.get("breaking_utilization"),
            buckeling_utilization=scenario.get("buckeling_utilization"),
            capex_components=scenario.get("capex_components")
        )
        
        cases.append((turbine, env, ref))
        
    return cases


def main():
    # 1. Load the data directly from JSON
    test_cases = load_test_cases_from_json("tests/reference_data.json")
    print(f"Loaded {len(test_cases)} test cases from reference_data.json")
    
    # 2. Initialize the generic calibrator
    calibrator = Calibrator(test_cases)
    
    # 3. Run calibrations
    calibrate_finance(calibrator)
    calibrate_rna_mass(calibrator)
    calibrate_wind(calibrator)
    calibrate_structure(calibrator)

if __name__ == "__main__":
    main()
