import customtkinter as ctk
import tkinter as tk
import math
import datetime
import os

def load_scale_factor():
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        scale_path = os.path.join(dir_path, "scale.txt")
        if os.path.exists(scale_path):
            with open(scale_path, "r") as f:
                return float(f.read().strip())
    except Exception:
        pass
    return 1.35  # Fallback to comfortable scaling

def scaled_font(family, size, weight=None):
    if weight:
        return (family, size, weight)
    return (family, size)


# --- COLOR PALETTE (Cyberpunk/CAD Slate Theme) ---
BG_COLOR = "#0B0F19"         # Deep space dark background
PANEL_BG = "#151F32"         # Dark slate panels
ACCENT_BLUE = "#00D2FF"      # CAD Neon Blue
ACCENT_GREEN = "#00FF87"     # Tech Green
ACCENT_YELLOW = "#FFD000"    # Alert Yellow
ACCENT_RED = "#FF3E6C"       # Danger Red
GRID_COLOR = "#1D2B44"       # Subtle blueprint grid lines
TEXT_MUTED = "#8A99AD"       # Muted text color

class CADBlueprintApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

        # --- WINDOW SETUP ---
        self.title("Wind Turbine CAD Blueprint - Mockup A")
        self.geometry("1100x720")
        self.minsize(1050, 680)
        ctk.set_appearance_mode("dark")
        
        # --- STATE VARIABLES ---
        self.name_var = ctk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = ctk.StringVar(value="199801281234")
        
        self.diam_var = ctk.DoubleVar(value=95.0)
        self.height_var = ctk.DoubleVar(value=105.0)
        self.solidity_var = ctk.DoubleVar(value=3.0)
        
        self.gearbox_var = ctk.StringVar(value="Medium")
        self.generator_var = ctk.StringVar(value="DFIG")

        # Create Layout
        self.create_layout()
        self.recalculate()

    def create_layout(self):
        # Configure grid grid layout: 1 row, 3 columns
        self.grid_columnconfigure(0, weight=3, minsize=320) # Left panel (Inputs)
        self.grid_columnconfigure(1, weight=5, minsize=460) # Center panel (Canvas)
        self.grid_columnconfigure(2, weight=3, minsize=320) # Right panel (Stats)
        self.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # 1. LEFT PANEL: CONTROLS & INPUTS
        # ----------------------------------------------------
        self.left_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.left_frame.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        left_title = ctk.CTkLabel(self.left_frame, text="DESIGN PARAMETERS", font=scaled_font("Montserrat", 16, "bold"), text_color=ACCENT_BLUE)
        left_title.pack(pady=(20, 15), padx=20, anchor="w")

        # Scrollable area for sliders and parameters
        scroll_container = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        scroll_container.grid_columnconfigure(0, weight=1)

        # -- Identity Section --
        sec_id = ctk.CTkFrame(scroll_container, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#1E293B")
        sec_id.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(sec_id, text="Project Identity", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 2))
        
        ctk.CTkLabel(sec_id, text="Designer Name", font=scaled_font("Arial", 11)).pack(anchor="w", padx=12, pady=(5, 0))
        self.ent_name = ctk.CTkEntry(sec_id, textvariable=self.name_var, height=32, fg_color="#1A2436", border_color=GRID_COLOR, font=scaled_font("Arial", 12))
        self.ent_name.pack(fill="x", padx=12, pady=(2, 8))
        self.ent_name.bind("<KeyRelease>", lambda e: self.recalculate())

        ctk.CTkLabel(sec_id, text="SSN (YYYYMMDDXXXX)", font=scaled_font("Arial", 11)).pack(anchor="w", padx=12, pady=(2, 0))
        self.ent_ssn = ctk.CTkEntry(sec_id, textvariable=self.ssn_var, height=32, fg_color="#1A2436", border_color=GRID_COLOR, font=scaled_font("Arial", 12))
        self.ent_ssn.pack(fill="x", padx=12, pady=(2, 12))
        self.ent_ssn.bind("<KeyRelease>", lambda e: self.recalculate())

        # -- Dimensions Section --
        sec_dim = ctk.CTkFrame(scroll_container, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#1E293B")
        sec_dim.pack(fill="x", pady=10, padx=5)
        
        ctk.CTkLabel(sec_dim, text="Physical Dimensions", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 5))

        # Rotor Diameter Slider
        self.lbl_diam = ctk.CTkLabel(sec_dim, text="Rotor Diameter: 95.0 m", font=scaled_font("Arial", 13))
        self.lbl_diam.pack(anchor="w", padx=12, pady=(5, 0))
        self.slider_diam = ctk.CTkSlider(sec_dim, from_=10, to=200, number_of_steps=190, variable=self.diam_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_diam.pack(fill="x", padx=12, pady=(2, 10))

        # Hub Height Slider
        self.lbl_height = ctk.CTkLabel(sec_dim, text="Hub Height: 105.0 m", font=scaled_font("Arial", 13))
        self.lbl_height.pack(anchor="w", padx=12, pady=(5, 0))
        self.slider_height = ctk.CTkSlider(sec_dim, from_=10, to=200, number_of_steps=190, variable=self.height_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_height.pack(fill="x", padx=12, pady=(2, 10))

        # Solidity Slider
        self.lbl_solidity = ctk.CTkLabel(sec_dim, text="Rotor Solidity: 3.0 %", font=scaled_font("Arial", 13))
        self.lbl_solidity.pack(anchor="w", padx=12, pady=(5, 0))
        self.slider_solidity = ctk.CTkSlider(sec_dim, from_=1, to=15, number_of_steps=140, variable=self.solidity_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_solidity.pack(fill="x", padx=12, pady=(2, 12))

        # -- Component Selection Section --
        sec_comp = ctk.CTkFrame(scroll_container, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#1E293B")
        sec_comp.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(sec_comp, text="Powertrain Selection", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 5))

        # Gearbox Selection
        ctk.CTkLabel(sec_comp, text="Gearbox Type", font=scaled_font("Arial", 11)).pack(anchor="w", padx=12, pady=(2, 0))
        self.opt_gearbox = ctk.CTkOptionMenu(sec_comp, values=["None (Direct Drive)", "Medium Ratio", "High-Speed Gearbox"], 
                                              variable=self.gearbox_var, command=self.on_combo_change, font=scaled_font("Arial", 12),
                                              fg_color="#1A2436", button_color="#2E3F59", button_hover_color="#3D5375")
        self.opt_gearbox.pack(fill="x", padx=12, pady=(2, 10))

        # Generator Selection
        ctk.CTkLabel(sec_comp, text="Generator Type", font=scaled_font("Arial", 11)).pack(anchor="w", padx=12, pady=(2, 0))
        self.opt_generator = ctk.CTkOptionMenu(sec_comp, values=["Synchronous", "Asynchronous", "DFIG (Double Fed)"], 
                                                variable=self.generator_var, command=self.on_combo_change, font=scaled_font("Arial", 12),
                                                fg_color="#1A2436", button_color="#2E3F59", button_hover_color="#3D5375")
        self.opt_generator.pack(fill="x", padx=12, pady=(2, 15))


        # ----------------------------------------------------
        # 2. CENTER PANEL: CAD SCHEMA CANVAS
        # ----------------------------------------------------
        self.center_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.center_frame.grid(row=0, column=1, padx=10, pady=15, sticky="nsew")
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(1, weight=1)

        # Canvas Header / Control info
        header_bar = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        header_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))
        
        ctk.CTkLabel(header_bar, text="REAL-TIME CAD SCHEMATIC", font=scaled_font("Montserrat", 16, "bold"), text_color="white").pack(side="left")
        self.lbl_scale_info = ctk.CTkLabel(header_bar, text="Scale: Auto-adaptive", font=scaled_font("Arial", 11), text_color=TEXT_MUTED)
        self.lbl_scale_info.pack(side="right", pady=3)

        # Interactive Canvas
        self.canvas_frame = tk.Frame(self.center_frame, bg=BG_COLOR)
        self.canvas_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_turbine())

        # Base warning/status label at canvas bottom
        self.lbl_cad_warn = ctk.CTkLabel(self.center_frame, text="✓ Structure parameters within safe operational limits", 
                                         font=scaled_font("Arial", 12, "bold"), text_color=ACCENT_GREEN, height=36, fg_color="#102A24", corner_radius=8)
        self.lbl_cad_warn.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))


        # ----------------------------------------------------
        # 3. RIGHT PANEL: STATISTICS & METRICS
        # ----------------------------------------------------
        self.right_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.right_frame.grid(row=0, column=2, padx=(10, 15), pady=15, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        right_title = ctk.CTkLabel(self.right_frame, text="SIMULATION METRICS", font=scaled_font("Montserrat", 16, "bold"), text_color=ACCENT_BLUE)
        right_title.pack(pady=(20, 15), padx=20, anchor="w")

        # Scrollable area for output cards
        out_container = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        out_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Output Cards
        self.card_power = self.create_stat_card(out_container, "RATED POWER OUTPUT", "0.0 kW", ACCENT_BLUE)
        self.card_energy = self.create_stat_card(out_container, "ANNUAL ENERGY GENERATION", "0.0 MWh", ACCENT_GREEN)
        self.card_aero = self.create_stat_card(out_container, "AERODYNAMIC THRUST FORCE", "0.0 kN", "white")
        self.card_storm = self.create_stat_card(out_container, "STORM LOAD (@60 m/s)", "0.0 kN", ACCENT_YELLOW)
        
        # Wall Thickness Comparisons
        self.thickness_frame = ctk.CTkFrame(out_container, fg_color="#0F172A", corner_radius=10, border_width=1, border_color=GRID_COLOR)
        self.thickness_frame.pack(fill="x", pady=8, padx=5)
        
        ctk.CTkLabel(self.thickness_frame, text="TOWER WALL THICKNESS REQ.", font=scaled_font("Arial", 11, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 2))
        
        self.lbl_thick_op = ctk.CTkLabel(self.thickness_frame, text="Operating Loads: 0.0 mm", font=scaled_font("Arial", 13, "bold"), text_color="white")
        self.lbl_thick_op.pack(anchor="w", padx=12, pady=2)
        
        self.lbl_thick_storm = ctk.CTkLabel(self.thickness_frame, text="Storm Survival: 0.0 mm", font=scaled_font("Arial", 13, "bold"), text_color=ACCENT_YELLOW)
        self.lbl_thick_storm.pack(anchor="w", padx=12, pady=(2, 8))

        # Financial Quick Indicator
        self.fin_frame = ctk.CTkFrame(out_container, fg_color="#102A20", corner_radius=10, border_width=1, border_color="#164A35")
        self.fin_frame.pack(fill="x", pady=8, padx=5)
        
        ctk.CTkLabel(self.fin_frame, text="ESTIMATED MARGIN & PROFITS", font=scaled_font("Arial", 11, "bold"), text_color="#A7F3D0").pack(anchor="w", padx=12, pady=(8, 2))
        
        self.lbl_fin_margin = ctk.CTkLabel(self.fin_frame, text="0.0% Profit Margin", font=scaled_font("Arial", 18, "bold"), text_color=ACCENT_GREEN)
        self.lbl_fin_margin.pack(anchor="w", padx=12, pady=1)
        
        self.lbl_fin_profits = ctk.CTkLabel(self.fin_frame, text="Lifetime Profits: 0.0 k€", font=scaled_font("Arial", 12), text_color="#D1FAE5")
        self.lbl_fin_profits.pack(anchor="w", padx=12, pady=(1, 8))

    def create_stat_card(self, parent, label_text, init_value, value_color):
        card = ctk.CTkFrame(parent, fg_color="#0F172A", corner_radius=10, border_width=1, border_color=GRID_COLOR)
        card.pack(fill="x", pady=5, padx=5)
        
        lbl = ctk.CTkLabel(card, text=label_text, font=scaled_font("Arial", 11, "bold"), text_color=TEXT_MUTED)
        lbl.pack(anchor="w", padx=12, pady=(8, 2))
        
        val_lbl = ctk.CTkLabel(card, text=init_value, font=scaled_font("Arial", 20, "bold"), text_color=value_color)
        val_lbl.pack(anchor="w", padx=12, pady=(0, 8))
        
        return val_lbl

    def on_slider_change(self, value):
        # Update sliders label readings
        self.lbl_diam.configure(text=f"Rotor Diameter: {self.diam_var.get():.1f} m")
        self.lbl_height.configure(text=f"Hub Height: {self.height_var.get():.1f} m")
        self.lbl_solidity.configure(text=f"Rotor Solidity: {self.solidity_var.get():.1f} %")
        self.recalculate()

    def on_combo_change(self, choice):
        self.recalculate()

    def recalculate(self):
        """
        Runs intermediate mocked model calculation for the UI simulation.
        Ensures graceful SSN inputs.
        """
        # Parse identity
        ssn = self.ssn_var.get().strip()
        name = self.name_var.get().strip()
        
        # Validations
        if len(ssn) != 12 or not ssn.isdigit():
            # Gracefully wait and keep UI alive with default parameters derived from 199801281234
            m_factor, d_factor, y_factor, pin_val = 1, 28, 1998, 1234
        else:
            try:
                y_factor = int(ssn[0:4])
                m_factor = int(ssn[4:6])
                d_factor = int(ssn[6:8])
                pin_val = int(ssn[8:12])
            except ValueError:
                m_factor, d_factor, y_factor, pin_val = 1, 28, 1998, 1234
                
        # Calculations based on formulas
        diam = self.diam_var.get()
        height = self.height_var.get()
        solidity = self.solidity_var.get()
        
        # Intermediate params
        k_factor = (11 + m_factor) / 10
        avg_U10 = (6 + d_factor / 10) - height / 50
        roughness = max(1, m_factor * d_factor)
        downtime = abs(2000 - y_factor) + 1
        capture_efficiency = max(0.2, min(0.59, 0.54 - m_factor / 100))
        efficiency_drivetrain = max(0.5, min(0.98, 0.94 - (pin_val - round(pin_val, -2)) / 400))
        
        z0 = roughness / 1000
        # Protect against log(<=0)
        h_ratio = max(1.1, height / z0)
        ten_ratio = max(1.1, 10 / z0)
        wind_nacelle = max(2.0, avg_U10 * math.log(h_ratio) / math.log(ten_ratio))
        
        # Betz Law cap calculations
        swept_area = math.pi * (diam / 2) ** 2
        rated_speed = max(6.0, wind_nacelle * 1.5) # approximated rated speed
        cut_in = max(2.0, rated_speed * 0.25)
        cut_out = min(30.0, rated_speed * 2.2)
        
        rated_power = 0.62 * (rated_speed ** 3) * swept_area * capture_efficiency * efficiency_drivetrain / 1000
        
        # Adjust calculations for Gearbox/Generator selection
        gearbox = self.gearbox_var.get()
        generator = self.generator_var.get()
        
        # Adjust drivetrain efficiency depending on selection
        # (Direct drive has high efficiency but high capex. High speed has gearbox loss).
        efficiency_mod = 0.0
        capex_mod = 0.0
        if gearbox == "None (Direct Drive)":
            efficiency_mod += 0.03 # direct drive is slightly more efficient
            capex_mod += 1200 # but costs significantly more
        elif gearbox == "High-Speed Gearbox":
            efficiency_mod -= 0.02 # losses in gearbox
            capex_mod += 200 # minor gearbox cost
            
        if generator == "DFIG (Double Fed)":
            capex_mod *= 1.2 # 2x generator cost
            efficiency_mod -= 0.005
        
        final_efficiency = max(0.5, min(0.99, efficiency_drivetrain + efficiency_mod))
        rated_power = rated_power * (final_efficiency / efficiency_drivetrain)
        
        # Energy production model
        availability = (100 - downtime) / 100
        hours_active = 8760 * availability * 0.42 # capacity factor mockup
        generated_energy = rated_power * hours_active / 1000 # MWh
        
        # Mechanical Loads
        # C_T=8/9, density=1.2
        aero_load = 0.5 * 1.2 * (8/9) * swept_area * (rated_speed ** 2) / 1000 # kN
        
        # Solidity slider affects storm load
        storm_load = 0.5 * 1.2 * 1.5 * (solidity / 100) * swept_area * (60 ** 2) / 1000 # kN
        
        # Wall thicknesses (in m) - multiplied by 1000 for mm
        wall_thick_op = (aero_load * height / (math.pi * ((height/40) ** 2) * 160) * 2) * 1000
        wall_thick_storm = (storm_load * height / (math.pi * ((height/40) ** 2) * 160) * 2) * 1000
        
        # Economics
        wo_param = 6 + m_factor / 6
        turbine_cost = 900 * ((wo_param / 7.5) ** 3) * ((diam / 90) ** 3.5)
        drivetrain_cost = 800 * (wo_param / 7) * (rated_power / 1000 / 3) * (diam / 90)
        tower_cost = 700 * ((wo_param / 7) ** 2.5) * ((diam / 90) ** 2) * ((height / 90) ** 2) + 300
        foundation_cost = 300 * math.sqrt((diam / 90) * (height / 100))
        
        capex = turbine_cost + drivetrain_cost + tower_cost + foundation_cost + capex_mod
        installation = 3500 # k€
        total_capex = capex + installation
        
        # OPEX
        om = 600 * (rated_power / 1000 / 84) + 100 * math.sqrt(rated_power / 1000 / 84) + 360/28 + 200 * (rated_power / 1000 / 84)
        
        # Income
        electricity_price = 29 # €/MWh
        green_cert = 1
        annual_income = generated_energy * 0.95 * (electricity_price + green_cert) / 1000 # k€
        savings = annual_income - om
        
        # NPV and Margin
        interest = 0.03
        inflation = 0.02
        lifetime = 22
        k_fact = (1 + inflation) / (1 + interest)
        npv = savings * (k_fact * (1 - k_fact ** lifetime)) / (1 - k_fact)
        financial_costs = 0.07 * total_capex
        profits = npv - total_capex - financial_costs
        margin = profits / total_capex
        
        # Update UI text
        self.card_power.configure(text=f"{rated_power:.1f} kW")
        self.card_energy.configure(text=f"{generated_energy:.1f} MWh")
        self.card_aero.configure(text=f"{aero_load:.1f} kN")
        self.card_storm.configure(text=f"{storm_load:.1f} kN")
        
        self.lbl_thick_op.configure(text=f"Operating Loads: {wall_thick_op:.1f} mm")
        self.lbl_thick_storm.configure(text=f"Storm Survival: {wall_thick_storm:.1f} mm")
        
        self.lbl_fin_margin.configure(text=f"{margin * 100:.1f}% Profit Margin")
        self.lbl_fin_profits.configure(text=f"Lifetime Profits: {profits:.1f} k€")
        
        # Set colors depending on financial margin and mechanical safety
        if margin < 0.0:
            self.lbl_fin_margin.configure(text_color=ACCENT_RED)
            self.fin_frame.configure(fg_color="#3B1C22", border_color="#5C2630")
        elif margin < 0.2:
            self.lbl_fin_margin.configure(text_color=ACCENT_YELLOW)
            self.fin_frame.configure(fg_color="#302715", border_color="#4E3E20")
        else:
            self.lbl_fin_margin.configure(text_color=ACCENT_GREEN)
            self.fin_frame.configure(fg_color="#102A20", border_color="#164A35")
            
        # Structure status warning
        # If wall thickness is excessive or height/diameter ratio is physically weird, warn user
        ratio = height / diam
        if ratio > 4.0:
            self.lbl_cad_warn.configure(text="⚠ Warning: Aspect ratio (Height/Diam) is very thin! Tower buckle risk high.", text_color=ACCENT_RED, fg_color="#3B1C22")
            self.structure_status = "unsafe"
        elif ratio < 0.4:
            self.lbl_cad_warn.configure(text="⚠ Warning: Rotor diameter too large for tower height. Ground clearance risk!", text_color=ACCENT_RED, fg_color="#3B1C22")
            self.structure_status = "clearance_risk"
        elif wall_thick_storm > 150.0:
            self.lbl_cad_warn.configure(text="⚠ Warning: Required storm thickness exceeds 150mm! Structural weight inefficient.", text_color=ACCENT_YELLOW, fg_color="#302715")
            self.structure_status = "inefficient"
        else:
            self.lbl_cad_warn.configure(text="✓ Structure parameters within safe operational limits", text_color=ACCENT_GREEN, fg_color="#102A24")
            self.structure_status = "safe"
            
        # Draw the updated CAD model
        self.draw_turbine()

    def draw_turbine(self):
        """
        Draws the schematic representation of the wind turbine on the Canvas.
        """
        if not hasattr(self, 'canvas') or self.canvas.winfo_width() < 10:
            return
            
        # Clean canvas
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Scale factor for drawings
        scale = self.scale_factor
        
        # 1. DRAW BLUEPRINT GRID
        grid_size = int(40 * scale)
        for x in range(0, w, grid_size):
            self.canvas.create_line(x, 0, x, h, fill=GRID_COLOR, width=1 * scale)
        for y in range(0, h, grid_size):
            self.canvas.create_line(0, y, w, y, fill=GRID_COLOR, width=1 * scale)
            
        # Draw coordinate labels in bottom-left
        self.canvas.create_text(int(25 * scale), h - int(15 * scale), text="0,0 (ref)", fill=TEXT_MUTED, font=("Consolas", int(9 * scale)))
        self.canvas.create_line(int(15 * scale), h - int(30 * scale), int(15 * scale), h - int(15 * scale), arrow="first", fill=ACCENT_BLUE, width=1.5 * scale)
        self.canvas.create_line(int(15 * scale), h - int(15 * scale), int(30 * scale), h - int(15 * scale), arrow="last", fill=ACCENT_BLUE, width=1.5 * scale)
        
        # 2. CALCULATE SCALE
        # We map dimensions to pixels
        # Real-world: diam max ~200m, height max ~200m. Overall bounding height ~300m
        # Let's anchor the ground line at 85% of canvas height
        ground_y = int(h * 0.85)
        center_x = int(w * 0.5)
        
        # Set max visual height to represent 260m
        max_real_height = 280.0
        pixels_per_meter = (h * 0.7) / max_real_height
        
        real_height = self.height_var.get()
        real_diam = self.diam_var.get()
        
        pixel_height = real_height * pixels_per_meter
        pixel_radius = (real_diam / 2) * pixels_per_meter
        
        hub_y = ground_y - pixel_height
        
        # 3. DRAW FOUNDATION (Concrete slab)
        foundation_w = max(int(40 * scale), int(pixel_radius * 0.5))
        foundation_h = int(20 * scale)
        self.canvas.create_rectangle(center_x - foundation_w, ground_y, center_x + foundation_w, ground_y + foundation_h,
                                     fill="#1E293B", outline=ACCENT_BLUE, width=1.5 * scale)
        
        # 4. DRAW TOWER
        # Width scales with height and rotor diameter
        base_w = max(int(10 * scale), int(real_height / 12 * pixels_per_meter))
        top_w = max(int(5 * scale), int(real_height / 25 * pixels_per_meter))
        
        # Color changes to Red if status is unsafe
        tower_outline = ACCENT_BLUE
        tower_fill = "#151F32"
        
        if hasattr(self, 'structure_status'):
            if self.structure_status == "unsafe":
                tower_outline = ACCENT_RED
                tower_fill = "#3B1D25"
            elif self.structure_status == "inefficient":
                tower_outline = ACCENT_YELLOW
                tower_fill = "#2E241E"
                
        tower_poly = [
            center_x - base_w, ground_y,
            center_x - top_w, hub_y,
            center_x + top_w, hub_y,
            center_x + base_w, ground_y
        ]
        
        self.canvas.create_polygon(tower_poly, fill=tower_fill, outline=tower_outline, width=2 * scale)
        
        # 5. DRAW NACELLE & HUB
        nacelle_w = max(int(18 * scale), int(real_diam * 0.08 * pixels_per_meter))
        nacelle_h = max(int(10 * scale), int(real_diam * 0.04 * pixels_per_meter))
        
        self.canvas.create_rectangle(center_x - nacelle_w, hub_y - nacelle_h, center_x, hub_y,
                                     fill="#29354F", outline=ACCENT_BLUE, width=1.5 * scale)
        
        hub_r = max(int(4 * scale), int(real_diam * 0.025 * pixels_per_meter))
        self.canvas.create_oval(center_x - hub_r, hub_y - hub_r, center_x + hub_r, hub_y + hub_r,
                                fill=ACCENT_BLUE, outline="white", width=1.5 * scale)
        
        # 6. DRAW BLADES (3 blades at static 120-degree separations for mockup)
        angles = [0, 120, 240]
        # Make one blade point straight up (0 degree = -90 in tk coordinates)
        for angle in angles:
            rad = math.radians(angle - 90)
            end_x = center_x + pixel_radius * math.cos(rad)
            end_y = hub_y + pixel_radius * math.sin(rad)
            
            # Thick root, thin tip
            perp_rad = math.radians(angle) # perpendicular for width
            width_offset = max(int(2 * scale), int(real_diam * 0.015 * pixels_per_meter))
            
            pt1_x = center_x + width_offset * math.cos(perp_rad)
            pt1_y = hub_y + width_offset * math.sin(perp_rad)
            pt2_x = center_x - width_offset * math.cos(perp_rad)
            pt2_y = hub_y - width_offset * math.sin(perp_rad)
            
            self.canvas.create_polygon([pt1_x, pt1_y, end_x, end_y, pt2_x, pt2_y], 
                                         fill="#2C3D5E", outline="white", width=1 * scale)
            
        # Draw rotation indicator circle
        self.canvas.create_oval(center_x - pixel_radius, hub_y - pixel_radius, center_x + pixel_radius, hub_y + pixel_radius,
                                outline="#1E293B", dash=(3, 5), width=1 * scale)
        
        # 7. DRAW GROUND LINE
        self.canvas.create_line(0, ground_y, w, ground_y, fill=TEXT_MUTED, width=2 * scale)
        
        # 8. DIMENSION ANNOTATIONS
        # Hub Height Label
        self.canvas.create_line(center_x - base_w - int(40 * scale), ground_y, center_x - base_w - int(40 * scale), hub_y, fill=ACCENT_BLUE, arrow="both", width=1.5 * scale)
        self.canvas.create_line(center_x - base_w - int(50 * scale), ground_y, center_x - base_w - int(30 * scale), ground_y, fill=ACCENT_BLUE, width=1.5 * scale)
        self.canvas.create_line(center_x - base_w - int(50 * scale), hub_y, center_x - base_w - int(30 * scale), hub_y, fill=ACCENT_BLUE, width=1.5 * scale)
        self.canvas.create_text(center_x - base_w - int(85 * scale), (ground_y + hub_y) // 2, text=f"H = {real_height:.1f}m", fill="white", font=("Arial", int(11 * scale), "bold"))
        
        # Rotor Diameter Label (on the right)
        right_dim_x = center_x + pixel_radius + int(30 * scale)
        if right_dim_x < w - int(20 * scale):
            self.canvas.create_line(right_dim_x, hub_y - pixel_radius, right_dim_x, hub_y + pixel_radius, fill=ACCENT_BLUE, arrow="both", width=1.5 * scale)
            self.canvas.create_line(right_dim_x - int(10 * scale), hub_y - pixel_radius, right_dim_x + int(10 * scale), hub_y - pixel_radius, fill=ACCENT_BLUE, width=1.5 * scale)
            self.canvas.create_line(right_dim_x - int(10 * scale), hub_y + pixel_radius, right_dim_x + int(10 * scale), hub_y + pixel_radius, fill=ACCENT_BLUE, width=1.5 * scale)
            self.canvas.create_text(right_dim_x + int(45 * scale), hub_y, text=f"D = {real_diam:.1f}m", fill="white", font=("Arial", int(11 * scale), "bold"))

        # 9. ROTATION ANIMATION (Hinting it is live)
        # Static indicators are fine, but adding a neat compass/crosshair completes the CAD blueprint look
        self.canvas.create_line(center_x, hub_y - int(10 * scale), center_x, hub_y + int(10 * scale), fill="white", width=1 * scale)
        self.canvas.create_line(center_x - int(10 * scale), hub_y, center_x + int(10 * scale), hub_y, fill="white", width=1 * scale)

if __name__ == "__main__":
    app = CADBlueprintApp()
    app.mainloop()
