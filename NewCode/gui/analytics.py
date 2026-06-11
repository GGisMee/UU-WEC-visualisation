# gui/analytics.py
import customtkinter as ctk
import tkinter as tk
from enum import Enum


class AnalyticsPanel(ctk.CTkFrame):
    def __init__(self, parent, on_simulate_click):
        super().__init__(parent, width=420, fg_color="#111827", border_width=1, border_color="#2D3748")
        self.on_simulate = on_simulate_click
        
        # Skapa Tabview för grafer, mekanik-rapport och ekonomi
        self.tabs = ctk.CTkTabview(self, fg_color="transparent")
        self.tabs.pack(fill="both", expand=True)
        
        # Laddningsskärm (Overlay)
        self.loading_overlay = ctk.CTkFrame(self, fg_color="#111827")
        self.warning_banner = ctk.CTkFrame(self, fg_color="#332B12") # "Rerun Simulation"
        
        self.create_widgets()

    def show_warning_banner(self):
        self.warning_banner.place(...)  # Visa banner om inputs ändrats

    def display_results(self, result):
        """Fyller i faktisk data från SimulationResult."""
        # 1. Dölj laddningsskärm & varningsbanner
        self.warning_banner.place_forget()
        
        # 2. Uppdatera labels i Audit & Economics med faktisk data:
        # self.lbl_power.configure(text=f"{result.rated_power:.1f} kW")
        
        # 3. Rita upp kurvor på grafernas Canvas utifrån faktiska punkter i resultatet
        self.draw_weibull_curve(result)
        self.draw_power_curve(result)
        self.draw_capex_bar(result)

    def draw_weibull_curve(self, result):
        # Ritar den matematiskt korrekta Weibull-fördelningen utifrån result.weibull_C och result.weibull_k