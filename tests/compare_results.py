import sys
import json
from pathlib import Path

# Ensure src is in PYTHONPATH so we can run this file directly
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent))

from wec_visualisation.models.simulation import SimulationEngine, SimulationConfiguration, SimulationResult
from calibrate import load_test_cases_from_json

def compare_results():
    print("Loading reference data...")
    try:
        test_cases = load_test_cases_from_json("tests/reference_data.json")
        with open("tests/reference_data.json") as f:
            raw_data = json.load(f)
        raw_map = {d["id"]: d for d in raw_data}
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return
        
    # We will use the default uncalibrated configuration
    config = SimulationConfiguration()
    
    print("=" * 90)
    print("SIMULATION VS REFERENCE DATA COMPARISON (Default Configuration)")
    print("=" * 90)
    
    for turbine, env, ref in test_cases:
        print(f"\nTurbine ID: {ref.id}")
        print("-" * 90)
        
        # Run uncalibrated simulation
        res = SimulationEngine.simulate(turbine, env, config=config)
        
        print(f"{'Metric':<30} | {'Reference':<15} | {'Simulated':<15} | {'Diff (%)':<10}")
        print("-" * 90)
        
        raw_dict = raw_map[ref.id]
        
        # Dynamically grab all fields defined in SimulationResult
        for metric in getattr(SimulationResult, "__annotations__", {}):
            expected = raw_dict.get(metric)
            simulated = getattr(res, metric, None)
            
            # Skip if it doesn't exist in the JSON or if it's not simulated
            if expected is None or simulated is None:
                continue
                
            if isinstance(expected, dict) and isinstance(simulated, dict):
                print(f"{metric:<30} | {'':<15} | {'':<15} | ")
                for key in expected:
                    sub_exp = expected[key]
                    sub_sim = simulated.get(key, 0.0)
                    if sub_exp != 0:
                        diff_pct = ((sub_sim - sub_exp) / sub_exp) * 100.0
                    else:
                        diff_pct = float('inf')
                    print(f"  - {key:<26} | {sub_exp:<15.1f} | {sub_sim:<15.1f} | {diff_pct:>+8.2f}%")
            else:
                # Normal float/int comparison
                try:
                    expected_float = float(expected)
                    simulated_float = float(simulated)
                    
                    if expected_float != 0:
                        diff_pct = ((simulated_float - expected_float) / expected_float) * 100.0
                    else:
                        diff_pct = float('inf')
                    print(f"{metric:<30} | {expected_float:<15.2f} | {simulated_float:<15.2f} | {diff_pct:>+8.2f}%")
                except (ValueError, TypeError):
                    # In case there are non-numeric strings
                    pass
        
        print("-" * 90)

if __name__ == "__main__":
    compare_results()
