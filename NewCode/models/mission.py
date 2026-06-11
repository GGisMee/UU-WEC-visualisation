# models/challenge.py
from dataclasses import dataclass
from models.environment import SiteEnvironment
from models.simulation import SimulationResult
from utils.ssn import SSNGenerator
from enum import Enum


class DefaultMissions(Enum):
    Sandbox = Mission(
        name="Sandbox",
        description="Free Play Sandbox: Explore turbine sizes and parameters with unlimited simulation runs.",
        max_runs = 10000,
        constraints={},
        env=SSNGenerator.apply_ssn_to_env(ssn="199801281234",env=SiteEnvironment())

        )
    
    Economic_Challange = Mission()

@dataclass
class Mission:
    name: str
    description: str
    env: SiteEnvironment
    constraints: dict  # t.ex. {"min_safety_factor": 1.6, "min_margin": 10.0, "max_capex": 5000.0}
    max_runs: int

    def evaluate(self, result: SimulationResult) -> tuple[bool, list[str]]:
        """Utvärderar om simuleringen klarade uppdragets mål.

        Returnerar (Success, lista_med_felmeddelanden).
        """
