# config.py

# Physical Constants
AIR_DENSITY = 1.2  # kg/m^3
BETZ_LIMIT = 0.593  # Max theoretical efficiency for rotor (Cp)
WIND_DENSITY_COEFFICIENT = 0.62  # 0.5 * air_density (Excel matched value of ~1.24 kg/m^3)
C_T = 8.0 / 9.0  # Thrust coefficient
GRAVITY = 9.82  # m/s^2

# Structural Properties
STEEL_YIELD_STRENGTH = 160.0  # MPa, limit for bending stress in the steel tower
TOWER_MAX_WALL_THICKNESS = 150.0  # mm, max allowed thickness before becoming invalid
YOUNGS_MODULUS_STEEL = 210000e6  # Pa, Young's modulus for steel
STEEL_DENSITY = 7850  # kg/m^3, Structural steel density
STEEL_YIELD_STRESS = 235e6  # Pa, Breaking stress for steel

# Default Economic Values
DEFAULT_INSTALLATION_COST = 3500.0  # k€ (roads, grid connection, etc.)
DEFAULT_FINANCIAL_FEES_RATE = 0.07  # 7% extra cost on CAPEX for loans/fees