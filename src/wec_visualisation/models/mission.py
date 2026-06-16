# models/challenge.py
from dataclasses import dataclass
from wec_visualisation.models.environment import SiteEnvironment
from wec_visualisation.models.simulation import SimulationResult
from wec_visualisation.models.environment import SSNGenerator
from enum import Enum

class DefaultMissions(Enum):
    SANDBOX = "sandbox"
    ARCTIC_GALE = "arctic_gale"
    THE_GENTLE_BREEZE = "the_gentle_breeze"
    THE_COMMUNITY_COOPERATIVE = "the_community_cooperative"

    def create(self, env: SiteEnvironment) -> Mission:
        # Matchar enum-värdet och returnerar rätt Mission
        match self:
            case DefaultMissions.SANDBOX:
                return Mission(
                    name="Sandbox",
                    description="Free play sandbox: explore turbine sizes and parameters with unlimited simulation runs.",
                    env=env,
                    constraints={},
                    max_runs=None
                    )
                
            case DefaultMissions.ARCTIC_GALE:
                return Mission(
                    name="Arctic Gale",
                    description="Design a wind farm that can withstand the worlds strongest sustained winds",
                    env=env,
                    constraints={ # True => OK, False => Fail
                        "utilization": lambda utilization: utilization >= 1.5, 
                        "margin": lambda margin: margin >= 0, 
                    },
                    max_runs=6
                    )
                
            case DefaultMissions.THE_GENTLE_BREEZE:
                return Mission(
                    name="The Gentle Breeze",
                    description="Design a wind farm for high energy production in low-wind conditions",
                    env=env,
                    constraints={
                        "tip_height": lambda tip_height:tip_height <= 160, # [m]
                        "generated_energy": lambda generated_energy: generated_energy >= 5500, # [MWh]
                        "total_capex": lambda total_capex: total_capex <= 3000 # [M$]
                        
                        
                    },
                    max_runs=6
                    )

            case DefaultMissions.THE_COMMUNITY_COOPERATIVE:
                return Mission(
                    name="The Community Cooperative",
                    description="Onshore plattlandskap nära ett litet samhälle.",
                    env=env,
                    constraints={},
                    max_runs=6
                    )


@dataclass
class Mission:
    name: str
    description: str
    env: SiteEnvironment 
    constraints: dict  # t.ex. {"min_safety_factor": 1.6, "min_margin": 10.0, "max_capex": 5000.0}
    max_runs: int | None # None <=> Evigt

    def evaluate(self, result: SimulationResult) -> tuple[bool, list[str]]:
        """Utvärderar om simuleringen klarade uppdragets mål.

        Returnerar (Success, lista_med_felmeddelanden).
        """
        pass
