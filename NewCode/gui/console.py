# gui/console.py
import customtkinter as ctk
import tkinter as tk

class ConsolePanel(ctk.CTkFrame):
    def __init__(self, parent, turbine, environment, on_change_callback, on_ssn_callback):
        super().__init__(parent, width=320, fg_color="#111827", border_width=1, border_color="#2D3748")
        self.turbine = turbine
        self.environment = environment
        self.on_change = on_change_callback
        self.on_ssn = on_ssn_callback
        
        # Tkinter-variabler för att styra GUI-tillstånd
        self.diam_var = tk.DoubleVar(value=turbine.diameter)
        self.height_var = tk.DoubleVar(value=turbine.height)
        # ... Fler variabler för alla parametrar
        
        self.create_widgets()

    def create_widgets(self):
        # Flikväljare (Tabview) för Physical, Drivetrain, Economics
        self.tabs = ctk.CTkTabview(self, fg_color="transparent")
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        p_tab = self.tabs.add("Physical Specs")
        # Sliders kopplade till on_slider_move
        self.slider_diam = ctk.CTkSlider(p_tab, from_=30, to=150, variable=self.diam_var, command=self.on_slider_move)
        self.slider_diam.pack()

    def on_slider_move(self, *args):
        # 1. Uppdatera domänmodellen direkt
        self.turbine.diameter = self.diam_var.get()
        self.turbine.height = self.height_var.get()
        
        # 2. Meddela huvudfönstret (App) som i sin tur uppdaterar CAD & Analys
        self.on_change()

