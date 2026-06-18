import pytest
from wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator

def test_windturbine_swept_area():
    wt = WindTurbine(rotor_diameter=100.0, height=100.0, solidity=0.05, gearbox=Gearbox.HIGH_SPEED, generator=Generator.DFIG)
    # Area = pi * r^2 = pi * 50^2 = 7853.98
    assert wt.swept_area == pytest.approx(7853.98, rel=1e-4)

def test_windturbine_slenderness_ratio():
    wt = WindTurbine(rotor_diameter=100.0, height=120.0, solidity=0.05, bottom_diameter=6.0, gearbox=Gearbox.HIGH_SPEED, generator=Generator.DFIG)
    assert wt.slenderness_ratio == 20.0

def test_windturbine_capture_efficiency():
    wt = WindTurbine(rotor_diameter=100.0, height=100.0, solidity=0.04, gearbox=Gearbox.HIGH_SPEED, generator=Generator.DFIG)
    # Based on the spline points, solidity 0.04 is mapped to cp 0.48
    assert wt.capture_efficiency == pytest.approx(0.48, abs=0.01)
    
    wt.solidity = 0.5
    # For solidity >= 0.5, it should decay linearly to 0.04
    assert wt.capture_efficiency == pytest.approx(0.04, abs=0.01)

def test_windturbine_drivetrain_modifiers():
    wt = WindTurbine(rotor_diameter=100.0, height=100.0, solidity=0.05, gearbox=Gearbox.NONE, generator=Generator.SYNCHRONOUS)
    
    assert wt.drivetrain_efficiency == 0.96
    assert wt.downtime == 0.02
    assert wt.drivetrain_cost_modifier == 1.25
    assert wt.opex_modifier == 0.50
    assert wt.nacelle_mass_modifier == 1.50
