import customtkinter as ctk
import tkinter as tk
import math
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


# --- DESIGN SYSTEM COLORS (Sleek Modern Dashboard) ---
BG_COLOR = "#090D16"         # Dark violet-black background
CARD_BG = "#111827"          # Glassy dark card color
CARD_BORDER = "#1F2937"      # Card stroke
ACCENT_GREEN = "#10B981"     # Vibrant emerald green
ACCENT_BLUE = "#3B82F6"      # Deep sky blue
ACCENT_YELLOW = "#F59E0B"    # Rich gold yellow
ACCENT_RED = "#EF4444"       # Punchy red
ACCENT_PURPLE = "#8B5CF6"    # Electric purple
TEXT_MAIN = "#F9FAFB"        # Clean white
TEXT_MUTED = "#9CA3AF"       # Cool grey

class TycoonDashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

        # --- WINDOW SETUP ---
        self.title("Wind Farm Feasibility Dashboard - Mockup B")
        self.geometry("1120x730")
        self.minsize(1050, 680)
        ctk.set_appearance_mode("dark")

        # --- STATE VARIABLES ---
        # Tab 1: Identity & Environment
        self.name_var = ctk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = ctk.StringVar(value="199801281234")
        self.preset_var = ctk.StringVar(value="Coastal Winds")
        
        # Tab 2: Rotor & Drivetrain
        self.diam_var = ctk.DoubleVar(value=95.0)
        self.height_var = ctk.DoubleVar(value=105.0)
        self.solidity_var = ctk.DoubleVar(value=3.0)
        self.blades_var = ctk.StringVar(value="3 Blades")
        self.gearbox_var = ctk.StringVar(value="Medium Ratio")
        self.generator_var = ctk.StringVar(value="DFIG")

        # Tab 3: Economics
        self.price_elec_var = ctk.DoubleVar(value=29.0) # €/MWh
        self.green_cert_var = ctk.DoubleVar(value=1.0) # €/MWh
        self.lifetime_var = ctk.DoubleVar(value=22.0) # Years
        self.interest_var = ctk.DoubleVar(value=3.0) # %
        self.inflation_var = ctk.DoubleVar(value=2.0) # %

        self.create_layout()
        self.recalculate()

    def create_layout(self):
        # 1. TOP HEADER SECTION (SCORECARD)
        self.header_frame = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=CARD_BORDER)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        # Logo / Title
        logo_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        logo_container.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(logo_container, text="WIND SIMULATOR", font=scaled_font("Montserrat", 11, "bold"), text_color=ACCENT_BLUE).pack(anchor="w")
        ctk.CTkLabel(logo_container, text="TYCOON BOARD", font=scaled_font("Montserrat", 20, "bold"), text_color=TEXT_MAIN).pack(anchor="w")

        # Scorecard Cards
        self.score_grade = self.create_header_card("PROJECT GRADE", "B+", ACCENT_GREEN)
        self.score_profit = self.create_header_card("LIFETIME NET PROFIT", "+3,212 k€", ACCENT_GREEN)
        self.score_payback = self.create_header_card("PAYBACK PERIOD", "9.2 Years", ACCENT_BLUE)
        self.score_safety = self.create_header_card("STRUCTURAL SAFETY", "Safe", "white")

        # 2. MAIN SPLIT SECTION (Left: Inputs, Right: Analytics)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.main_container.grid_columnconfigure(0, weight=4, minsize=400) # Inputs
        self.main_container.grid_columnconfigure(1, weight=6, minsize=550) # Analytics
        self.main_container.grid_rowconfigure(0, weight=1)

        # -- LEFT SIDE: INPUT TABS --
        self.inputs_frame = ctk.CTkFrame(self.main_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=CARD_BORDER)
        self.inputs_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")

        input_title = ctk.CTkLabel(self.inputs_frame, text="CONTROL CONSOLE", font=scaled_font("Montserrat", 14, "bold"), text_color=TEXT_MUTED)
        input_title.pack(anchor="w", padx=20, pady=(15, 10))

        # Tabs Widget
        self.tab_widget = ctk.CTkTabview(self.inputs_frame, fg_color="transparent", text_color=TEXT_MAIN)

        self.tab_widget.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        t1 = self.tab_widget.add("Location & ID")
        t2 = self.tab_widget.add("Physical Specs")
        t3 = self.tab_widget.add("Financial Settings")

        # Setup Tab 1: Identity & Environment
        self.setup_tab_location(t1)
        # Setup Tab 2: Physical Specs
        self.setup_tab_physical(t2)
        # Setup Tab 3: Economics
        self.setup_tab_economics(t3)

        # -- RIGHT SIDE: ANALYTICS PANEL --
        self.analytics_frame = ctk.CTkFrame(self.main_container, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=CARD_BORDER)
        self.analytics_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")

        analytics_title = ctk.CTkLabel(self.analytics_frame, text="ECONOMIC & STRUCTURAL AUDIT", font=scaled_font("Montserrat", 14, "bold"), text_color=TEXT_MAIN)
        analytics_title.pack(anchor="w", padx=20, pady=(15, 15))

        # Grid of indicators (Circular meters mockups using custom labels & meters)
        self.meters_frame = ctk.CTkFrame(self.analytics_frame, fg_color="transparent")
        self.meters_frame.pack(fill="x", padx=20, pady=5)
        self.meters_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.meter_roi = self.create_status_gauge(self.meters_frame, 0, "RETURN ON INVEST", "0.0%", ACCENT_GREEN)
        self.meter_wind = self.create_status_gauge(self.meters_frame, 1, "WIND QUALITY", "Poor", ACCENT_BLUE)
        self.meter_safety = self.create_status_gauge(self.meters_frame, 2, "SAFETY RESERVE", "100%", ACCENT_GREEN)

        # Cost Breakdown Segmented Bar (Visual Canvas)
        self.breakdown_title = ctk.CTkLabel(self.analytics_frame, text="CAPEX ALLOCATION BREAKDOWN", font=scaled_font("Arial", 11, "bold"), text_color=TEXT_MUTED)
        self.breakdown_title.pack(anchor="w", padx=20, pady=(20, 5))

        # Canvas bar
        self.bar_canvas = tk.Canvas(self.analytics_frame, height=24, bg=CARD_BG, highlightthickness=0)
        self.bar_canvas.pack(fill="x", padx=20, pady=5)
        self.bar_canvas.bind("<Configure>", lambda e: self.draw_cost_bar())

        # Legend frame
        self.legend_frame = ctk.CTkFrame(self.analytics_frame, fg_color="transparent")
        self.legend_frame.pack(fill="x", padx=20, pady=(5, 15))

        # Detailed Finance Ledger List
        self.ledger_title = ctk.CTkLabel(self.analytics_frame, text="FINANCIAL LEDGER DETAILS", font=scaled_font("Arial", 11, "bold"), text_color=TEXT_MUTED)
        self.ledger_title.pack(anchor="w", padx=20, pady=(10, 5))

        self.ledger_container = ctk.CTkFrame(self.analytics_frame, fg_color="#0F172A", corner_radius=10, border_width=1, border_color=CARD_BORDER)
        self.ledger_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.ledger_items = {}
        self.create_ledger_row("Total Initial Investment (CAPEX)", "0 k€", "capex", is_bold=True)
        self.create_ledger_row("Grid & Site Installation cost", "3500 k€", "install")
        self.create_ledger_row("Annual O&M Operations Cost (OPEX)", "0 k€/yr", "opex")
        self.create_ledger_row("Annual Gross Savings / Revenue", "0 k€/yr", "savings")
        self.create_ledger_row("Weibull Scale Factor (A-parameter)", "0.0 m/s", "weibull")

    def create_header_card(self, title, val, color):
        card = ctk.CTkFrame(self.header_frame, fg_color="#1E293B", corner_radius=8, width=160, height=60)
        card.pack(side="right", padx=10, pady=15)
        card.pack_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=scaled_font("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(8, 1))
        val_lbl = ctk.CTkLabel(card, text=val, font=scaled_font("Arial", 16, "bold"), text_color=color)
        val_lbl.pack()
        
        return val_lbl

    def create_status_gauge(self, parent, col, title, initial_val, color):
        card = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=12, border_width=1, border_color="#2E3F59")
        card.grid(row=0, column=col, padx=8, pady=5, sticky="nsew")
        
        ctk.CTkLabel(card, text=title, font=scaled_font("Arial", 9, "bold"), text_color=TEXT_MUTED).pack(pady=(12, 4))
        
        # Gauge mockup
        val_lbl = ctk.CTkLabel(card, text=initial_val, font=scaled_font("Arial", 22, "bold"), text_color=color)
        val_lbl.pack(pady=(0, 12))
        
        return val_lbl

    def create_ledger_row(self, label_text, init_val, key, is_bold=False):
        row = ctk.CTkFrame(self.ledger_container, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=6)
        
        font_name = scaled_font("Arial", 12, "bold" if is_bold else "normal")
        color = TEXT_MAIN if is_bold else TEXT_MUTED
        
        ctk.CTkLabel(row, text=label_text, font=font_name, text_color=color).pack(side="left")
        
        val_lbl = ctk.CTkLabel(row, text=init_val, font=font_name, text_color=ACCENT_BLUE if key=="capex" else TEXT_MAIN)
        val_lbl.pack(side="right")
        self.ledger_items[key] = val_lbl

    # --- TAB SETUPS ---
    def setup_tab_location(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Identity
        ctk.CTkLabel(scroll, text="Designer Name", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.ent_name = ctk.CTkEntry(scroll, textvariable=self.name_var, fg_color="#1F2937", border_color=CARD_BORDER, font=scaled_font("Arial", 12))
        self.ent_name.pack(fill="x", pady=(2, 10))
        self.ent_name.bind("<KeyRelease>", lambda e: self.recalculate())

        ctk.CTkLabel(scroll, text="SSN (YYYYMMDDXXXX)", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.ent_ssn = ctk.CTkEntry(scroll, textvariable=self.ssn_var, fg_color="#1F2937", border_color=CARD_BORDER, font=scaled_font("Arial", 12))
        self.ent_ssn.pack(fill="x", pady=(2, 10))
        self.ent_ssn.bind("<KeyRelease>", lambda e: self.recalculate())

        # Presets for location
        ctk.CTkLabel(scroll, text="Location Wind Preset", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.opt_preset = ctk.CTkOptionMenu(scroll, values=["Forest Inland (High Roughness)", "Open Plains", "Coastal Winds", "Offshore (Ideal Wind)"], 
                                             variable=self.preset_var, command=self.on_preset_change, font=scaled_font("Arial", 12),
                                             fg_color="#1F2937", button_color="#374151")
        self.opt_preset.pack(fill="x", pady=(2, 10))

    def setup_tab_physical(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Sliders
        self.lbl_diam = ctk.CTkLabel(scroll, text="Rotor Diameter: 95.0 m", font=scaled_font("Arial", 12))
        self.lbl_diam.pack(anchor="w", pady=(5, 0))
        self.slider_diam = ctk.CTkSlider(scroll, from_=10, to=200, variable=self.diam_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_diam.pack(fill="x", pady=(2, 10))

        self.lbl_height = ctk.CTkLabel(scroll, text="Hub Height: 105.0 m", font=scaled_font("Arial", 12))
        self.lbl_height.pack(anchor="w", pady=(5, 0))
        self.slider_height = ctk.CTkSlider(scroll, from_=10, to=200, variable=self.height_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_height.pack(fill="x", pady=(2, 10))

        self.lbl_sol = ctk.CTkLabel(scroll, text="Rotor Solidity: 3.0%", font=scaled_font("Arial", 12))
        self.lbl_sol.pack(anchor="w", pady=(5, 0))
        self.slider_sol = ctk.CTkSlider(scroll, from_=1, to=15, variable=self.solidity_var, progress_color=ACCENT_BLUE, command=self.on_slider_change)
        self.slider_sol.pack(fill="x", pady=(2, 10))

        # Selectors
        ctk.CTkLabel(scroll, text="Blades Count", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.opt_blades = ctk.CTkSegmentedButton(scroll, values=["2 Blades", "3 Blades", "4 Blades"], variable=self.blades_var, command=self.on_segment_change,
                                                  selected_color=ACCENT_BLUE, selected_hover_color=ACCENT_BLUE, font=scaled_font("Arial", 12))
        self.opt_blades.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(scroll, text="Gearbox Type", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.opt_gearbox = ctk.CTkOptionMenu(scroll, values=["None (Direct Drive)", "Medium Ratio", "High-Speed Gearbox"], variable=self.gearbox_var, command=self.on_combo_change, font=scaled_font("Arial", 12))
        self.opt_gearbox.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(scroll, text="Generator Type", font=scaled_font("Arial", 11)).pack(anchor="w", pady=(5, 0))
        self.opt_generator = ctk.CTkOptionMenu(scroll, values=["Synchronous", "Asynchronous", "DFIG"], variable=self.generator_var, command=self.on_combo_change, font=scaled_font("Arial", 12))
        self.opt_generator.pack(fill="x", pady=(2, 10))

    def setup_tab_economics(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Financial Inputs
        self.lbl_price_elec = ctk.CTkLabel(scroll, text="Electricity Price: 29.0 €/MWh", font=scaled_font("Arial", 12))
        self.lbl_price_elec.pack(anchor="w", pady=(5, 0))
        self.slider_price_elec = ctk.CTkSlider(scroll, from_=10, to=150, variable=self.price_elec_var, progress_color=ACCENT_PURPLE, command=self.on_fin_change)
        self.slider_price_elec.pack(fill="x", pady=(2, 10))

        self.lbl_green_cert = ctk.CTkLabel(scroll, text="Green Certificate: 1.0 €/MWh", font=scaled_font("Arial", 12))
        self.lbl_green_cert.pack(anchor="w", pady=(5, 0))
        self.slider_green_cert = ctk.CTkSlider(scroll, from_=0, to=50, variable=self.green_cert_var, progress_color=ACCENT_PURPLE, command=self.on_fin_change)
        self.slider_green_cert.pack(fill="x", pady=(2, 10))

        self.lbl_lifetime = ctk.CTkLabel(scroll, text="Project Lifetime: 22.0 Years", font=scaled_font("Arial", 12))
        self.lbl_lifetime.pack(anchor="w", pady=(5, 0))
        self.slider_lifetime = ctk.CTkSlider(scroll, from_=10, to=30, variable=self.lifetime_var, progress_color=ACCENT_PURPLE, command=self.on_fin_change)
        self.slider_lifetime.pack(fill="x", pady=(2, 10))

        self.lbl_interest = ctk.CTkLabel(scroll, text="Interest Rate: 3.0 %", font=scaled_font("Arial", 12))
        self.lbl_interest.pack(anchor="w", pady=(5, 0))
        self.slider_interest = ctk.CTkSlider(scroll, from_=0, to=10, variable=self.interest_var, progress_color=ACCENT_PURPLE, command=self.on_fin_change)
        self.slider_interest.pack(fill="x", pady=(2, 10))

        self.lbl_inflation = ctk.CTkLabel(scroll, text="Inflation Rate: 2.0 %", font=scaled_font("Arial", 12))
        self.lbl_inflation.pack(anchor="w", pady=(5, 0))
        self.slider_inflation = ctk.CTkSlider(scroll, from_=0, to=8, variable=self.inflation_var, progress_color=ACCENT_PURPLE, command=self.on_fin_change)
        self.slider_inflation.pack(fill="x", pady=(2, 10))

    # --- ACTION HANDLERS ---
    def on_slider_change(self, val):
        self.lbl_diam.configure(text=f"Rotor Diameter: {self.diam_var.get():.1f} m")
        self.lbl_height.configure(text=f"Hub Height: {self.height_var.get():.1f} m")
        self.lbl_sol.configure(text=f"Rotor Solidity: {self.solidity_var.get():.1f}%")
        self.recalculate()

    def on_fin_change(self, val):
        self.lbl_price_elec.configure(text=f"Electricity Price: {self.price_elec_var.get():.1f} €/MWh")
        self.lbl_green_cert.configure(text=f"Green Certificate: {self.green_cert_var.get():.1f} €/MWh")
        self.lbl_lifetime.configure(text=f"Project Lifetime: {int(self.lifetime_var.get())} Years")
        self.lbl_interest.configure(text=f"Interest Rate: {self.interest_var.get():.1f} %")
        self.lbl_inflation.configure(text=f"Inflation Rate: {self.inflation_var.get():.1f} %")
        self.recalculate()

    def on_preset_change(self, choice):
        # Update slider values based on preset
        if choice == "Forest Inland (High Roughness)":
            self.price_elec_var.set(35.0) # Inland has higher price
        elif choice == "Coastal Winds":
            self.price_elec_var.set(29.0)
        elif choice == "Offshore (Ideal Wind)":
            self.price_elec_var.set(22.0) # lower grid prices sometimes
        self.on_fin_change(None)
        self.recalculate()

    def on_segment_change(self, choice):
        self.recalculate()

    def on_combo_change(self, choice):
        self.recalculate()

    # --- CALCULATIONS ---
    def recalculate(self):
        # Parse SSN gracefully
        ssn = self.ssn_var.get().strip()
        
        # Validations
        if len(ssn) != 12 or not ssn.isdigit():
            m_factor, d_factor, y_factor, pin_val = 1, 28, 1998, 1234
        else:
            try:
                y_factor = int(ssn[0:4])
                m_factor = int(ssn[4:6])
                d_factor = int(ssn[6:8])
                pin_val = int(ssn[8:12])
            except ValueError:
                m_factor, d_factor, y_factor, pin_val = 1, 28, 1998, 1234
                
        diam = self.diam_var.get()
        height = self.height_var.get()
        solidity = self.solidity_var.get()
        
        # Environmental params (deriving from SSN and selections)
        preset = self.preset_var.get()
        if preset == "Forest Inland (High Roughness)":
            roughness = 800.0 # mm
            wind_modifier = 0.8
        elif preset == "Open Plains":
            roughness = 100.0
            wind_modifier = 1.0
        elif preset == "Coastal Winds":
            roughness = 10.0
            wind_modifier = 1.15
        else: # Offshore
            roughness = 0.2
            wind_modifier = 1.35
            
        k_factor = (11 + m_factor) / 10
        avg_U10 = ((6 + d_factor / 10) - height / 50) * wind_modifier
        avg_U10 = max(2.5, avg_U10)
        
        z0 = roughness / 1000
        wind_nacelle = max(2.5, avg_U10 * math.log(max(1.1, height/z0)) / math.log(max(1.1, 10/z0)))
        
        # Model calculations
        swept_area = math.pi * (diam / 2) ** 2
        rated_speed = wind_nacelle * 1.5
        capture_efficiency = max(0.25, 0.54 - m_factor / 100)
        efficiency_drivetrain = max(0.6, 0.94 - (pin_val - round(pin_val, -2)) / 400)
        
        # Adjust with blades selection (blade counts change capture efficiency / solidity loads)
        blades = self.blades_var.get()
        if blades == "2 Blades":
            capture_efficiency -= 0.05
            solidity *= 0.7
        elif blades == "4 Blades":
            capture_efficiency += 0.02
            solidity *= 1.2
            
        rated_power = 0.62 * (rated_speed ** 3) * swept_area * capture_efficiency * efficiency_drivetrain / 1000
        
        # Capex modifications based on gearbox / generator
        gearbox = self.gearbox_var.get()
        generator = self.generator_var.get()
        
        capex_mod = 0.0
        if gearbox == "None (Direct Drive)":
            capex_mod += 1500
        elif gearbox == "High-Speed Gearbox":
            capex_mod += 300
            
        if generator == "DFIG":
            capex_mod += 500
        
        # Capex calculations (Breakdown parts)
        wo_param = 6 + m_factor / 6
        self.c_turbine = 900 * ((wo_param / 7.5) ** 3) * ((diam / 90) ** 3.5)
        self.c_drivetrain = 800 * (wo_param / 7) * (rated_power / 1000 / 3) * (diam / 90) + capex_mod
        self.c_tower = 700 * ((wo_param / 7) ** 2.5) * ((diam / 90) ** 2) * ((height / 90) ** 2) + 300
        self.c_foundation = 300 * math.sqrt((diam / 90) * (height / 100))
        self.c_install = 3500.0 # Grid connection constant
        
        total_capex = self.c_turbine + self.c_drivetrain + self.c_tower + self.c_foundation + self.c_install
        
        # O&M OPEX
        om = 600 * (rated_power / 1000) + 100 * math.sqrt(rated_power / 1000) + 360/28 + 200 * (rated_power / 1000)
        
        # Annual Savings
        downtime = abs(2000 - y_factor) + 1
        availability = (100 - downtime) / 100
        generated_energy = rated_power * 8760 * availability * 0.45 / 1000 # MWh
        
        price_elec = self.price_elec_var.get()
        price_green = self.green_cert_var.get()
        
        annual_income = generated_energy * 0.95 * (price_elec + price_green) / 1000 # k€
        savings = annual_income - om
        
        # Lifetime series
        interest = self.interest_var.get() / 100
        inflation = self.inflation_var.get() / 100
        lifetime = int(self.lifetime_var.get())
        
        k_fact = (1 + inflation) / (1 + interest)
        
        if k_fact != 1.0:
            npv = savings * (k_fact * (1 - k_fact ** lifetime)) / (1 - k_fact)
        else:
            npv = savings * lifetime
            
        financial_costs = 0.07 * total_capex
        profits = npv - total_capex - financial_costs
        margin = profits / total_capex if total_capex > 0 else 0
        
        # Payback period
        payback = total_capex / savings if savings > 0 else float('inf')
        
        # Safety Factor calculation (thickness)
        aero_load = 0.5 * 1.2 * (8/9) * swept_area * (rated_speed ** 2) / 1000
        storm_load = 0.5 * 1.2 * 1.5 * (solidity / 100) * swept_area * (60 ** 2) / 1000
        
        thick_op = (aero_load * height / (math.pi * ((height/40) ** 2) * 160) * 2) * 1000
        thick_storm = (storm_load * height / (math.pi * ((height/40) ** 2) * 160) * 2) * 1000
        
        safety_reserve = thick_op / thick_storm if thick_storm > 0 else 1.0
        
        # 1. Update Header Scores
        self.score_profit.configure(text=f"{profits:,.0f} k€")
        
        if payback == float('inf') or payback > 40:
            self.score_payback.configure(text="Never")
        else:
            self.score_payback.configure(text=f"{payback:.1f} Years")
            
        # Determine Grade
        ratio = height / diam
        if ratio > 4.0 or ratio < 0.4:
            grade = "F (Struc Risk)"
            grade_color = ACCENT_RED
        elif margin < 0:
            grade = "D (Loss)"
            grade_color = ACCENT_RED
        elif margin < 0.2:
            grade = "C (Marginal)"
            grade_color = ACCENT_YELLOW
        elif margin < 0.5:
            grade = "B (Healthy)"
            grade_color = ACCENT_BLUE
        else:
            grade = "A+ (Excellent)"
            grade_color = ACCENT_GREEN
            
        self.score_grade.configure(text=grade, text_color=grade_color)
        
        # Structure Safety Text
        if ratio > 4.0:
            safety_text = "Buckle Risk!"
            safety_color = ACCENT_RED
        elif ratio < 0.4:
            safety_text = "Clearance Risk"
            safety_color = ACCENT_RED
        elif safety_reserve < 0.8:
            safety_text = "Storm Warning"
            safety_color = ACCENT_YELLOW
        else:
            safety_text = "Optimal"
            safety_color = ACCENT_GREEN
        self.score_safety.configure(text=safety_text, text_color=safety_color)

        # 2. Update Gauges
        self.meter_roi.configure(text=f"{margin*100:.1f}%")
        
        wind_quality = "Poor"
        if wind_nacelle > 9.0:
            wind_quality = "Superb"
        elif wind_nacelle > 7.0:
            wind_quality = "Good"
        elif wind_nacelle > 5.0:
            wind_quality = "Moderate"
        self.meter_wind.configure(text=f"{wind_nacelle:.1f} m/s ({wind_quality})")
        self.meter_safety.configure(text=f"x{safety_reserve:.2f}")

        # 3. Update Ledger
        self.ledger_items["capex"].configure(text=f"{total_capex:,.0f} k€")
        self.ledger_items["opex"].configure(text=f"{om:,.1f} k€/yr")
        self.ledger_items["savings"].configure(text=f"{annual_income:,.1f} k€/yr")
        self.ledger_items["weibull"].configure(text=f"{wind_nacelle / 1.128:.2f} m/s") # approximation of scale factor A

        # 4. Redraw Cost breakdown bar
        self.draw_cost_bar()

    def draw_cost_bar(self):
        """
        Draws the visual CAPEX breakdown bar on the canvas.
        """
        if not hasattr(self, 'bar_canvas') or self.bar_canvas.winfo_width() < 10:
            return
            
        self.bar_canvas.delete("all")
        w = self.bar_canvas.winfo_width()
        h = self.bar_canvas.winfo_height()

        # Sum of capex
        totals = self.c_turbine + self.c_drivetrain + self.c_tower + self.c_foundation + self.c_install
        
        if totals <= 0:
            return
            
        # Segments
        segments = [
            ("Turbine", self.c_turbine, ACCENT_BLUE),
            ("Drivetrain", self.c_drivetrain, ACCENT_PURPLE),
            ("Tower", self.c_tower, ACCENT_YELLOW),
            ("Foundation", self.c_foundation, ACCENT_RED),
            ("Installation", self.c_install, ACCENT_GREEN)
        ]
        
        current_x = 0
        border_radius = 6
        
        # Draw background container
        for name, value, color in segments:
            percent = value / totals
            seg_w = percent * w
            
            if seg_w > 1:
                # Draw segment rectangle
                self.bar_canvas.create_rectangle(current_x, 0, current_x + seg_w, h, fill=color, outline="", width=0)
                current_x += seg_w
                
        # Update Legend Text with values in the legend_frame
        # Clear old widgets in legend_frame
        for widget in self.legend_frame.winfo_children():
            widget.destroy()
            
        self.legend_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        for idx, (name, value, color) in enumerate(segments):
            percent = (value / totals) * 100
            
            card = ctk.CTkFrame(self.legend_frame, fg_color="transparent")
            card.grid(row=0, column=idx, sticky="w")
            
            # Colored dot
            dot = ctk.CTkFrame(card, fg_color=color, corner_radius=4, width=int(8 * self.scale_factor), height=int(8 * self.scale_factor))
            dot.pack(side="left", padx=(0, 5))
            
            # Label
            ctk.CTkLabel(card, text=f"{name}: {percent:.0f}%", font=scaled_font("Arial", 10), text_color=TEXT_MUTED).pack(side="left")

if __name__ == "__main__":
    app = TycoonDashboardApp()
    app.mainloop()
