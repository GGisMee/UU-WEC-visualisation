import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
import numpy as np
from numpy.polynomial import Polynomial
from scipy.interpolate import CubicSpline

# def capture_efficiency(solidity:float|np.ndarray) -> float:
#     if not hasattr(capture_efficiency, "polynomial"):
#         solidity_points = np.array((0,1.5, 3, 10,20))/100 # In quotient
#         capture_efficienty_points = np.array((0,0.35, 0.51, 0.35,0)) 
#         capture_efficiency.polynomial = Polynomial.fit(solidity_points, capture_efficienty_points, deg=3) # type: ignore
#     return capture_efficiency.polynomial(solidity) # type: ignore

# def capture_efficiency(solidity: float | np.ndarray) -> float | np.ndarray:

#     if not hasattr(capture_efficiency, "cp_interp"):
#         # Enbart punkter för det lyftkraftsbaserade verket
#         sigma_pts = np.array([0.0, 0.01, 0.035, 0.10, 0.20])
#         cp_pts    = np.array([0.0, 0.35,  0.48, 0.35, 0.00])

#         capture_efficiency.cp_interp = PchipInterpolator(sigma_pts, cp_pts) # type: ignore
#     return capture_efficiency.cp_interp(solidity) # type: ignore



def capture_efficiency(solidity: float) -> float:
    if not hasattr(capture_efficiency, "cp_interp"):
        # 1. Definiera de täta, sorterade punkterna
        sigma_pts = np.array([0.0,   0.015, 0.025, 0.040, 0.060, 0.100, 0.200])
        cp_pts    = np.array([0.04,   0.25,  0.38,  0.48,  0.42,  0.25,  0.04])

        # 2. Skapa interpolatorn med CubicSpline
        # bc_type='clamped' tvingas derivatan till 0 vid ändpunkterna för snyggare kurva
        capture_efficiency.cp_spline = CubicSpline(sigma_pts, cp_pts, bc_type='clamped') # type: ignore

    v = capture_efficiency.cp_spline(solidity) # type:ignore
    if solidity > 0.1:
        value_at_01 = capture_efficiency.cp_spline(0.1) # type:ignore
        t = (solidity-0.1)/(0.5-0.1) # [0,1] from first solidity=0.1 to solidity=0.5
        res = value_at_01+t*(0.04-value_at_01) # Linear interpolation
    else:
        res = v # Cubic interpol
    return res if res >= 0.04 else 0.04


solidity = np.linspace(0,0.5, 100)
solidity_points = np.array((1.5,3,10))/100
capture_efficienty_points = np.array((0.25, 0.51, 0.25)) 

# plt.scatter(solidity_points, [capture_efficiency(p) for p in solidity_points])
plt.scatter(solidity_points,capture_efficienty_points)
plt.plot(solidity, [capture_efficiency(p) for p in solidity])
plt.show()