# models/challenge.py
from dataclasses import dataclass
from wec_visualisation.models.environment import SiteEnvironment
from wec_visualisation.models.simulation import SimulationResult
from wec_visualisation.models.environment import SSNGenerator
from wec_visualisation.models.turbine import WindTurbine
from enum import Enum
from typing import Callable

@dataclass
class ConstraintEvaluation:
    """Carries the result of an evaluated constraint"""
    constraint_name: str
    target_text: str
    passed: bool
    actual_value_text: str

@dataclass
class Constraint:
    """Constraint and info about it"""
    constraint_name: str       # E.g. "Total CAPEX"
    check: str                 # E.g. "<"
    target: float              # E.g. 5.0
    unit: str                  # E.g. "M€"  
    display_text: tuple[str, str]          # E.g ("Failed, too high:", "CAPEX well managed:")
    value_getter: Callable[[WindTurbine, SimulationResult], float] # Function to get actual value
    
    def evaluate(self, turbine: WindTurbine, result: SimulationResult) -> ConstraintEvaluation:
        val = self.value_getter(turbine, result)
        
        # Evaluate based on operator
        if self.check == "<=": passed = val <= self.target
        elif self.check == ">=": passed = val >= self.target
        elif self.check == "<": passed = val < self.target
        elif self.check == ">": passed = val > self.target
        else: passed = False
        
        text_prefix = self.display_text[1] if passed else self.display_text[0]
        
        # Format values > 1000 without decimals, else 1-2 decimals
        formatted_val = f"{val:,.0f}" if val > 1000 else f"{val:.2f}"
        unit_suffix = f" {self.unit}" if self.unit else ""
        
        return ConstraintEvaluation(
            constraint_name=self.constraint_name,
            target_text=f"{self.check} {self.target} {self.unit}".strip(),
            passed=passed,
            actual_value_text=f"{formatted_val}{unit_suffix} ({text_prefix})"
        )
        
@dataclass
class MissionReport:
    """Complete Report of how Mission went after Simulation"""
    success: bool                          # Did we pass the mission?
    evaluations: list[ConstraintEvaluation] # List of results for each constraint

@dataclass
class Mission:
    name: str
    description: str
    env: SiteEnvironment 
    constraints: list[Constraint] # List of constraint evaluator methods
    max_runs: int | None # None <=> Infinite

    def evaluate(self, turbine: WindTurbine, result: SimulationResult) -> MissionReport:
        """Evaluates if the simulation cleared the mission goals."""
        evals = []
        success = True
        
        for constraint in self.constraints:
            eval_result = constraint.evaluate(turbine, result)
            evals.append(eval_result)
            if not eval_result.passed:
                success = False
                
        return MissionReport(success=success, evaluations=evals)

class DefaultMissions(Enum):
    """Enum with default missions to choose between"""
    SANDBOX = "sandbox"
    ARCTIC_GALE = "arctic_gale"
    THE_GENTLE_BREEZE = "the_gentle_breeze"
    THE_COMMUNITY_COOPERATIVE = "the_community_cooperative"

    def create(self, env: SiteEnvironment) -> Mission:
        # Match enum value and return the correct Mission
        match self:
            case DefaultMissions.SANDBOX:
                return Mission(
                    name="Sandbox",
                    description="Free play sandbox: explore turbine sizes and parameters with unlimited simulation runs.",
                    env=env,
                    constraints=[],
                    max_runs=None
                    )
                
            case DefaultMissions.ARCTIC_GALE:
                return Mission(
                    name="Arctic Gale",
                    description="Design a wind farm that can withstand the worlds strongest sustained winds",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Buckling Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Buckling risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.buckeling_utilization
                        ),
                        Constraint(
                            constraint_name="Breaking Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Breaking risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.breaking_utilization
                        ),
                        Constraint(
                            constraint_name="Profit Margin",
                            check=">=", target=10.0, unit="%",
                            display_text=("Margin too low", "Margin met"),
                            value_getter=lambda turbine, result: result.margin * 100.0
                        )
                    ],
                    max_runs=6
                    )
                
            case DefaultMissions.THE_GENTLE_BREEZE:
                return Mission(
                    name="The Gentle Breeze",
                    description="Design a wind farm for high energy production in low-wind conditions",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Total Height",
                            check="<=", target=160.0, unit="m",
                            display_text=("Too high", "Height OK"),
                            value_getter=lambda turbine, result: turbine.height + (turbine.rotor_diameter / 2)
                        ),
                        Constraint(
                            constraint_name="Annual Production",
                            check=">=", target=1800.0, unit="MWh",
                            display_text=("Low production", "Production OK"),
                            value_getter=lambda turbine, result: result.generated_energy
                        ),
                        Constraint(
                            constraint_name="Total CAPEX",
                            check="<", target=5000.0, unit="k€",
                            display_text=("Budget exceeded", "Within budget"),
                            value_getter=lambda turbine, result: result.total_capex
                        )
                    ],
                    max_runs=6
                    )
 
            case DefaultMissions.THE_COMMUNITY_COOPERATIVE:
                return Mission(
                    name="The Community Cooperative",
                    description="Onshore flat land near a small community.",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Profit Margin",
                            check=">=", target=5.0, unit="%",
                            display_text=("Low profit margin", "Margin OK"),
                            value_getter=lambda turbine, result: result.margin * 100.0
                        ),
                        Constraint(
                            constraint_name="Buckling Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Buckling risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.buckeling_utilization
                        )
                    ],
                    max_runs=6
                    )

