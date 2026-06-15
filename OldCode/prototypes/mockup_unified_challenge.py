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

# --- COLOR PALETTE (Neon Cyber-Slate & Tech Orange) ---
BG_COLOR = "#080D16"         # Dark space background
PANEL_BG = "#111827"         # Slate panels
CARD_BG = "#1A2238"          # Dark blue-slate card highlights
CARD_BORDER = "#2D3748"      # Card stroke
ACCENT_BLUE = "#00D2FF"      # Electric Cyan
ACCENT_ORANGE = "#FF7A00"    # Tech Orange
ACCENT_YELLOW = "#FFD000"    # Alert Yellow
ACCENT_GREEN = "#10B981"     # Emerald Green
ACCENT_RED = "#FF3E6C"       # Cyber Red
TEXT_MAIN = "#F9FAFB"        # Core text
TEXT_MUTED = "#9CA3AF"       # Subtitle text


class UnifiedChallengeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

        # --- WINDOW SETUP ---
        self.title("Wind Power Simulator - Challenge Mode")
        # Optimized size for 3 panels + header
        self.geometry("1200x750")

        self.resizable(True, True)
        self.configure(fg_color=BG_COLOR)
        ctk.set_appearance_mode("dark")

        # --- STATE VARIABLES ---
        self.current_mission = "Free Play Sandbox"
        self.runs_remaining = 6
        self.simulation_out_of_date = True
        self.last_simulated_results = None
        self.blade_angle = 0.0
        self.animation_running = True

        # Input variables
        self.name_var = tk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = tk.StringVar(value="199801281234")
        self.diam_var = tk.DoubleVar(value=95.0)
        self.height_var = tk.DoubleVar(value=105.0)
        self.solidity_var = tk.DoubleVar(value=3.5)
        self.blades_var = tk.StringVar(value="3 Blades")
        self.gearbox_var = tk.StringVar(value="Medium-Speed")
        self.generator_var = tk.StringVar(value="DFIG")
        self.price_var = tk.DoubleVar(value=30.0)
        self.lifetime_var = tk.IntVar(value=22)
        self.inflation_var = tk.DoubleVar(value=2.0)
        self.interest_var = tk.DoubleVar(value=3.0)

        # Set tracer for SSN to validate birthdate integration
        self.ssn_var.trace_add("write", self.on_ssn_change)

        # Draw GUI Layout
        self.create_layout()

        # Start visual turbine rotation animation
        self.rotate_blades_loop()
        
        # Initial CAD render
        self.update_cad_drawing()

    def create_layout(self):
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Core Workspace
        self.grid_columnconfigure(0, weight=0)  # Left panel (Console)
        self.grid_columnconfigure(1, weight=1)  # Center panel (CAD)
        self.grid_columnconfigure(2, weight=0)  # Right panel (Analytics)

        # ==========================================
        # 1. HEADER BAR
        # ==========================================
        self.header_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, border_width=1, border_color=CARD_BORDER)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        # Left Info: Mission Selector & Description
        left_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        ctk.CTkLabel(left_header, text="MISSION / CHALLENGE", font=("Montserrat", 10, "bold"), text_color=ACCENT_ORANGE).pack(anchor="w")
        self.mission_menu = ctk.CTkOptionMenu(
            left_header, 
            values=["Free Play Sandbox", "The Arctic Gale", "The Gentle Breeze"],
            command=self.on_mission_change,
            fg_color=CARD_BG,
            button_color=CARD_BORDER,
            button_hover_color=ACCENT_BLUE,
            width=200,
            height=28
        )
        self.mission_menu.pack(anchor="w", pady=(2, 5))
        
        self.lbl_mission_desc = ctk.CTkLabel(
            left_header, 
            text="Free Sandbox: Explore turbine sizes and parameters with unlimited simulation runs.",
            font=("Arial", 11),
            text_color=TEXT_MUTED,
            justify="left"
        )
        self.lbl_mission_desc.pack(anchor="w")

        # Right Info: Scorecards & R&D Budget
        right_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_header.grid(row=0, column=1, sticky="e", padx=15, pady=10)

        # Mission Status Card
        self.status_card = ctk.CTkFrame(right_header, fg_color=CARD_BG, width=150, height=55, border_width=1, border_color=CARD_BORDER)
        self.status_card.pack(side="left", padx=5)
        self.status_card.pack_propagate(False)
        ctk.CTkLabel(self.status_card, text="MISSION STATUS", font=("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(4, 0))
        self.lbl_mission_status = ctk.CTkLabel(self.status_card, text="SANDBOX", font=("Arial", 14, "bold"), text_color=ACCENT_BLUE)
        self.lbl_mission_status.pack()

        # Runs Card
        self.runs_card = ctk.CTkFrame(right_header, fg_color=CARD_BG, width=130, height=55, border_width=1, border_color=CARD_BORDER)
        self.runs_card.pack(side="left", padx=5)
        self.runs_card.pack_propagate(False)
        ctk.CTkLabel(self.runs_card, text="R&D RUNS REMAINING", font=("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(4, 0))
        self.lbl_runs = ctk.CTkLabel(self.runs_card, text="∞ / ∞", font=("Arial", 14, "bold"), text_color=ACCENT_GREEN)
        self.lbl_runs.pack()

        # Scorecard Grade
        self.grade_card = ctk.CTkFrame(right_header, fg_color=CARD_BG, width=100, height=55, border_width=1, border_color=CARD_BORDER)
        self.grade_card.pack(side="left", padx=5)
        self.grade_card.pack_propagate(False)
        ctk.CTkLabel(self.grade_card, text="DESIGN GRADE", font=("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(4, 0))
        self.lbl_grade = ctk.CTkLabel(self.grade_card, text="N/A", font=("Arial", 14, "bold"), text_color=TEXT_MUTED)
        self.lbl_grade.pack()

        # Scorecard Profit
        self.profit_card = ctk.CTkFrame(right_header, fg_color=CARD_BG, width=140, height=55, border_width=1, border_color=CARD_BORDER)
        self.profit_card.pack(side="left", padx=5)
        self.profit_card.pack_propagate(False)
        ctk.CTkLabel(self.profit_card, text="LIFETIME PROFIT", font=("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(4, 0))
        self.lbl_profit = ctk.CTkLabel(self.profit_card, text="- k€", font=("Arial", 14, "bold"), text_color=TEXT_MUTED)
        self.lbl_profit.pack()

        # ==========================================
        # 2. LEFT PANEL (CONTROL CONSOLE)
        # ==========================================
        self.inputs_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, width=320, border_width=1, border_color=CARD_BORDER)
        self.inputs_frame.grid(row=1, column=0, sticky="nsw", padx=(10, 5), pady=(5, 10))
        self.inputs_frame.pack_propagate(False)

        ctk.CTkLabel(self.inputs_frame, text="CONTROL CONSOLE", font=("Montserrat", 13, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Tabs for inputs
        self.tab_widget = ctk.CTkTabview(self.inputs_frame, fg_color="transparent", text_color="white")

        self.tab_widget.pack(fill="both", expand=True, padx=5, pady=5)
        self.tab_widget.add("Physical Specs")
        self.tab_widget.add("Drivetrain")
        self.tab_widget.add("Economics")

        # --- Tab 1: Physical Setup ---
        p_tab = self.tab_widget.tab("Physical Specs")
        
        # Project Identity fields
        ctk.CTkLabel(p_tab, text="Designer Name", font=("Arial", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=5, pady=(5, 0))
        self.ent_name = ctk.CTkEntry(p_tab, textvariable=self.name_var, height=26, fg_color="#182030", border_color=CARD_BORDER)
        self.ent_name.pack(fill="x", padx=5, pady=(0, 5))

        ctk.CTkLabel(p_tab, text="SSN (YYYYMMDDXXXX)", font=("Arial", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=5, pady=(2, 0))
        self.ent_ssn = ctk.CTkEntry(p_tab, textvariable=self.ssn_var, height=26, fg_color="#182030", border_color=CARD_BORDER)
        self.ent_ssn.pack(fill="x", padx=5, pady=(0, 10))

        # Sliders
        self.lbl_diam = ctk.CTkLabel(p_tab, text="Rotor Diameter: 95.0 m", font=("Arial", 12))
        self.lbl_diam.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_diam = ctk.CTkSlider(p_tab, from_=30, to=150, number_of_steps=120, variable=self.diam_var, command=self.on_slider_move)
        self.slider_diam.pack(fill="x", padx=5, pady=(0, 10))

        self.lbl_height = ctk.CTkLabel(p_tab, text="Hub Height: 105.0 m", font=("Arial", 12))
        self.lbl_height.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_height = ctk.CTkSlider(p_tab, from_=40, to=160, number_of_steps=120, variable=self.height_var, command=self.on_slider_move)
        self.slider_height.pack(fill="x", padx=5, pady=(0, 10))

        self.lbl_solidity = ctk.CTkLabel(p_tab, text="Rotor Solidity: 3.5 %", font=("Arial", 12))
        self.lbl_solidity.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_solidity = ctk.CTkSlider(p_tab, from_=1, to=10, number_of_steps=90, variable=self.solidity_var, command=self.on_slider_move)
        self.slider_solidity.pack(fill="x", padx=5, pady=(0, 10))

        # Blades Count Segmented Button
        ctk.CTkLabel(p_tab, text="Number of Blades", font=("Arial", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=5, pady=(5, 0))
        self.seg_blades = ctk.CTkSegmentedButton(
            p_tab, 
            values=["2 Blades", "3 Blades", "4 Blades"], 
            variable=self.blades_var,
            command=self.on_slider_move,
            selected_color=ACCENT_ORANGE,
            unselected_color="#223147"
        )
        self.seg_blades.pack(fill="x", padx=5, pady=5)

        # --- Tab 2: Drivetrain Setup ---
        d_tab = self.tab_widget.tab("Drivetrain")
        
        ctk.CTkLabel(d_tab, text="Gearbox Technology", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(10, 2))
        self.combo_gearbox = ctk.CTkOptionMenu(
            d_tab, 
            values=["None (Direct Drive)", "Medium-Speed", "High-Speed"],
            variable=self.gearbox_var,
            command=self.on_slider_move,
            fg_color="#182030", button_color=CARD_BORDER, button_hover_color=ACCENT_BLUE
        )
        self.combo_gearbox.pack(fill="x", padx=5, pady=(0, 15))

        ctk.CTkLabel(d_tab, text="Generator Type", font=("Arial", 12)).pack(anchor="w", padx=5, pady=(10, 2))
        self.combo_generator = ctk.CTkOptionMenu(
            d_tab, 
            values=["Synchronous", "Asynchronous", "DFIG"],
            variable=self.generator_var,
            command=self.on_slider_move,
            fg_color="#182030", button_color=CARD_BORDER, button_hover_color=ACCENT_BLUE
        )
        self.combo_generator.pack(fill="x", padx=5, pady=(0, 15))

        # Add visual description box
        drivetrain_info = ctk.CTkFrame(d_tab, fg_color="#162235", corner_radius=6, border_width=1, border_color=CARD_BORDER)
        drivetrain_info.pack(fill="both", expand=True, padx=5, pady=10)
        
        self.lbl_drivetrain_desc = ctk.CTkLabel(
            drivetrain_info, 
            text="DFIG + Medium-Speed: Combines active speed variation with lower mechanical fatigue. Provides moderate efficiency boost (+2% CF).",
            font=("Arial", 10),
            text_color=TEXT_MUTED,
            wraplength=260,
            justify="left"
        )
        self.lbl_drivetrain_desc.pack(padx=10, pady=10)

        # --- Tab 3: Economic Variables ---
        e_tab = self.tab_widget.tab("Economics")
        
        self.lbl_price = ctk.CTkLabel(e_tab, text="Electricity Price: 30 €/MWh", font=("Arial", 12))
        self.lbl_price.pack(anchor="w", padx=5, pady=(10, 0))
        self.slider_price = ctk.CTkSlider(e_tab, from_=10, to=100, number_of_steps=90, variable=self.price_var, command=self.on_slider_move)
        self.slider_price.pack(fill="x", padx=5, pady=(0, 15))

        self.lbl_lifetime = ctk.CTkLabel(e_tab, text="Project Lifetime: 22 years", font=("Arial", 12))
        self.lbl_lifetime.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_lifetime = ctk.CTkSlider(e_tab, from_=15, to=30, number_of_steps=15, variable=self.lifetime_var, command=self.on_slider_move)
        self.slider_lifetime.pack(fill="x", padx=5, pady=(0, 15))

        self.lbl_inflation = ctk.CTkLabel(e_tab, text="Inflation: 2.0 %", font=("Arial", 12))
        self.lbl_inflation.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_inflation = ctk.CTkSlider(e_tab, from_=0, to=8, number_of_steps=80, variable=self.inflation_var, command=self.on_slider_move)
        self.slider_inflation.pack(fill="x", padx=5, pady=(0, 15))

        self.lbl_interest = ctk.CTkLabel(e_tab, text="Interest Rate: 3.0 %", font=("Arial", 12))
        self.lbl_interest.pack(anchor="w", padx=5, pady=(5, 0))
        self.slider_interest = ctk.CTkSlider(e_tab, from_=0, to=10, number_of_steps=100, variable=self.interest_var, command=self.on_slider_move)
        self.slider_interest.pack(fill="x", padx=5, pady=(0, 15))

        # ==========================================
        # 3. CENTER PANEL (CAD CANVAS WITH ROTATION)
        # ==========================================
        self.cad_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, border_width=1, border_color=CARD_BORDER)
        self.cad_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(5, 10))
        
        self.cad_frame.grid_rowconfigure(0, weight=0)  # Subheader
        self.cad_frame.grid_rowconfigure(1, weight=1)  # Canvas
        self.cad_frame.grid_rowconfigure(2, weight=0)  # Action Button
        self.cad_frame.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(self.cad_frame, text="LIVE CAD BLUEPRINT SCHEMATIC", font=("Montserrat", 13, "bold"), text_color="white").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Canvas
        self.canvas = tk.Canvas(self.cad_frame, bg="#0B132B", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        # Action: Commit & Run Button
        action_bar = ctk.CTkFrame(self.cad_frame, fg_color="transparent")
        action_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
        action_bar.grid_columnconfigure(0, weight=1)

        self.btn_simulate = ctk.CTkButton(
            action_bar, 
            text="RUN SIMULATION", 
            font=("Arial", 14, "bold"), 
            fg_color=ACCENT_ORANGE, 
            hover_color="#CC6200",
            text_color="white",
            height=40,
            command=self.trigger_simulation
        )
        self.btn_simulate.grid(row=0, column=0, sticky="ew")

        # ==========================================
        # 4. RIGHT PANEL (ANALYTICS & OVERLAY)
        # ==========================================
        self.analytics_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, width=420, border_width=1, border_color=CARD_BORDER)
        self.analytics_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=(5, 10))
        self.analytics_frame.pack_propagate(False)

        ctk.CTkLabel(self.analytics_frame, text="ANALYTICS & RESULTS", font=("Montserrat", 13, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=15, pady=(15, 5))

        # Tabs for analytics
        self.results_tab = ctk.CTkTabview(self.analytics_frame, fg_color="transparent", text_color="white")

        self.results_tab.pack(fill="both", expand=True, padx=5, pady=5)
        self.results_tab.add("Performance Charts")
        self.results_tab.add("Engineering Audit")
        self.results_tab.add("Financial Ledger")

        # --- Tab 1: Charts Canvas ---
        ch_tab = self.results_tab.tab("Performance Charts")
        self.charts_canvas = tk.Canvas(ch_tab, bg="#10172A", highlightthickness=0)
        self.charts_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Tab 2: Audit ---
        au_tab = self.results_tab.tab("Engineering Audit")
        
        self.audit_scroll = ctk.CTkScrollableFrame(au_tab, fg_color="transparent")
        self.audit_scroll.pack(fill="both", expand=True)

        # Create audit metrics rows
        self.audit_rows = {}
        audit_defs = [
            ("hub_wind", "Hub Average Wind Speed", "- m/s"),
            ("swept_area", "Rotor Swept Area", "- m²"),
            ("rated_power", "Turbine Rated Power", "- kW"),
            ("cap_factor", "Drivetrain Capacity Factor", "- %"),
            ("thrust_load", "Operational Aerodynamic Load", "- kN"),
            ("storm_load", "Storm Load (60 m/s Survival)", "- kN"),
            ("t_op", "Tower Base Wall Thickness (Op)", "- mm"),
            ("t_storm", "Tower Base Wall Thickness (Storm)", "- mm"),
            ("safety_factor", "Structural Safety Factor", "-"),
        ]
        
        for key, label, init_val in audit_defs:
            row = ctk.CTkFrame(self.audit_scroll, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            ctk.CTkLabel(row, text=label, font=("Arial", 11), text_color=TEXT_MUTED).pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=init_val, font=("Arial", 11, "bold"), text_color=TEXT_MAIN)
            val_lbl.pack(side="right")
            self.audit_rows[key] = val_lbl

        # Guidelines Box
        guidelines_box = ctk.CTkFrame(self.audit_scroll, fg_color="#1E293B", corner_radius=6)
        guidelines_box.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(guidelines_box, text="DESIGN GUIDELINES", font=("Arial", 10, "bold"), text_color=ACCENT_ORANGE).pack(anchor="w", padx=10, pady=(8, 2))
        
        desc_guidelines = (
            "• Safety Factor must exceed 1.0 (preferably > 1.5).\n"
            "• High solidity blades increase storm torque significantly, requiring thicker tower walls.\n"
            "• Increasing hub height yields higher wind speeds (Wind Shear) but raises gravity bending loads."
        )
        ctk.CTkLabel(guidelines_box, text=desc_guidelines, font=("Arial", 10), text_color=TEXT_MUTED, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        # --- Tab 3: Ledger ---
        fn_tab = self.results_tab.tab("Financial Ledger")
        
        self.ledger_scroll = ctk.CTkScrollableFrame(fn_tab, fg_color="transparent")
        self.ledger_scroll.pack(fill="both", expand=True)

        # Cost breakdown chart area
        ctk.CTkLabel(self.ledger_scroll, text="CAPEX COST ALLOCATION BREAKDOWN", font=("Arial", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=5, pady=(5, 2))
        self.capex_canvas = tk.Canvas(self.ledger_scroll, bg="#111827", highlightthickness=0, height=25)
        self.capex_canvas.pack(fill="x", padx=5, pady=(0, 10))

        self.ledger_rows = {}
        ledger_defs = [
            ("capex_turb", "Turbine Rotor Assembly Cost", "- k€"),
            ("capex_driv", "Drivetrain & Nacelle Cost", "- k€"),
            ("capex_tow", "Steel Tower Structure Cost", "- k€"),
            ("capex_found", "Concrete Foundation & Site Cost", "- k€"),
            ("capex_inst", "Grid Connection & Roads", "3,500 k€"),
            ("capex_tot", "TOTAL CAPITAL COST (CAPEX)", "- k€", True),
            ("opex", "Annual Operating Costs (OPEX)", "- k€/yr"),
            ("revenue", "Net Annual Yield Revenue", "- k€/yr"),
            ("margin", "Lifetime Profit Margin", "- %", True),
        ]

        for item in ledger_defs:
            is_bold = len(item) == 4
            key, label, init_val = item[0], item[1], item[2]
            
            row = ctk.CTkFrame(self.ledger_scroll, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            lbl_weight = "bold" if is_bold else "normal"
            lbl_color = TEXT_MAIN if is_bold else TEXT_MUTED
            
            ctk.CTkLabel(row, text=label, font=("Arial", 11, lbl_weight), text_color=lbl_color).pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=init_val, font=("Arial", 11, "bold"), text_color=ACCENT_BLUE if is_bold else TEXT_MAIN)
            val_lbl.pack(side="right")
            self.ledger_rows[key] = val_lbl

        # ==========================================
        # 5. SIMULATION LOADING OVERLAY & BANNER
        # ==========================================
        # Dynamic Warning Banner indicating that current inputs differ from plots
        self.banner = ctk.CTkFrame(self.analytics_frame, fg_color="#332B12", height=32, corner_radius=0)
        self.banner.place(relx=0, rely=0.88, relwidth=1, relheight=0.06)
        self.lbl_banner = ctk.CTkLabel(
            self.banner, 
            text="⚠️ Inputs changed. Click 'Run Simulation' to calculate results.",
            font=("Arial", 11, "bold"),
            text_color=ACCENT_YELLOW
        )
        self.lbl_banner.pack(pady=4)

        # Loading overlay frame
        self.loading_overlay = ctk.CTkFrame(self.analytics_frame, fg_color="#111827", corner_radius=0)

        
        self.loading_container = ctk.CTkFrame(self.loading_overlay, fg_color="transparent")
        self.loading_container.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(self.loading_container, text="SUPERCOMPUTER SIMULATION RUNNING", font=("Montserrat", 11, "bold"), text_color=ACCENT_ORANGE).pack(pady=5)
        self.lbl_loading_status = ctk.CTkLabel(self.loading_container, text="Initializing wind tunnel aerodynamic grid...", font=("Arial", 12), text_color="white")
        self.lbl_loading_status.pack(pady=(0, 15))

        self.loading_progress = ctk.CTkProgressBar(self.loading_container, width=280, progress_color=ACCENT_ORANGE, fg_color="#223147")
        self.loading_progress.pack()

        # Update initial states
        self.on_mission_change("Free Play Sandbox")

    # ==========================================
    # LOGIC: INPUT TRACERS & PRESSETS
    # ==========================================
    def on_slider_move(self, *args):
        # Update labels instantly
        self.lbl_diam.configure(text=f"Rotor Diameter: {self.diam_var.get():.1f} m")
        self.lbl_height.configure(text=f"Hub Height: {self.height_var.get():.1f} m")
        self.lbl_solidity.configure(text=f"Rotor Solidity: {self.solidity_var.get():.1f} %")
        self.lbl_price.configure(text=f"Electricity Price: {int(self.price_var.get())} €/MWh")
        self.lbl_lifetime.configure(text=f"Project Lifetime: {self.lifetime_var.get()} years")
        self.lbl_inflation.configure(text=f"Inflation: {self.inflation_var.get():.1f} %")
        self.lbl_interest.configure(text=f"Interest Rate: {self.interest_var.get():.1f} %")

        # Update Drivetrain Info Box Description dynamically
        gear = self.combo_gearbox.get()
        gen = self.combo_generator.get()
        if gear == "None (Direct Drive)":
            desc = "Direct Drive + " + gen + ": No gearbox eliminates failure points and reduces maintenance, but high-pole generator adds weight and CAPEX."
        else:
            desc = gear + " + " + gen + ": Traditional geared drivetrain. Standard design, lower nacelle cost, but requires scheduled gearbox checkups."
        self.lbl_drivetrain_desc.configure(text=desc)

        # Flag that simulation outputs do not match inputs
        self.simulation_out_of_date = True
        self.banner.place(relx=0, rely=0.88, relwidth=1, relheight=0.06)
        
        # Redraw the CAD turbine visually (interactive blueprint update)
        self.update_cad_drawing()

    def on_ssn_change(self, *args):
        ssn = self.ssn_var.get()
        if len(ssn) == 12 and ssn.isdigit():
            # Integrate parameters from birth month / day
            month = int(ssn[4:6])
            day = int(ssn[6:8])
            
            # Derived average wind presets from SSN
            sim_avg_u10 = round(5.0 + (day / 15.0), 1)
            self.lbl_mission_desc.configure(
                text=f"Sandbox mode: Wind speed preset at {sim_avg_u10} m/s based on birthdate (SSN month/day: {month}/{day})."
            )
            self.on_slider_move()

    def on_mission_change(self, choice):
        self.current_mission = choice
        self.runs_remaining = 6
        self.simulation_out_of_date = True
        self.banner.place(relx=0, rely=0.88, relwidth=1, relheight=0.06)

        # Enable/disable inputs or adjust limits according to mission rules
        if choice == "Free Play Sandbox":
            self.lbl_mission_desc.configure(text="Free Sandbox: Explore turbine sizes and parameters with unlimited simulation runs.")
            self.lbl_runs.configure(text="∞ / ∞", text_color=ACCENT_GREEN)
            self.lbl_mission_status.configure(text="SANDBOX", text_color=ACCENT_BLUE)
            # Reset controls to normal defaults
            self.slider_diam.configure(state="normal")
            self.slider_height.configure(state="normal")
        
        elif choice == "The Arctic Gale":
            desc = "Mission A: Build a storm-hardened offshore turbine. Goal: Safety Factor > 1.6 AND positive profit margin. Max 6 runs!"
            self.lbl_mission_desc.configure(text=desc)
            self.lbl_runs.configure(text="6 / 6", text_color=ACCENT_GREEN)
            self.lbl_mission_status.configure(text="IN PROGRESS", text_color=ACCENT_YELLOW)
            
            # Setup presets matching the mission
            self.diam_var.set(80.0)
            self.height_var.set(90.0)
            self.solidity_var.set(3.0)
            self.gearbox_var.set("Medium-Speed")
            self.generator_var.set("DFIG")
            
        elif choice == "The Gentle Breeze":
            desc = "Mission B: Optimize a low-wind site turbine. Goal: Energy > 1,800 MWh AND Capacity Factor > 35% AND CAPEX < 5.0 M€. Max 6 runs!"
            self.lbl_mission_desc.configure(text=desc)
            self.lbl_runs.configure(text="6 / 6", text_color=ACCENT_GREEN)
            self.lbl_mission_status.configure(text="IN PROGRESS", text_color=ACCENT_YELLOW)

            # Setup presets matching the mission
            self.diam_var.set(110.0)
            self.height_var.set(120.0)
            self.solidity_var.set(4.0)
            self.gearbox_var.set("High-Speed")
            self.generator_var.set("Synchronous")

        self.on_slider_move()
        self.clear_charts()

    # ==========================================
    # ANIMATION: ROTATING TURBINE BLADES
    # ==========================================
    def rotate_blades_loop(self):
        if self.animation_running:
            # Rotor speed depends slightly on diameter and solidity
            # Smaller rotors with lower solidity rotate faster
            sol = self.solidity_var.get()
            diam = self.diam_var.get()
            speed = max(1, int(40 - diam / 4 - sol))
            
            self.blade_angle = (self.blade_angle + speed) % 360
            self.update_cad_drawing()
            
        self.after(50, self.rotate_blades_loop)

    # ==========================================
    # RENDERING: CANVAS CAD DRAWING
    # ==========================================
    def update_cad_drawing(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            return  # Wait for geometry manager to place widget

        self.canvas.delete("all")

        # Technical Grid lines
        grid_space = 25
        for x in range(0, w, grid_space):
            self.canvas.create_line(x, 0, x, h, fill="#121D33", width=1)
        for y in range(0, h, grid_space):
            self.canvas.create_line(0, y, w, y, fill="#121D33", width=1)

        # Scale math to fit canvas
        max_dim = 160.0
        draw_scale = (h * 0.55) / max_dim

        # Core Coordinates
        ground_y = h - int(50 * self.scale_factor)
        center_x = w // 2

        real_height = self.height_var.get()
        real_diam = self.diam_var.get()
        real_solidity = self.solidity_var.get()

        hub_y = ground_y - int(real_height * draw_scale)
        rotor_r = int((real_diam / 2) * draw_scale)

        # Check safety (approx structural stress highlights tower base)
        # solidity * diameter * wind shear moment
        moment = (real_solidity / 3.0) * (real_diam / 90.0) * (real_height / 90.0)**2
        is_unsafe = moment > 2.2
        tower_color = ACCENT_RED if is_unsafe else "#334155"

        # 1. Foundation Base
        base_w = int(40 * self.scale_factor)
        self.canvas.create_polygon(
            center_x - base_w, ground_y,
            center_x + base_w, ground_y,
            center_x + base_w - 5, ground_y - 12,
            center_x - base_w + 5, ground_y - 12,
            fill="#1E293B", outline="#475569", width=2
        )

        # 2. Tower Structure (Tapered)
        tower_base_r = max(5, int(15 * (real_height / 100)))
        tower_top_r = max(3, int(6 * (real_height / 100)))
        self.canvas.create_polygon(
            center_x - tower_base_r, ground_y - 12,
            center_x + tower_base_r, ground_y - 12,
            center_x + tower_top_r, hub_y,
            center_x - tower_top_r, hub_y,
            fill=tower_color, outline="#64748B", width=2
        )

        # 3. Dimension Line: Tower Height
        dim_left_x = center_x - tower_base_r - int(25 * self.scale_factor)
        self.canvas.create_line(dim_left_x, ground_y, dim_left_x, hub_y, fill=ACCENT_BLUE, arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_left_x - 5, ground_y, dim_left_x + 5, ground_y, fill=ACCENT_BLUE)
        self.canvas.create_line(dim_left_x - 5, hub_y, dim_left_x + 5, hub_y, fill=ACCENT_BLUE)
        self.canvas.create_text(
            dim_left_x - int(35 * self.scale_factor), (ground_y + hub_y) // 2, 
            text=f"H = {real_height:.1f}m", fill=TEXT_MAIN, font=("Arial", int(10 * self.scale_factor), "bold")
        )

        # 4. Nacelle (Drivetrain housing)
        nacelle_w = int(22 * self.scale_factor)
        nacelle_h = int(12 * self.scale_factor)
        self.canvas.create_rectangle(
            center_x - nacelle_w, hub_y - nacelle_h,
            center_x + 6, hub_y + 3,
            fill="#475569", outline="#E2E8F0", width=1.5
        )

        # 5. Rotating Blades
        blades_str = self.blades_var.get()
        num_blades = int(blades_str.split()[0])
        blade_base_w = int(4 * (real_solidity / 3.0))

        # Rotate and draw blades
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
                fill="#F8FAFC", outline=ACCENT_BLUE, width=1.5
            )

        # 6. Hub nose cone
        self.canvas.create_oval(
            center_x - 6, hub_y - 6,
            center_x + 6, hub_y + 6,
            fill=ACCENT_ORANGE, outline="#FFFFFF", width=1.5
        )

        # 7. Dimension Line: Rotor Diameter
        dim_right_x = center_x + rotor_r + int(25 * self.scale_factor)
        self.canvas.create_line(dim_right_x, hub_y - rotor_r, dim_right_x, hub_y + rotor_r, fill=ACCENT_BLUE, arrow=tk.BOTH, width=1.5)
        self.canvas.create_line(dim_right_x - 5, hub_y - rotor_r, dim_right_x + 5, hub_y - rotor_r, fill=ACCENT_BLUE)
        self.canvas.create_line(dim_right_x - 5, hub_y + rotor_r, dim_right_x + 5, hub_y + rotor_r, fill=ACCENT_BLUE)
        self.canvas.create_text(
            dim_right_x + int(35 * self.scale_factor), hub_y, 
            text=f"D = {real_diam:.1f}m", fill=TEXT_MAIN, font=("Arial", int(10 * self.scale_factor), "bold")
        )

        # Safety Alert Banner on CAD
        if is_unsafe:
            self.canvas.create_rectangle(
                center_x - 110, ground_y + 10,
                center_x + 110, ground_y + 35,
                fill="#FF3E6C", outline="#FFFFFF", width=1
            )
            self.canvas.create_text(
                center_x, ground_y + 22,
                text="⚠️ HIGH BENDING MOMENT ALERT", fill="white", font=("Arial", 9, "bold")
            )

    # ==========================================
    # LOGIC: SIMULATION STEPS AND LOADING
    # ==========================================
    def trigger_simulation(self):
        # Prevent simulation if out of runs in challenge mode
        if self.current_mission != "Free Play Sandbox" and self.runs_remaining <= 0:
            self.show_dialog("Out of R&D Budget", "You have used all 6 simulation runs for this challenge.\nPlease restart or select another mission.", is_err=True)
            return

        # Show loading overlay
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.loading_progress.start()
        
        # Step through animated progress labels
        self.after(500, lambda: self.lbl_loading_status.configure(text="Integrating wind speed probability using Weibull factors..."))
        self.after(1200, lambda: self.lbl_loading_status.configure(text="Calculating beam bending moments on structural tower base..."))
        self.after(2000, lambda: self.lbl_loading_status.configure(text="Compiling financial CAPEX ledger and NPV margin predictions..."))
        self.after(3000, self.complete_simulation)

    def complete_simulation(self):
        # Stop animation and remove overlay
        self.loading_progress.stop()
        self.loading_overlay.place_forget()

        # Decrement runs if in challenge mode
        if self.current_mission != "Free Play Sandbox":
            self.runs_remaining -= 1
            if self.runs_remaining < 0: self.runs_remaining = 0
            
            # Update Runs display
            color = ACCENT_GREEN if self.runs_remaining >= 4 else (ACCENT_YELLOW if self.runs_remaining >= 2 else ACCENT_RED)
            self.lbl_runs.configure(text=f"{self.runs_remaining} / 6", text_color=color)

        # Clear warning banner
        self.simulation_out_of_date = False
        self.banner.place_forget()

        # Run math and update charts/ledger
        self.run_physics_and_economics()

        # Check Mission Target conditions
        self.check_mission_objectives()

    # ==========================================
    # CORE MATH: SIMULATION ENGINE (MOCKED)
    # ==========================================
    def run_physics_and_economics(self):
        # Read inputs
        diam = self.diam_var.get()
        height = self.height_var.get()
        solidity = self.solidity_var.get()
        blades_str = self.blades_var.get()
        num_blades = int(blades_str.split()[0])
        gear = self.gearbox_var.get()
        generator = self.generator_var.get()
        price = self.price_var.get()
        lifetime = self.lifetime_var.get()
        inflation = self.inflation_var.get()
        interest = self.interest_var.get()

        # 1. Establish Wind Presets based on Active Mission
        if self.current_mission == "The Arctic Gale":
            avg_u10 = 9.5
            roughness = 0.01  # Sea (smooth)
            k_factor = 2.2
        elif self.current_mission == "The Gentle Breeze":
            avg_u10 = 5.2
            roughness = 1.0   # Forest (rough, high shear)
            k_factor = 1.6
        else:
            # Sandbox Wind Preset: Parse SSN birthdate or default
            ssn = self.ssn_var.get()
            if len(ssn) == 12 and ssn.isdigit():
                day = int(ssn[6:8])
                avg_u10 = round(5.0 + (day / 15.0), 1)
            else:
                avg_u10 = 7.5
            roughness = 100.0  # Open fields
            k_factor = 2.0

        # 2. Physics Model calculations
        z0 = roughness / 1000.0
        # Wind shear power profile calculation
        wind_nacelle = avg_u10 * math.log(height / z0) / math.log(10.0 / z0)
        
        swept_area = math.pi * (diam / 2.0)**2
        
        # Efficiencies derived from input selections
        capture_eff = 0.45
        drivetrain_eff = 0.90
        
        # Rated Wind Speed and power calculations
        v_rated = 11.5
        rated_power = 0.62 * (v_rated**3) * swept_area * capture_eff * drivetrain_eff / 1000.0  # kW
        
        # Drivetrain Gearbox/Generator Capacity Factor boosts
        cf_base = 0.07 * wind_nacelle - 0.12
        cf_boost = 0.0
        if gear == "High-Speed": cf_boost += 0.03
        elif gear == "Medium-Speed": cf_boost += 0.01
        if generator == "DFIG": cf_boost += 0.02
        elif generator == "Synchronous": cf_boost += 0.01
        
        cap_factor = max(0.12, min(0.52, cf_base + cf_boost))
        
        # AEP in MWh
        generated_energy = rated_power * 8760.0 * cap_factor * 0.95 / 1000.0

        # 3. Structural Loads & Wall Thickness
        aerodynamic_load = 0.5 * 1.2 * (8.0/9.0) * swept_area * (v_rated**2) / 1000.0  # kN
        
        # Solidity & Storm wind speeds (60m/s survival gust)
        storm_wind_survival = 60.0
        if self.current_mission == "The Arctic Gale":
            storm_wind_survival = 65.0  # Severe arctic storm
            
        storm_load = 0.5 * 1.2 * 1.5 * (solidity / 100.0) * swept_area * (storm_wind_survival**2) / 1000.0  # kN

        # Tower base required thickness (160 MPa steel strength yield limit)
        t_op = (aerodynamic_load * height) / (math.pi * (height / 40.0)**2 * 160.0) * 2.0 * 1000.0  # mm
        t_storm = (storm_load * height) / (math.pi * (height / 40.0)**2 * 160.0) * 2.0 * 1000.0      # mm
        t_max = max(t_op, t_storm)

        # Safety Factor against design limits (150 mm base wall thickness budget)
        safety_factor = 150.0 / t_max

        # 4. Economics Model
        # CAPEX components
        capex_turbine = 900.0 * (diam / 90.0)**3.5
        capex_drivetrain = 800.0 * (rated_power / 3000.0) * (diam / 90.0)
        # Apply costs for gearbox tech
        if gear == "None (Direct Drive)": capex_drivetrain += 300.0
        elif gear == "High-Speed": capex_drivetrain += 150.0
        
        capex_tower = 700.0 * (diam / 90.0)**2 * (height / 90.0)**2 + 300.0
        capex_foundation = 300.0 * math.sqrt((diam / 90.0) * (height / 100.0))
        capex_installation = 3500.0
        
        total_capex = capex_turbine + capex_drivetrain + capex_tower + capex_foundation + capex_installation
        
        # Annual OPEX and Income
        opex = 600.0 * (rated_power / 3000.0) + 150.0
        annual_revenue = generated_energy * (price + 1.0) / 1000.0  # k€
        annual_savings = annual_revenue - opex

        # NPV over project lifetime
        k = (1 + inflation / 100.0) / (1 + interest / 100.0)
        if abs(k - 1.0) > 0.0001:
            NPV = annual_savings * (k * (1 - k**lifetime)) / (1 - k)
        else:
            NPV = annual_savings * lifetime

        profits = NPV - total_capex - (0.07 * total_capex)
        margin = (profits / total_capex) * 100.0
        payback = total_capex / max(1.0, annual_savings)

        # Grade scorecards
        grade = "C"
        grade_color = TEXT_MAIN
        if safety_factor < 1.0:
            grade = "F"
            grade_color = ACCENT_RED
        elif profits < 0:
            grade = "D"
            grade_color = ACCENT_RED
        else:
            if margin >= 25.0:
                grade = "A+"
                grade_color = ACCENT_GREEN
            elif margin >= 15.0:
                grade = "A"
                grade_color = ACCENT_GREEN
            elif margin >= 5.0:
                grade = "B"
                grade_color = ACCENT_BLUE

        # Save simulated state
        self.last_simulated_results = {
            "hub_wind": wind_nacelle,
            "swept_area": swept_area,
            "rated_power": rated_power,
            "cap_factor": cap_factor * 100.0,
            "thrust_load": aerodynamic_load,
            "storm_load": storm_load,
            "t_op": t_op,
            "t_storm": t_storm,
            "safety_factor": safety_factor,
            "capex_turb": capex_turbine,
            "capex_driv": capex_drivetrain,
            "capex_tow": capex_tower,
            "capex_found": capex_foundation,
            "capex_tot": total_capex,
            "opex": opex,
            "revenue": annual_revenue,
            "margin": margin,
            "payback": payback,
            "profits": profits,
            "grade": grade,
            "grade_color": grade_color,
            "k_factor": k_factor,
            "wind_nacelle_avg": wind_nacelle,
            "v_rated": v_rated
        }

        # 5. Render results to widgets
        self.lbl_grade.configure(text=grade, text_color=grade_color)
        self.lbl_profit.configure(
            text=f"{profits:,.1f} k€", 
            text_color=ACCENT_GREEN if profits >= 0 else ACCENT_RED
        )

        # Update Audit Tab
        self.audit_rows["hub_wind"].configure(text=f"{wind_nacelle:.1f} m/s")
        self.audit_rows["swept_area"].configure(text=f"{swept_area:,.1f} m²")
        self.audit_rows["rated_power"].configure(text=f"{rated_power:,.1f} kW")
        self.audit_rows["cap_factor"].configure(text=f"{cap_factor * 100:.1f} %")
        self.audit_rows["thrust_load"].configure(text=f"{aerodynamic_load:,.1f} kN")
        self.audit_rows["storm_load"].configure(text=f"{storm_load:,.1f} kN")
        
        # Color wall thickness based on limits
        self.audit_rows["t_op"].configure(text=f"{t_op:.1f} mm")
        self.audit_rows["t_storm"].configure(
            text=f"{t_storm:.1f} mm",
            text_color=ACCENT_RED if t_storm > 150 else (ACCENT_YELLOW if t_storm > 110 else TEXT_MAIN)
        )
        
        sf_color = ACCENT_GREEN if safety_factor >= 1.5 else (ACCENT_YELLOW if safety_factor >= 1.0 else ACCENT_RED)
        self.audit_rows["safety_factor"].configure(text=f"{safety_factor:.2f}", text_color=sf_color)

        # Update Ledger Tab
        self.ledger_rows["capex_turb"].configure(text=f"{capex_turbine:,.1f} k€")
        self.ledger_rows["capex_driv"].configure(text=f"{capex_drivetrain:,.1f} k€")
        self.ledger_rows["capex_tow"].configure(text=f"{capex_tower:,.1f} k€")
        self.ledger_rows["capex_found"].configure(text=f"{capex_foundation:,.1f} k€")
        self.ledger_rows["capex_tot"].configure(text=f"{total_capex:,.1f} k€")
        self.ledger_rows["opex"].configure(text=f"{opex:,.1f} k€/yr")
        self.ledger_rows["revenue"].configure(text=f"{annual_revenue:,.1f} k€/yr")
        
        self.ledger_rows["margin"].configure(
            text=f"{margin:.1f} %",
            text_color=ACCENT_GREEN if margin >= 0 else ACCENT_RED
        )

        # Redraw cost allocation bar and curve plots
        self.draw_capex_breakdown(capex_turbine, capex_drivetrain, capex_tower, capex_foundation, capex_installation)
        self.draw_performance_curves()

    # ==========================================
    # ANALYTICS GRAPHICS: CHARTS & CAPEX BAR
    # ==========================================
    def clear_charts(self):
        w = self.charts_canvas.winfo_width()
        h = self.charts_canvas.winfo_height()
        if w < 10 or h < 10: return
        self.charts_canvas.delete("all")
        self.charts_canvas.create_text(w//2, h//2, text="[ Simulation Out of Date ]\nClick Run Simulation to plot.", fill=TEXT_MUTED, font=("Arial", 12), justify="center")

    def draw_performance_curves(self):
        w = self.charts_canvas.winfo_width()
        h = self.charts_canvas.winfo_height()
        if w < 10 or h < 10: return

        self.charts_canvas.delete("all")

        res = self.last_simulated_results
        if not res: return

        # Dimensions of Subplots
        pad = 25
        plot_w = (w - 3*pad) // 2
        plot_h = h - 2*pad

        # --- Subplot 1: Weibull Wind Speed Distribution ---
        x1_offset = pad
        y_offset = pad
        
        # Subplot border & background
        self.charts_canvas.create_rectangle(x1_offset, y_offset, x1_offset + plot_w, y_offset + plot_h, fill="#0F172A", outline=CARD_BORDER)
        self.charts_canvas.create_text(x1_offset + plot_w//2, y_offset - 10, text="Weibull Wind Speed Curve", fill=ACCENT_BLUE, font=("Arial", 9, "bold"))

        # Draw Weibull curve line
        k = res["k_factor"]
        C = res["wind_nacelle_avg"] / math.gamma(1.0 + 1.0/k)
        
        points = []
        max_v = 25.0
        max_prob = 0.12  # Hardcoded scaling factor for visual height
        
        for i in range(plot_w):
            v = (i / plot_w) * max_v
            if v > 0:
                prob = (k/C) * ((v/C)**(k-1)) * math.exp(-((v/C)**k))
            else:
                prob = 0
                
            px = x1_offset + i
            py = y_offset + plot_h - int((prob / max_prob) * plot_h)
            # Clamp inside plot height
            py = max(y_offset, min(y_offset + plot_h, py))
            points.append((px, py))

        if len(points) > 1:
            self.charts_canvas.create_line(points, fill=ACCENT_BLUE, width=2)

        # Cut-in/Cut-out Shaded Operational Band
        cut_in_x = int((3.5 / max_v) * plot_w)
        cut_out_x = int((25.0 / max_v) * plot_w)
        self.charts_canvas.create_line(x1_offset + cut_in_x, y_offset, x1_offset + cut_in_x, y_offset + plot_h, fill=ACCENT_GREEN, dash=(4, 4))
        self.charts_canvas.create_text(x1_offset + cut_in_x + 12, y_offset + 15, text="Cut-in", fill=ACCENT_GREEN, font=("Arial", 7), angle=90)

        # Plot labels/ticks
        self.charts_canvas.create_text(x1_offset + 15, y_offset + plot_h + 10, text="0", fill=TEXT_MUTED, font=("Arial", 8))
        self.charts_canvas.create_text(x1_offset + plot_w - 15, y_offset + plot_h + 10, text="25m/s", fill=TEXT_MUTED, font=("Arial", 8))
        
        # --- Subplot 2: Turbine Power Curve ---
        x2_offset = 2*pad + plot_w
        
        self.charts_canvas.create_rectangle(x2_offset, y_offset, x2_offset + plot_w, y_offset + plot_h, fill="#0F172A", outline=CARD_BORDER)
        self.charts_canvas.create_text(x2_offset + plot_w//2, y_offset - 10, text="Turbine Power Curve (kW)", fill=ACCENT_ORANGE, font=("Arial", 9, "bold"))

        p_points = []
        p_rated = res["rated_power"]
        
        for i in range(plot_w):
            v = (i / plot_w) * max_v
            # Piecewise power curve math
            if v < 3.5:
                p = 0
            elif v < 11.5:
                # Cubic rise
                p = p_rated * ((v - 3.5) / (11.5 - 3.5))**3
            elif v < 25.0:
                # Capped rated power
                p = p_rated
            else:
                p = 0
                
            px = x2_offset + i
            py = y_offset + plot_h - int((p / (p_rated * 1.1)) * plot_h)
            py = max(y_offset, min(y_offset + plot_h, py))
            p_points.append((px, py))

        if len(p_points) > 1:
            self.charts_canvas.create_line(p_points, fill=ACCENT_ORANGE, width=2)

        # Plot labels
        self.charts_canvas.create_text(x2_offset + 15, y_offset + plot_h + 10, text="0", fill=TEXT_MUTED, font=("Arial", 8))
        self.charts_canvas.create_text(x2_offset + plot_w - 15, y_offset + plot_h + 10, text="25m/s", fill=TEXT_MUTED, font=("Arial", 8))
        self.charts_canvas.create_text(x2_offset + 25, y_offset + 12, text=f"{int(p_rated)}kW", fill=TEXT_MAIN, font=("Arial", 8))

    def draw_capex_breakdown(self, turb, driv, tow, found, inst):
        w = self.capex_canvas.winfo_width()
        h = self.capex_canvas.winfo_height()
        if w < 10 or h < 10:
            self.after(200, lambda: self.draw_capex_breakdown(turb, driv, tow, found, inst))
            return

        self.capex_canvas.delete("all")
        
        tot = turb + driv + tow + found + inst
        
        # Component ratios
        w_turb = int((turb / tot) * w)
        w_driv = int((driv / tot) * w)
        w_tow = int((tow / tot) * w)
        w_found = int((found / tot) * w)
        w_inst = w - (w_turb + w_driv + w_tow + w_found)  # Remaining width

        # Draw segment rectangles
        self.capex_canvas.create_rectangle(0, 0, w_turb, h, fill=ACCENT_BLUE, outline="")
        self.capex_canvas.create_rectangle(w_turb, 0, w_turb+w_driv, h, fill=ACCENT_BLUE, outline="")
        self.capex_canvas.create_rectangle(w_turb+w_driv, 0, w_turb+w_driv+w_tow, h, fill=ACCENT_ORANGE, outline="")
        self.capex_canvas.create_rectangle(w_turb+w_driv+w_tow, 0, w_turb+w_driv+w_tow+w_found, h, fill=ACCENT_GREEN, outline="")
        self.capex_canvas.create_rectangle(w_turb+w_driv+w_tow+w_found, 0, w, h, fill="#4B5563", outline="")

    # ==========================================
    # LOGIC: MISSION TARGET VERIFICATIONS
    # ==========================================
    def check_mission_objectives(self):
        res = self.last_simulated_results
        if not res or self.current_mission == "Free Play Sandbox":
            return

        sf = res["safety_factor"]
        margin = res["margin"]
        profits = res["profits"]
        tot_capex = res["capex_tot"]
        cap_factor = res["cap_factor"]
        aep = res["hub_wind"]  # wait, energy generated is generated_energy (AEP)

        # Correct parameter reference
        aep = (res["rated_power"] * 8760.0 * (res["cap_factor"]/100.0) * 0.95 / 1000.0)

        # Mission A: The Arctic Gale
        if self.current_mission == "The Arctic Gale":
            # Safety Factor > 1.6, Margin > 10%
            success = (sf >= 1.6) and (margin >= 10.0) and (profits > 0)
            
            if success:
                self.lbl_mission_status.configure(text="SUCCESS", text_color=ACCENT_GREEN)
                self.show_dialog("Mission Accomplished!", 
                                 f"Congratulations! You successfully designed an offshore turbine that can survive arctic storm gusts.\n\n"
                                 f"• Safety Factor: {sf:.2f} (Required: >= 1.6)\n"
                                 f"• Profit Margin: {margin:.1f}% (Required: >= 10%)\n"
                                 f"• Lifetime Profit: {profits:,.1f} k€")
            elif self.runs_remaining <= 0:
                self.lbl_mission_status.configure(text="FAILED", text_color=ACCENT_RED)
                self.show_dialog("Mission Failed", 
                                 "You ran out of simulation runs without meeting the criteria.\n\n"
                                 "TIP: The turbine base wall thickness requirements are too high during survival storms. "
                                 "Try reducing Rotor Solidity or Rotor Diameter to decrease the storm load surface area.", is_err=True)
            else:
                # Still have runs left
                self.show_dialog("Simulation Complete",
                                 f"Objectives not yet fully met.\n\n"
                                 f"• Safety Factor: {sf:.2f} / 1.60 {'(OK)' if sf >= 1.6 else '(FAILED)'}\n"
                                 f"• Profit Margin: {margin:.1f}% / 10.0% {'(OK)' if margin >= 10.0 else '(FAILED)'}\n"
                                 f"Runs Remaining: {self.runs_remaining}. Adjust parameters and try again!", is_err=True)

        # Mission B: The Gentle Breeze
        elif self.current_mission == "The Gentle Breeze":
            # AEP > 1,800 MWh, Capacity Factor > 35%, CAPEX < 5.0 M€
            success = (aep >= 1800.0) and (cap_factor >= 35.0) and (tot_capex < 5000.0)
            
            if success:
                self.lbl_mission_status.configure(text="SUCCESS", text_color=ACCENT_GREEN)
                self.show_dialog("Mission Accomplished!", 
                                 f"Excellent work! You engineered a low-wind turbine that hits both energy and budget targets.\n\n"
                                 f"• Energy Generated: {aep:,.1f} MWh (Required: >= 1,800 MWh)\n"
                                 f"• Capacity Factor: {cap_factor:.1f}% (Required: >= 35%)\n"
                                 f"• Total CAPEX: {tot_capex:,.1f} k€ (Required: < 5,000 k€)")
            elif self.runs_remaining <= 0:
                self.lbl_mission_status.configure(text="FAILED", text_color=ACCENT_RED)
                self.show_dialog("Mission Failed", 
                                 "You ran out of simulation runs without meeting the criteria.\n\n"
                                 "TIP: To increase power in low-wind regimes, you need a larger Rotor Diameter. "
                                 "To stay under budget, keep the Hub Height compact and choose a cost-effective Drivetrain (Medium-Speed DFIG).", is_err=True)
            else:
                # Still have runs left
                self.show_dialog("Simulation Complete",
                                 f"Objectives not yet fully met.\n\n"
                                 f"• Energy: {aep:,.1f} / 1,800 MWh {'(OK)' if aep >= 1800 else '(FAILED)'}\n"
                                 f"• Capacity Factor: {cap_factor:.1f}% / 35.0% {'(OK)' if cap_factor >= 35.0 else '(FAILED)'}\n"
                                 f"• Total CAPEX: {tot_capex:,.1f} / 5,000 k€ {'(OK)' if tot_capex < 5000 else '(FAILED)'}\n"
                                 f"Runs Remaining: {self.runs_remaining}. Adjust parameters and try again!", is_err=True)

    def show_dialog(self, title, message, is_err=False):
        # A simple non-blocking top-level pop-up dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x240")

        dialog.configure(fg_color=PANEL_BG)
        dialog.transient(self)
        dialog.grab_set()

        # Add message content
        color = ACCENT_RED if is_err else ACCENT_GREEN
        ctk.CTkLabel(dialog, text=title.upper(), font=("Montserrat", 12, "bold"), text_color=color).pack(pady=(15, 10))
        
        tb = ctk.CTkTextbox(dialog, fg_color="transparent", text_color="white", font=("Arial", 11), wrap="word", width=380, height=120)
        tb.pack(padx=15, pady=5)
        tb.insert("0.0", message)
        tb.configure(state="disabled")

        ctk.CTkButton(dialog, text="Close", width=120, height=28, fg_color=CARD_BG, text_color="white", hover_color=CARD_BORDER, command=dialog.destroy).pack(pady=10)

if __name__ == "__main__":
    app = UnifiedChallengeApp()
    app.mainloop()
