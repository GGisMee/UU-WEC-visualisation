import sys
import json
import numpy as np
import dataclasses
from pathlib import Path

# Ensure src is in PYTHONPATH so we can run this file directly
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent))

from wec_visualisation.models.simulation import SimulationEngine, SimulationConfiguration, SimulationResult
from calibrate import load_test_cases_from_json


def calculate_diffs(expected: np.ndarray, simulated: np.ndarray) -> np.ndarray:
    """
    Calculate the percentage difference between simulated and expected arrays.
    Handles division by zero by setting diff to np.inf where expected is 0.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        diffs = ((simulated - expected) / expected) * 100.0
        # If expected is exactly 0, replace NaN/inf with inf
        diffs = np.where(expected == 0, np.inf, diffs)
    return diffs


def print_table(title: str, headers: list[str], columns: list[list[str]], col_widths: list[int] = None):
    """
    Prints a generic formatted table.
    title: Title of the table
    headers: list of column names
    columns: list of string-formatted data columns corresponding to each header
    col_widths: optional list of integer widths for each column
    """
    if not columns or not headers:
        return
        
    num_rows = len(columns[0])
    num_cols = len(headers)
    
    if col_widths is None:
        col_widths = [max(len(h), 15) for h in headers]
        
    header_str = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    
    if title:
        print(f"\n{title}")
    print("-" * len(header_str))
    print(header_str)
    print("-" * len(header_str))
    
    for i in range(num_rows):
        row_strs = [f"{columns[j][i]:<{col_widths[j]}}" for j in range(num_cols)]
        print(" | ".join(row_strs))
        
    print("-" * len(header_str))


def extract_comparison_data(res: SimulationResult, raw_dict: dict) -> tuple[list[str], np.ndarray, np.ndarray]:
    """
    Extracts metrics, expected values, and simulated values from the raw JSON dict and the SimulationResult.
    
    Returns:
        metrics: list of metric names
        expected_array: np.ndarray of reference values
        simulated_array: np.ndarray of simulated values
    """
    metrics = []
    expected_vals = []
    simulated_vals = []
    
    for metric in getattr(SimulationResult, "__annotations__", {}):
        expected = raw_dict.get(metric)
        simulated = getattr(res, metric, None)
        
        if expected is None or simulated is None:
            continue
            
        if isinstance(expected, dict) and isinstance(simulated, dict):
            # Add a header row for the dictionary (using NaN to signal header to the printer)
            metrics.append(metric)
            expected_vals.append(np.nan)
            simulated_vals.append(np.nan)
            
            for key in expected:
                metrics.append(f"  - {key}")
                expected_vals.append(float(expected[key]))
                simulated_vals.append(float(simulated.get(key, 0.0)))
        else:
            try:
                exp_f = float(expected)
                sim_f = float(simulated)
                metrics.append(metric)
                expected_vals.append(exp_f)
                simulated_vals.append(sim_f)
            except (ValueError, TypeError):
                pass
                
    return metrics, np.array(expected_vals), np.array(simulated_vals)


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
        
    config = SimulationConfiguration()
    
    print("=" * 90)
    print("SIMULATION VS REFERENCE DATA COMPARISON (Default Configuration)")
    print("=" * 90)
    diffs_per_turbine = []
    for turbine, env, ref in test_cases:
        # Run uncalibrated simulation
        res = SimulationEngine.simulate(turbine, env, config=config)
        raw_dict = raw_map[ref.id]
        
        # 1. Extract data into lists/numpy arrays
        metrics, expected, simulated = extract_comparison_data(res, raw_dict)
        
        # 2. Estimate differences using vectorized numpy math
        diffs = calculate_diffs(expected, simulated)
        diffs_per_turbine.append(diffs)
        
        # 3. Format columns as strings for generic table printer
        exp_strs = [f"{v:.2f}" if not np.isnan(v) else "" for v in expected]
        sim_strs = [f"{v:.2f}" if not np.isnan(v) else "" for v in simulated]
        
        diff_strs = []
        for d in diffs:
            if np.isnan(d):
                diff_strs.append("")
            elif np.isinf(d):
                diff_strs.append("inf")
            else:
                diff_strs.append(f"{d:>+8.2f}%")
                
        columns = [metrics, exp_strs, sim_strs, diff_strs]
        headers = ["Metric", "Reference", "Simulated", "Diff (%)"]
        col_widths = [25, 15, 15, 10]
        
        # 4. Print the table
        print_table(f"Turbine ID: {ref.id}", headers, columns, col_widths)
    mean_diffs = np.mean(diffs_per_turbine, axis=0)
    std_diffs = np.std(diffs_per_turbine, axis=0)

    print_table(f"Std diffs",["Metric", "Mean","Std div"], [metrics,mean_diffs, std_diffs], col_widths)

if __name__ == "__main__":
    compare_results()
