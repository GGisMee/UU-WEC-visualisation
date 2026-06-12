# gui/canvas.py
import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
from models.turbine import WindTurbine
from gui.theme import FusionTheme

class CADCanvas(ctk.CTkFrame):
    def __init__(self, parent, turbine: WindTurbine, on_simulate_click: Callable):
        super().__init__(
            parent, 
            fg_color=FusionTheme.BG_SURFACE.value, 
            border_width=1, 
            border_color=FusionTheme.BORDER.value
        )
        self.turbine = turbine
        self.blade_angle = 0.0
        self.animation_running = True
        self.is_unsafe = False
        
        # Get parent scale factor if set
        self.scale_factor = getattr(parent, "scale_factor", 1.0)

        # Title Label
        self.lbl_title = ctk.CTkLabel(
            self, 
            text="LIVE CAD BLUEPRINT SCHEMATIC", 
            font=("Montserrat", 13, "bold"), 
            text_color=FusionTheme.TEXT_MAIN.value
        )
        self.lbl_title.pack(anchor="w", padx=15, pady=(15, 5))

        # Canvas drawing container
        # Background: `#0B132B` (blueprint dark blue)
        self.canvas = tk.Canvas(self, bg="#0B132B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=15, pady=(5, 5))

        # Action: Commit & Run Button (Fusion Orange)
        self.btn_simulate = ctk.CTkButton(
            self, 
            text="🚀 RUN SIMULATION", 
            font=("Arial", 13, "bold"), 
            fg_color=FusionTheme.ACCENT.value, 
            hover_color="#CC6200",
            text_color="white",
            height=36,
            command=on_simulate_click
        )
        self.btn_simulate.pack(fill="x", padx=15, pady=(5, 15))

        # Bind resize event to redraw canvas dynamically
        self.canvas.bind("<Configure>", lambda e: self.update_geometry())

        # Start animation loop
        self.rotate_loop()

    def update_geometry(self):
        """Renders/Redraws the entire wind turbine blueprint schematic."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return  # Canvas is not yet fully initialized/placed

        self.canvas.delete("all")

        # 1. Technical Grid lines (Spacing: 25px)
        grid_space = 25
        grid_color = "#121D33"
        for x in range(0, w, grid_space):
            self.canvas.create_line(x, 0, x, h, fill=grid_color, width=1)
        for y in range(0, h, grid_space):
            self.canvas.create_line(0, y, w, y, fill=grid_color, width=1)

        # 2. Scale math to fit the turbine height/diameter in the canvas
        # Maximum expected turbine height/diameter is ~160m
        max_expected_dim = 160.0
        draw_scale = (h * 0.55) / max_expected_dim

        # Core anchor positions
        ground_y = h - int(50 * self.scale_factor)
        center_x = w // 2

        real_height = self.turbine.height
        real_diam = self.turbine.diameter
        real_solidity = self.turbine.solidity

        hub_y = ground_y - int(real_height * draw_scale)
        rotor_r = int((real_diam / 2) * draw_scale)

        # 3. Check structural stress safety (either forced by simulation or live approximation)
        # solidity * diameter * wind shear moment
        moment = (real_solidity / 3.0) * (real_diam / 90.0) * (real_height / 90.0)**2
        is_unsafe = self.is_unsafe or (moment > 2.2)
        
        tower_color = FusionTheme.DANGER.value[1] if is_unsafe else "#334155"
        tower_outline = FusionTheme.DANGER.value[1] if is_unsafe else "#64748B"

        # 4. Draw Foundation Base
        base_w = int(40 * self.scale_factor)
        self.canvas.create_polygon(
            center_x - base_w, ground_y,
            center_x + base_w, ground_y,
            center_x + base_w - 5, ground_y - 12,
            center_x - base_w + 5, ground_y - 12,
            fill="#1E293B", outline="#475569", width=2
        )

        # 5. Draw Tapered Tower
        tower_base_r = max(5, int(15 * (real_height / 100)))
        tower_top_r = max(3, int(6 * (real_height / 100)))
        self.canvas.create_polygon(
            center_x - tower_base_r, ground_y - 12,
            center_x + tower_base_r, ground_y - 12,
            center_x + tower_top_r, hub_y,
            center_x - tower_top_r, hub_y,
            fill=tower_color, outline=tower_outline, width=2
        )

        # 6. Draw Height Dimension Line (Left Side)
        dim_left_x = center_x - tower_base_r - int(25 * self.scale_factor)
        self.canvas.create_line(dim_left_x, ground_y, dim_left_x, hub_y, fill=FusionTheme.INFO.value[1], arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_left_x - 5, ground_y, dim_left_x + 5, ground_y, fill=FusionTheme.INFO.value[1])
        self.canvas.create_line(dim_left_x - 5, hub_y, dim_left_x + 5, hub_y, fill=FusionTheme.INFO.value[1])
        self.canvas.create_text(
            dim_left_x - int(35 * self.scale_factor), (ground_y + hub_y) // 2, 
            text=f"H = {real_height:.1f}m", fill=FusionTheme.TEXT_MAIN.value[1], font=("Arial", int(10 * self.scale_factor), "bold")
        )

        # 7. Draw Nacelle (Drivetrain housing)
        nacelle_w = int(22 * self.scale_factor)
        nacelle_h = int(12 * self.scale_factor)
        self.canvas.create_rectangle(
            center_x - nacelle_w, hub_y - nacelle_h,
            center_x + 6, hub_y + 3,
            fill="#475569", outline="#E2E8F0", width=1.5
        )

        # 8. Draw Rotating Blades
        num_blades = self.turbine.blades
        blade_base_w = int(4 * (real_solidity / 3.0))

        for i in range(num_blades):
            angle_deg = self.blade_angle + (i * (360.0 / num_blades))
            angle_rad = math.radians(angle_deg)
            
            # Blade tip coordinates
            tip_x = center_x + rotor_r * math.sin(angle_rad)
            tip_y = hub_y - rotor_r * math.cos(angle_rad)
            
            # Orthogonal vector coordinates for base width
            base_rad = angle_rad + math.pi/2
            bx = blade_base_w * math.sin(base_rad)
            by = blade_base_w * math.cos(base_rad)
            
            self.canvas.create_polygon(
                center_x - bx, hub_y + by,
                center_x + bx, hub_y - by,
                tip_x, tip_y,
                fill="#F8FAFC", outline=FusionTheme.INFO.value[1], width=1.5
            )

        # 9. Draw Hub Nose Cone (Highlight in Fusion Orange)
        self.canvas.create_oval(
            center_x - 6, hub_y - 6,
            center_x + 6, hub_y + 6,
            fill=FusionTheme.ACCENT.value[1], outline="#FFFFFF", width=1.5
        )

        # 10. Draw Rotor Diameter Dimension Line (Right Side)
        dim_right_x = center_x + rotor_r + int(25 * self.scale_factor)
        self.canvas.create_line(dim_right_x, hub_y - rotor_r, dim_right_x, hub_y + rotor_r, fill=FusionTheme.INFO.value[1], arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_right_x - 5, hub_y - rotor_r, dim_right_x + 5, hub_y - rotor_r, fill=FusionTheme.INFO.value[1])
        self.canvas.create_line(dim_right_x - 5, hub_y + rotor_r, dim_right_x + 5, hub_y + rotor_r, fill=FusionTheme.INFO.value[1])
        self.canvas.create_text(
            dim_right_x + int(35 * self.scale_factor), hub_y, 
            text=f"D = {real_diam:.1f}m", fill=FusionTheme.TEXT_MAIN.value[1], font=("Arial", int(10 * self.scale_factor), "bold")
        )

        # 11. Safety Alert Banner (Bending Moment overload)
        if is_unsafe:
            self.canvas.create_rectangle(
                center_x - 110, ground_y + 10,
                center_x + 110, ground_y + 35,
                fill=FusionTheme.DANGER.value[1], outline="#FFFFFF", width=1
            )
            self.canvas.create_text(
                center_x, ground_y + 22,
                text="⚠️ HIGH BENDING MOMENT ALERT", fill="white", font=("Arial", 9, "bold")
            )

    def rotate_loop(self):
        """Blade rotation animation loop."""
        if self.animation_running:
            # Rotor speed depends on diameter and solidity (smaller/thinner = faster)
            sol = self.turbine.solidity
            diam = self.turbine.diameter
            speed = max(1, int(40 - diam / 4 - sol))
            
            self.blade_angle = (self.blade_angle + speed) % 360
            self.update_geometry()
            
        self.after(50, self.rotate_loop)

    def update_safety_state(self, is_unsafe: bool):
        """Called by parent app upon simulation run completion."""
        self.is_unsafe = is_unsafe
        self.update_geometry()

    def set_animation(self, running: bool):
        self.animation_running = running