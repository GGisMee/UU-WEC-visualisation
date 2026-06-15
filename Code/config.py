# NewCode/config.py

# Fysikaliska konstanter
AIR_DENSITY = 1.2  # kg/m^3
BETZ_LIMIT = 0.593  # Max teoretisk verkningsgrad för rotor (Cp)
WIND_DENSITY_COEFFICIENT = 0.62  # 0.5 * air_density (Excel matched value of ~1.24 kg/m^3)

# Hållfasthet
STEEL_YIELD_STRENGTH = 160.0  # MPa, gräns för böjspänning i ståltornet
TOWER_MAX_WALL_THICKNESS = 150.0  # mm, maximal tillåten tjocklek innan det blir ogiltigt/rött

# Standardvärden för ekonomi
DEFAULT_INSTALLATION_COST = 3500.0  # k€ (vägar, nätanslutning, etc.)
DEFAULT_FINANCIAL_FEES_RATE = 0.07  # 7% extra kostnader på CAPEX för lån/avgifter

# TODO: Lägg in scale och andra sådanna dev parametrar möjligtvis låta användaren ändar det med en settings sida
# TODO: Implementera fler av dessa