# models/challenge.py
from dataclasses import dataclass
from models.environment import SiteEnvironment
from models.simulation import SimulationResult


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
