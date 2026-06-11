# gui/app.py
from enum import Enum

import customtkinter as ctk
from models.turbine import WindTurbine
from models.environment import SiteEnvironment
from models.simulation import SimulationEngine
from gui.console import ConsolePanel
from gui.canvas import CADCanvas
from gui.analytics import AnalyticsPanel


class FusionTheme(Enum):
    # Format: VALUE = ("light_mode_hex", "dark_mode_hex")
    
    BG_MAIN = ("#F5F5F5", "#3B4453")
    BG_SURFACE = ("#FFFFFF", "#2C3440")
    BG_INPUT = ("#FFFFFF", "#282828")
    TEXT_MAIN = ("#000000", "#F5F5F5")
    TEXT_MUTED = ("#3C3C3C", "#F5F5F5")
    BORDER = ("#C8C8C8", "#505864")
    ACCENT = ("#ED742E", "#ED742E")  # Samma i båda lägen
    DELETE_HOVER = ("#BE3035", "#FF8D92")
    
    # Tooltip
    TOOLTIP_BG = ("#272E3A", "#161F2D")
    TOOLTIP_TEXT = ("#E8ECF2", "#DCE5F1")
    TOOLTIP_BORDER = ("#4A5361", "#3E4A5E")
    
    # Scrollbar
    SCROLLBAR_TRACK = ("#E6E6E6", "#222832")
    SCROLLBAR_THUMB = ("#AAAAAA", "#626C7A")
    SCROLLBAR_THUMB_HOVER = ("#8C8C8C", "#7A8492")
    
    # Chat specifikt
    CHAT_TEXT = ("#000000", "#FFFFFF")
    CHAT_MUTED = ("#757F8E", "#9CA8BB")


class FuturisticTheme(Enum):
    # Format: VALUE = ("light_mode_hex", "dark_mode_hex")
    
    BG_MAIN = ("#E2E8F0", "#080D16")          # Light cyber-gray vs Dark space background
    BG_SURFACE = ("#F1F5F9", "#111827")       # Light slate vs Slate panels
    BG_INPUT = ("#FFFFFF", "#1A2238")         # White vs Dark blue-slate card highlights
    TEXT_MAIN = ("#0F172A", "#F9FAFB")        # Dark slate vs Core text
    TEXT_MUTED = ("#475569", "#9CA3AF")       # Muted slate vs Subtitle text
    BORDER = ("#CBD5E1", "#2D3748")           # Light border vs Card stroke
    ACCENT = ("#FF7A00", "#FF7A00")           # Tech Orange
    DELETE_HOVER = ("#FF3E6C", "#FF3E6C")     # Cyber Red (ACCENT_RED)
    
    # Tooltip
    TOOLTIP_BG = ("#1E293B", "#1A2238")
    TOOLTIP_TEXT = ("#F9FAFB", "#F9FAFB")
    TOOLTIP_BORDER = ("#CBD5E1", "#2D3748")
    
    # Scrollbar
    SCROLLBAR_TRACK = ("#ECEFF1", "#080D16")
    SCROLLBAR_THUMB = ("#9CA3AF", "#1A2238")
    SCROLLBAR_THUMB_HOVER = ("#475569", "#2D3748")
    
    # Chat specifikt
    CHAT_TEXT = ("#0F172A", "#F9FAFB")
    CHAT_MUTED = ("#475569", "#9CA3AF")

    # Additional theme specific color tokens from mockup
    ACCENT_BLUE = ("#00A3C4", "#00D2FF")      # Electric Cyan
    ACCENT_ORANGE = ("#FF7A00", "#FF7A00")    # Tech Orange
    ACCENT_YELLOW = ("#D9A300", "#FFD000")    # Alert Yellow
    ACCENT_GREEN = ("#059669", "#10B981")     # Emerald Green
    ACCENT_RED = ("#E11D48", "#FF3E6C")       # Cyber Red




class UnifiedSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Wind Power Simulator Pro")
        self.geometry("1200x750")

        # --- APPLIKATIONENS TILLSTÅND (STATE) ---
        self.turbine: WindTurbine
        self.environment: SiteEnvironment

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

if __name__ == "__main__":
    app = UnifiedSimulatorApp()
    app.mainloop()