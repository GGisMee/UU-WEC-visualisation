import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Code.economics import Economics
from Code.user_input import InputData
from Code.energy_calculations import EnergyCalculations

inp_data = InputData("Gustav Gamstedt", "199908266714", 37,44)
energy_calcs = EnergyCalculations(inp_data)
economics = Economics(inp_data, energy_calcs.output_data)
economics.update()