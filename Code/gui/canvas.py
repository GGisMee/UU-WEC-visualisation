# gui/canvas.py
import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
from models.turbine import WindTurbine
from gui.theme import Theme

class CADCanvas(ctk.CTkFrame):
    def __init__(self, parent, turbine: WindTurbine, on_simulate_click: Callable):
        super().__init__(
            parent, 
            fg_color=Theme.BG_SURFACE.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
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
            font=Theme.fonts.SUBTITLE, 
            text_color=Theme.TEXT_MAIN.value
        )
        self.lbl_title.pack(anchor="w", padx=15, pady=(15, 5))

        # Canvas drawing container
        mode_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        self.canvas = tk.Canvas(self, bg=Theme.BLUEPRINT_BG.value[mode_idx], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=15, pady=(5, 5))

        # Action: Commit & Run Button (Fusion Orange)
        self.btn_simulate = ctk.CTkButton(
            self, 
            text="🚀 RUN SIMULATION", 
            font=Theme.fonts.SUBTITLE, 
            fg_color=Theme.ACCENT.value, 
            hover_color=Theme.ACCENT_HOVER.value,
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

        # Extract color indices based on current CustomTkinter appearance mode
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        bg_color = Theme.BLUEPRINT_BG.value[idx]
        grid_color = Theme.BLUEPRINT_GRID.value[idx]
        steel_color = Theme.BLUEPRINT_STEEL.value[idx]
        base_color = Theme.BLUEPRINT_BASE.value[idx]
        blade_color = Theme.BLUEPRINT_BLADE.value[idx]
        text_color = Theme.TEXT_MAIN.value[idx]
        info_color = Theme.INFO.value[idx]

        self.canvas.delete("all")
        self.canvas.configure(bg=bg_color)

        # 1. Technical Grid lines (Spacing: 25px)
        grid_space = 25
        for x in range(0, w, grid_space):
            self.canvas.create_line(x, 0, x, h, fill=grid_color, width=1)
        for y in range(0, h, grid_space):
            self.canvas.create_line(0, y, w, y, fill=grid_color, width=1)

        # 2. Scale math to fit the turbine height/rotor_diameter in the canvas
        max_expected_dim = 160.0
        draw_scale = (h * 0.55) / max_expected_dim

        # Core anchor positions
        ground_y = h - int(50 * self.scale_factor)
        center_x = w // 2

        real_height = self.turbine.height
        real_rotor_diam = self.turbine.rotor_diameter
        real_solidity = self.turbine.solidity

        hub_y = ground_y - int(real_height * draw_scale)
        rotor_r = int((real_rotor_diam / 2) * draw_scale)

        # 3. Check structural stress safety (either forced by simulation or live approximation)
        moment = (real_solidity / 3.0) * (real_rotor_diam / 90.0) * (real_height / 90.0)**2
        is_unsafe = self.is_unsafe or (moment > 2.2)
        
        tower_fill = Theme.DANGER.value[idx] if is_unsafe else steel_color
        tower_outline = Theme.DANGER.value[idx] if is_unsafe else base_color

        # 4. Draw Foundation Base
        base_w = int(40 * self.scale_factor)
        self.canvas.create_polygon(
            center_x - base_w, ground_y,
            center_x + base_w, ground_y,
            center_x + base_w - 5, ground_y - 12,
            center_x - base_w + 5, ground_y - 12,
            fill=base_color, outline=steel_color, width=2
        )

        # 5. Draw Tapered Tower
        tower_base_r = max(5, int((self.turbine.bottom_diameter / 2) * draw_scale * 3.0))
        tower_top_r = max(3, int((self.turbine.top_diameter / 2) * draw_scale * 3.0))
        self.canvas.create_polygon(
            center_x - tower_base_r, ground_y - 12,
            center_x + tower_base_r, ground_y - 12,
            center_x + tower_top_r, hub_y,
            center_x - tower_top_r, hub_y,
            fill=tower_fill, outline=tower_outline, width=2
        )

        # 6. Draw Height Dimension Line (Left Side)
        dim_left_x = center_x - tower_base_r - int(25 * self.scale_factor)
        self.canvas.create_line(dim_left_x, ground_y, dim_left_x, hub_y, fill=info_color, arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_left_x - 5, ground_y, dim_left_x + 5, ground_y, fill=info_color)
        self.canvas.create_line(dim_left_x - 5, hub_y, dim_left_x + 5, hub_y, fill=info_color)
        self.canvas.create_text(
            dim_left_x - int(35 * self.scale_factor), (ground_y + hub_y) // 2, 
            text=f"H = {real_height:.1f}m", fill=text_color, font=(Theme.fonts.family, int(10 * self.scale_factor), "bold")
        )

        # 7. Draw Nacelle (Drivetrain housing)
        nacelle_w = int(22 * self.scale_factor)
        nacelle_h = int(12 * self.scale_factor)
        self.canvas.create_rectangle(
            center_x - nacelle_w, hub_y - nacelle_h,
            center_x + 6, hub_y + 3,
            fill=steel_color, outline=base_color, width=1.5
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
                fill=blade_color, outline=info_color, width=1.5
            )

        # 9. Draw Hub Nose Cone (Highlight in Fusion Orange)
        self.canvas.create_oval(
            center_x - 6, hub_y - 6,
            center_x + 6, hub_y + 6,
            fill=Theme.ACCENT.value[idx], outline=blade_color, width=1.5
        )

        # 10. Draw Rotor Diameter Dimension Line (Right Side)
        dim_right_x = center_x + rotor_r + int(25 * self.scale_factor)
        self.canvas.create_line(dim_right_x, hub_y - rotor_r, dim_right_x, hub_y + rotor_r, fill=info_color, arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_right_x - 5, hub_y - rotor_r, dim_right_x + 5, hub_y - rotor_r, fill=info_color)
        self.canvas.create_line(dim_right_x - 5, hub_y + rotor_r, dim_right_x + 5, hub_y + rotor_r, fill=info_color)
        self.canvas.create_text(
            dim_right_x + int(35 * self.scale_factor), hub_y, 
            text=f"D = {real_rotor_diam:.1f}m", fill=text_color, font=(Theme.fonts.family, int(10 * self.scale_factor), "bold")
        )

        # 11. Safety Alert Banner (Bending Moment overload)
        if is_unsafe:
            self.canvas.create_rectangle(
                center_x - 110, ground_y + 10,
                center_x + 110, ground_y + 35,
                fill=Theme.DANGER.value[idx], outline=blade_color, width=1
            )
            self.canvas.create_text(
                center_x, ground_y + 22,
                text="⚠️ HIGH BENDING MOMENT ALERT", fill="white", font=Theme.fonts.HEADER
            )

        # Update frame styling
        self.configure(fg_color=Theme.BG_SURFACE.value, border_color=Theme.BORDER.value)

    def rotate_loop(self):
        """Blade rotation animation loop."""
        if self.animation_running:
            # Rotor speed depends on rotor_diameter and solidity (smaller/thinner = faster)
            sol = self.turbine.solidity
            rotor_diam = self.turbine.rotor_diameter
            speed = max(1, int(40 - rotor_diam / 4 - sol))
            
            self.blade_angle = (self.blade_angle + speed) % 360
            self.update_geometry()
            
        self.after(50, self.rotate_loop)

    def update_safety_state(self, is_unsafe: bool):
        """Called by parent app upon simulation run completion."""
        self.is_unsafe = is_unsafe
        self.update_geometry()

    def set_animation(self, running: bool):
        self.animation_running = running