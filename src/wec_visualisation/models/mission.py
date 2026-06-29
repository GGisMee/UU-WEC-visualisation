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
    tooltip: str = ""
    raw_val: str = ""
    raw_msg_key: str = ""
    target_val: float = 0.0

@dataclass
class Constraint:
    """Constraint and info about it"""
    constraint_name: str       # E.g. "Total CAPEX"
    check: str                 # E.g. "<"
    target: float              # E.g. 5.0
    unit: str                  # E.g. "M€"  
    display_text: tuple[str, str]          # E.g ("Failed, too high:", "CAPEX well managed:")
    value_getter: Callable[[WindTurbine, SimulationResult], float] # Function to get actual value
    tooltip: str = ""
    
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
            actual_value_text=f"{formatted_val}{unit_suffix} ({text_prefix})",
            tooltip=self.tooltip,
            raw_val=f"{formatted_val}{unit_suffix}",
            raw_msg_key=self.display_text[1] if passed else self.display_text[0],
            target_val=self.target
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
                    description="Sandbox: explore turbine sizes and parameters with unlimited simulation runs at Lillgrund, a shallow water site in Öresund, Sweden.",
                    env=env,
                    constraints=[],
                    max_runs=None
                    )
                
            case DefaultMissions.ARCTIC_GALE:
                return Mission(
                    name="The Arctic Gale",
                    description="Design a storm-hardened offshore turbine at Dogger Bank in the North Sea. This site features strong, sustained winds but is prone to extreme arctic storm gusts and waves.",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Buckling Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Buckling risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.buckling_utilization,
                            tooltip="Must not exceed a buckling utilization factor of 1.0 to prevent structural collapse."
                        ),
                        Constraint(
                            constraint_name="Breaking Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Breaking risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.breaking_utilization,
                            tooltip="Must not exceed a breaking utilization factor of 1.0 to prevent material failure."
                        ),
                        Constraint(
                            constraint_name="Profit Margin",
                            check=">=", target=10.0, unit="%",
                            display_text=("Margin too low", "Margin met"),
                            value_getter=lambda turbine, result: result.margin * 100.0,
                            tooltip="Must achieve a profit margin of at least 10%."
                        )
                    ],
                    max_runs=6
                    )
                
            case DefaultMissions.THE_GENTLE_BREEZE:
                return Mission(
                    name="The Gentle Breeze",
                    description="Design a wind turbine for high energy production in low-wind conditions at Smöla forest site in Norway. This inland site has high surface roughness from trees and strict zoning laws.",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Total Height",
                            check="<=", target=160.0, unit="m",
                            display_text=("Too high", "Height OK"),
                            value_getter=lambda turbine, result: turbine.height + (turbine.rotor_diameter / 2),
                            tooltip="Total height (tower + rotor radius) must be at most 160m due to zoning laws."
                        ),
                        Constraint(
                            constraint_name="Annual Production",
                            check=">=", target=1800.0, unit="MWh",
                            display_text=("Low production", "Production OK"),
                            value_getter=lambda turbine, result: result.generated_energy,
                            tooltip="Annual energy production must be at least 1800 MWh."
                        ),
                        Constraint(
                            constraint_name="Total CAPEX",
                            check="<", target=5000.0, unit="k€",
                            display_text=("Budget exceeded", "Within budget"),
                            value_getter=lambda turbine, result: result.total_capex,
                            tooltip="Total Capital Expenditure must be less than 5000 k€."
                        )
                    ],
                    max_runs=6
                    )
 
            case DefaultMissions.THE_COMMUNITY_COOPERATIVE:
                return Mission(
                    name="The Community Cooperative",
                    description="Build a community-friendly onshore turbine near Markbygden, Sweden. The site is a flat agricultural landscape near a small community, requiring noise limits and high safety.",
                    env=env,
                    constraints=[
                        Constraint(
                            constraint_name="Profit Margin",
                            check=">=", target=5.0, unit="%",
                            display_text=("Low profit margin", "Margin OK"),
                            value_getter=lambda turbine, result: result.margin * 100.0,
                            tooltip="Must achieve a profit margin of at least 5%."
                        ),
                        Constraint(
                            constraint_name="Buckling Utilization",
                            check="<=", target=1.0, unit="",
                            display_text=("Buckling risk", "Structure OK"),
                            value_getter=lambda turbine, result: result.buckling_utilization,
                            tooltip="Must not exceed a buckling utilization factor of 1.0."
                        )
                    ],
                    max_runs=6
                    )

