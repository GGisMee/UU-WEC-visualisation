# utils/ssn.py
from models.environment import SiteEnvironment


class SSNGenerator:
    @staticmethod
    def validate(ssn: str) -> bool:
        """Returnerar True om personnumret är i formatet YYYYMMDDXXXX."""
        return len(ssn) == 12 and ssn.isdigit()

    @staticmethod
    def apply_ssn_to_env(ssn: str, env: SiteEnvironment) -> SiteEnvironment:
        """Modifierar och returnerar ett SiteEnvironment-objekt baserat på SSN."""
        # Beräkna k-faktor, genomsnittsvind, etc. och skriv in i env
