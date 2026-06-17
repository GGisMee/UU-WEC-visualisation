import sys
from pathlib import Path

# Ensure src is in PYTHONPATH so we can run this file directly
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent))

from wec_visualisation.models.simulation import SimulationEngine, SimulationConfiguration
from calibrate import load_test_cases_from_json

def compare_results():
    print("Loading reference data...")
    try:
        test_cases = load_test_cases_from_json("tests/reference_data.json")
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return
        
    # We will use the default uncalibrated configuration
    config = SimulationConfiguration()
    
    metrics_to_compare = [
        "rna_mass",
        "total_capex",
        "annual_opex",
        "generated_energy",
        "buckeling_utilization"
    ]
    
    print("=" * 80)
    print("SIMULATION VS REFERENCE DATA COMPARISON (Default Configuration)")
    print("=" * 80)
    
    for turbine, env, ref in test_cases:
        print(f"\nTurbine ID: {ref.id}")
        print("-" * 70)
        
        # Run uncalibrated simulation
        res = SimulationEngine.simulate(turbine, env, config=config)
        
        print(f"{'Metric':<25} | {'Reference':<15} | {'Simulated':<15} | {'Diff (%)':<10}")
        print("-" * 70)
        
        for metric in metrics_to_compare:
            expected = getattr(ref, metric)
            if expected is not None:
                simulated = getattr(res, metric)
                
                # Calculate percentage difference
                if expected != 0:
                    diff_pct = ((simulated - expected) / expected) * 100.0
                else:
                    diff_pct = float('inf')
                    
                # Format numbers cleanly
                print(f"{metric:<25} | {expected:<15.1f} | {simulated:<15.1f} | {diff_pct:>+8.2f}%")
        
        print("-" * 70)

if __name__ == "__main__":
    compare_results()
