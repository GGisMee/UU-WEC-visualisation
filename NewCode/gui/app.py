# gui/app.py
import customtkinter as ctk
from models.turbine import WindTurbine
from models.environment import SiteEnvironment
from models.simulation import SimulationEngine
from gui.console import ConsolePanel
from gui.canvas import CADCanvas
from gui.analytics import AnalyticsPanel


class UnifiedSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wind Power Simulator Pro")
        self.geometry("1200x750")

        # --- APPLIKATIONENS TILLSTÅND (STATE) ---
        self.turbine = WindTurbine(
            diameter=95.0,
            height=105.0,
            solidity=3.5,
            blades=3,
            gearbox="Medium-Speed",
            generator="DFIG",
        )
        self.environment = SiteEnvironment(
            avg_wind_u10=7.5,
            roughness=100.0,
            survival_gust=60.0,
            downtime=2.0,
            capture_efficiency=0.45,
            drivetrain_efficiency=0.90,
            electricity_price=30.0,
            green_certificate=1.0,
            inflation=2.0,
            interest=3.0,
            lifetime=22,
        )

        self.active_mission = None
        self.runs_remaining = 0
        self.simulation_out_of_date = True

        # --- SKAPA PANELER ---
        self.console = ConsolePanel(
            self,
            self.turbine,
            self.environment,
            on_change_callback=self.on_inputs_changed,
        )
        self.console.grid(row=1, column=0, sticky="nsw")

        self.cad_canvas = CADCanvas(self, self.turbine)
        self.cad_canvas.grid(row=1, column=1, sticky="nsew")

        self.analytics = AnalyticsPanel(self)
        self.analytics.grid(row=1, column=2, sticky="nsew")

    def on_inputs_changed(self):
        """Triggers direkt när en slider flyttas eller dropdown ändras."""
        # 1. Uppdatera turbinritningen live (utan att räkna fysik)
        self.cad_canvas.redraw()
        # 2. Flagga att simuleringen inte matchar ändringarna
        self.simulation_out_of_date = True
        self.analytics.show_out_of_date_warning()

    def run_simulation(self):
        """Körs när användaren trycker på 'RUN SIMULATION'."""
        # 1. Kör beräkningarna
        result = SimulationEngine.simulate(self.turbine, self.environment)

        # 2. Skicka resultaten till analyspanelen
        self.analytics.update_results(result)

        # 3. Om ett uppdrag är aktivt, kolla mål
        if self.active_mission:
            success, errors = self.active_mission.evaluate(result)
            self.analytics.show_mission_feedback(success, errors)
