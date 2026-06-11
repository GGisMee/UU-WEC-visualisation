# gui/canvas.py
import customtkinter as ctk
import tkinter as tk
import math

class CADCanvas(ctk.CTkFrame):
    def __init__(self, parent, turbine):
        super().__init__(parent, fg_color="#111827", border_width=1, border_color="#2D3748")
        self.turbine = turbine
        self.blade_angle = 0
        
        self.canvas = tk.Canvas(self, bg="#0B132B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Starta animations-tråden/loopen
        self.rotate_loop()

    def update_geometry(self):
        """Ritar om turbinen med nya mått live."""
        self.canvas.delete("all")
        # Ritar linjer, torn (diameter/höjd), måttpilar, etc.
        # Använder self.turbine.diameter och self.turbine.height

    def rotate_loop(self):
        """Loop som animerar bladens rotation."""
        self.blade_angle = (self.blade_angle + 5) % 360
        self.update_geometry()
        self.after(50, self.rotate_loop)