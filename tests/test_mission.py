import pytest
from unittest.mock import Mock
from wec_visualisation.models.mission import Constraint, ConstraintEvaluation, Mission
from wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator

@pytest.fixture
def mock_turbine():
    return WindTurbine(rotor_diameter=100.0, height=100.0, solidity=0.05, gearbox=Gearbox.HIGH_SPEED, generator=Generator.DFIG)

@pytest.fixture
def mock_result():
    res = Mock()
    res.buckling_utilization = 0.8
    res.margin = 0.15 # 15%
    return res

def test_constraint_evaluate_less_than_equals(mock_turbine, mock_result):
    c = Constraint(
        constraint_name="Buckling",
        check="<=", target=1.0, unit="",
        display_text=("Fail", "Pass"),
        value_getter=lambda t, r: r.buckling_utilization
    )
    
    evaluation = c.evaluate(mock_turbine, mock_result)
    assert evaluation.passed is True
    assert evaluation.constraint_name == "Buckling"
    assert "Pass" in evaluation.actual_value_text
    
def test_constraint_evaluate_greater_than_equals(mock_turbine, mock_result):
    c = Constraint(
        constraint_name="Margin",
        check=">=", target=10.0, unit="%",
        display_text=("Fail", "Pass"),
        value_getter=lambda t, r: r.margin * 100.0
    )
    
    evaluation = c.evaluate(mock_turbine, mock_result)
    assert evaluation.passed is True
    assert "15.00 %" in evaluation.actual_value_text

def test_mission_evaluate(mock_turbine, mock_result):
    c1 = Constraint(
        constraint_name="Buckling", check="<=", target=1.0, unit="",
        display_text=("Fail", "Pass"), value_getter=lambda t, r: r.buckling_utilization
    )
    c2 = Constraint(
        constraint_name="Margin", check=">=", target=20.0, unit="%", # Will fail (15 < 20)
        display_text=("Fail", "Pass"), value_getter=lambda t, r: r.margin * 100.0
    )
    
    m = Mission(name="Test", description="Test", env=Mock(), constraints=[c1, c2], max_runs=6)
    report = m.evaluate(mock_turbine, mock_result)
    
    assert report.success is False
    assert len(report.evaluations) == 2
    assert report.evaluations[0].passed is True
    assert report.evaluations[1].passed is False
