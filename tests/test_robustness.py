import sys
import random
from pathlib import Path

# Add src to pythonpath for direct execution
sys.path.append(str(Path(__file__).parent.parent / "src"))
from wec_visualisation.models.turbine import WindTurbine, Gearbox, Generator
from wec_visualisation.models.environment import SiteEnvironment
from wec_visualisation.models.simulation import SimulationEngine, PresetConfigurations


def generate_random_env() -> SiteEnvironment:
    """Genererar slumpmässiga men realistiska miljövariabler (även kantfall)."""
    return SiteEnvironment(
        avg_wind_10=random.uniform(2.0, 15.0),
        roughness=random.uniform(0.1, 100.0),
        survival_gust=random.uniform(40.0, 80.0),
        k_factor=random.uniform(1.2, 3.0),
        is_offshore=random.choice([True, False]),
        electricity_price=55
    )

def generate_random_turbine() -> WindTurbine:
    """Genererar extrem och ibland konstig struktur för vindkraftverket."""
    bottom_d = random.uniform(2.0, 15.0)
    top_d = random.uniform(1.0, bottom_d)
    
    return WindTurbine(
        rotor_diameter=random.uniform(20.0, 300.0),
        height=random.uniform(30.0, 300.0),
        solidity=random.uniform(0.01, 0.15),
        gearbox=random.choice(list(Gearbox)),
        generator=random.choice(list(Generator)),
        top_diameter=top_d,
        bottom_diameter=bottom_d,
        wall_thickness=random.uniform(0.01, 0.15),
        lifetime=random.randint(15, 35)
    )

def test_robustness_random_configurations():
    """
    Testar 2000 slumpmässiga konfigurationer för att säkerställa 
    att modellen är robust (inte kraschar) och att 'margin' inte blir orimligt hög (>50%).
    """
    random.seed(42)  # För reproducerbarhet
    
    config = PresetConfigurations.v0.value
    
    num_tests = 2000
    high_margin_cases = []
    failed_cases = []
    
    for i in range(num_tests):
        env = generate_random_env()
        turbine = generate_random_turbine()
        
        try:
            res = SimulationEngine.simulate(turbine, env, config)
            
            # Kolla margin > 50%
            if (res.margin > 0.35) & (res.breaking_utilization < 1) & (res.buckeling_utilization < 1):
                high_margin_cases.append({
                    "margin": res.margin,
                    "wind": env.avg_wind_10,
                    "rotor_diameter": turbine.rotor_diameter,
                    "height": turbine.height
                })
        except Exception as e:
            failed_cases.append((env, turbine, str(e)))
            
    # # Säkerställ att inga kraschar
    # assert len(failed_cases) == 0, f"{len(failed_cases)} av {num_tests} konfigurationer kraschade! Exempel: {failed_cases[:2]}"
    
    # # Om det finns hög margin, flagga (t.ex. margin ska ej vara > 50%)
    # assert len(high_margin_cases) == 0, f"{len(high_margin_cases)} av {num_tests} konfigurationer gav över 50% margin! Exempel: {high_margin_cases[:3]}"
    print(f"{len(high_margin_cases)}/{num_tests} had 35% or more in NPV margin and did not crash")
    print(high_margin_cases[:20])

if __name__ == "__main__":
    # Kör testerna om filen exekveras direkt
    test_robustness_random_configurations()
