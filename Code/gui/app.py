# gui/app.py
import os
import customtkinter as ctk
import tkinter as tk
from models.turbine import WindTurbine, Generator, Gearbox
from models.environment import SiteEnvironment, DefaultEnvironments, SSNGenerator
from models.simulation import SimulationEngine
from models.mission import DefaultMissions
from gui.console import ConsolePanel
from gui.canvas import CADCanvas
from gui.analytics import AnalyticsPanel
from gui.theme import Theme

def load_scale_factor():
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        scale_path = os.path.join(dir_path, "scale.txt")
        if not os.path.exists(scale_path):
            scale_path = os.path.join(dir_path, "..", "Code", "prototypes", "scale.txt")
        if os.path.exists(scale_path):
            with open(scale_path, "r") as f:
                return float(f.read().strip())
    except Exception:
        pass
    return 1.35  # Fallback to comfortable scaling

class UnifiedSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING & LOOK SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)
        
        self.title("Wind Power Simulator Pro")
        self.geometry("1200x750")
        self.configure(fg_color=Theme.BG_MAIN.value)
        ctk.set_appearance_mode("dark")

        # --- STATE INITIALIZATION ---
        self.turbine = WindTurbine(
            rotor_diameter=95.0, 
            height=105.0, 
            top_diameter=1.5,
            bottom_diameter=2.6,
            solidity=3.5, 
            blades=3, 
            gearbox=Gearbox.MEDIUM_SPEED, 
            generator=Generator.DFIG
        )
        self.environment = DefaultEnvironments.SANDBOX.create()
        self.active_mission_name = "Free Play Sandbox"
        self.runs_remaining = None
        self.simulation_out_of_date = True
        self.last_sim_result = None

        # --- LAYOUT GRID CONFIGURATION ---
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Core Workspace panels
        self.grid_columnconfigure(0, weight=0)  # Left Console (width=320)
        self.grid_columnconfigure(1, weight=1)  # Center CAD Drawing
        self.grid_columnconfigure(2, weight=0)  # Right Analytics (width=420)

        # --- WIDGET CREATION ---
        self.create_header()

        # Instantiate modular panel frames
        self.console = ConsolePanel(
            self,
            self.turbine,
            self.environment,
            on_change_callback=self.on_inputs_changed,
            on_ssn_callback=self.on_ssn_changed
        )
        self.console.grid(row=1, column=0, sticky="nsw", padx=(10, 5), pady=(5, 10))

        self.cad_canvas = CADCanvas(
            self, 
            self.turbine,
            on_simulate_click=self.run_simulation
        )
        self.cad_canvas.grid(row=1, column=1, sticky="nsew", padx=5, pady=(5, 10))

        self.analytics = AnalyticsPanel(
            self,
            on_simulate_click=self.run_simulation
        )
        self.analytics.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=(5, 10))

        # Apply initial values to console views
        self.on_mission_change("Free Play Sandbox")

    def create_header(self):
        # Header main container
        self.header_frame = ctk.CTkFrame(
            self, 
            fg_color=Theme.BG_SURFACE.value, 
            corner_radius=0, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        # Left Column: Mission selector dropdown & description label
        left_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        ctk.CTkLabel(
            left_header, 
            text="MISSION / CHALLENGE SELECTOR", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.ACCENT.value
        ).pack(anchor="w")
        
        self.mission_menu = ctk.CTkOptionMenu(
            left_header, 
            values=[
                "Free Play Sandbox", 
                "The Arctic Gale", 
                "The Gentle Breeze", 
                "The Community Cooperative"
            ],
            command=self.on_mission_change,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BUTTON_BG.value,
            button_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value,
            width=220,
            height=28,
            font=Theme.fonts.BODY
        )
        self.mission_menu.pack(anchor="w", pady=(2, 5))
        
        self.lbl_mission_desc = ctk.CTkLabel(
            left_header, 
            text="",
            font=Theme.fonts.BODY,
            text_color=Theme.TEXT_MUTED.value,
            justify="left"
        )
        self.lbl_mission_desc.pack(anchor="w")

        # Right Column: Theme selection + scorecards
        right_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_header.grid(row=0, column=1, sticky="e", padx=15, pady=10)

        # Theme Selector Dropdown
        theme_frame = ctk.CTkFrame(right_header, fg_color="transparent")
        theme_frame.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(theme_frame, text="THEME", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(anchor="w")
        self.theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            command=self.on_theme_change,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BUTTON_BG.value,
            button_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value,
            width=90,
            height=24,
            font=Theme.fonts.MUTED
        )
        self.theme_menu.pack(anchor="w")
        self.theme_menu.set("Dark")

        # 1. R&D Runs Remaining Scorecard
        self.runs_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=130, height=52, border_width=1, border_color=Theme.BORDER.value)
        self.runs_card.pack(side="left", padx=5)
        self.runs_card.pack_propagate(False)
        ctk.CTkLabel(self.runs_card, text="R&D RUNS REMAINING", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(pady=(4, 0))
        self.lbl_runs = ctk.CTkLabel(self.runs_card, text="∞ / ∞", font=Theme.fonts.TITLE, text_color=Theme.SUCCESS.value)
        self.lbl_runs.pack()

        # 2. Design Grade Scorecard
        self.grade_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=100, height=52, border_width=1, border_color=Theme.BORDER.value)
        self.grade_card.pack(side="left", padx=5)
        self.grade_card.pack_propagate(False)
        ctk.CTkLabel(self.grade_card, text="DESIGN GRADE", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(pady=(4, 0))
        self.lbl_grade = ctk.CTkLabel(self.grade_card, text="N/A", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value)
        self.lbl_grade.pack()

        # 3. Lifetime Profit Scorecard
        self.profit_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=52, border_width=1, border_color=Theme.BORDER.value)
        self.profit_card.pack(side="left", padx=5)
        self.profit_card.pack_propagate(False)
        ctk.CTkLabel(self.profit_card, text="LIFETIME PROFIT", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(pady=(4, 0))
        self.lbl_profit = ctk.CTkLabel(self.profit_card, text="- k€", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value)
        self.lbl_profit.pack()

    # ==========================================
    # CONTROLLER EVENT HANDLING
    # ==========================================
    def on_inputs_changed(self):
        """Called live when a slider, button, or dropdown in ConsolePanel is toggled."""
        self.cad_canvas.update_geometry()
        self.simulation_out_of_date = True
        self.analytics.show_warning_banner(True)

    def on_ssn_changed(self, ssn: str):
        """Called when a valid 12-digit SSN is entered in ConsolePanel."""
        if self.active_mission_name == "Free Play Sandbox":
            SSNGenerator.apply_ssn_to_env(ssn, self.environment)
            self.console.update_from_models()
            self.on_inputs_changed()
            self.console.set_objectives_text(
                f"Sandbox: Environment updated via birthdate (SSN month/day: {ssn[4:6]}/{ssn[6:8]}). "
                f"Medelvind: {self.environment.avg_wind_10:.1f} m/s, Råhet: {self.environment.roughness:.1f} mm."
            )

    def on_theme_change(self, choice: str):
        """Called when appearance mode selection changes in dropdown."""
        ctk.set_appearance_mode(choice.lower())
        # Let CustomTkinter propagate color updates before updating canvas drawings
        self.after(50, self.update_theme_drawings)

    def update_theme_drawings(self):
        """Redraws manual tk.Canvas drawings with new theme color tokens."""
        self.configure(fg_color=Theme.BG_MAIN.value)
        self.cad_canvas.update_geometry()
        self.console.update_from_models()
        self.analytics.draw_performance_curves()
        self.analytics.redraw_capex_bar()

    def on_mission_change(self, choice: str):
        self.active_mission_name = choice
        self.simulation_out_of_date = True
        self.analytics.show_warning_banner(True)

        # 1. Map selection names to Environment & Mission configurations
        if choice == "Free Play Sandbox":
            self.environment = DefaultEnvironments.SANDBOX.create()
            self.runs_remaining = None
            self.lbl_runs.configure(text="∞ / ∞", text_color=Theme.SUCCESS.value)
            self.lbl_mission_desc.configure(text="Free Play Sandbox: Explore WEC layouts with no run limits.")
            # Set default turbine properties
        
        elif choice == "The Arctic Gale":
            self.environment = DefaultEnvironments.ARCTIC_GALE.create()
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)
            self.lbl_mission_desc.configure(
                text="Mission A: Design a storm-hardened offshore WEC. Goal: Safety Margin >= 1.0 (mean thickness <= 150mm) AND Profit Margin >= 10%. Max 6 runs!"
            )
            
        elif choice == "The Gentle Breeze":
            self.environment = DefaultEnvironments.THE_GENTLE_BREEZE.create()
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)
            self.lbl_mission_desc.configure(
                text="Mission B: Optimize for low-wind forest site. Goal: Energy >= 1,800 MWh AND Capacity Factor >= 35% AND CAPEX < 5,000 k€. Max 6 runs!"
            )


        elif choice == "The Community Cooperative":
            self.environment = DefaultEnvironments.THE_COMMUNITY_COOPERATIVE.create()
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)
            self.lbl_mission_desc.configure(
                text="Mission C: Build a community WEC. Goal: Profit Margin >= 5% AND Mean Wall Thickness <= 120.0 mm. Max 6 runs!"
            )
        # 2. Update panel child frames
        self.console.environment = self.environment
        self.console.update_from_models()
        self.console.set_objectives_text(self.lbl_mission_desc.cget("text"))
        self.analytics.clear_charts()
        self.cad_canvas.update_safety_state(False)

        # Reset scorecards
        self.lbl_grade.configure(text="N/A", text_color=Theme.TEXT_MUTED.value)
        self.lbl_profit.configure(text="- k€", text_color=Theme.TEXT_MUTED.value)
        
        self.on_inputs_changed()

    # ==========================================
    # SIMULATION EXECUTION LOOP
    # ==========================================
    def run_simulation(self):
        # Check budget runs remaining
        if self.runs_remaining is not None and self.runs_remaining <= 0:
            self.show_dialog(
                "Out of R&D Budget", 
                "You have used all 6 simulation runs for this challenge.\nPlease select a new mission or restart.", 
                is_err=True
            )
            return

        # Disable controls during simulation
        self.console.set_inputs_enabled(False)
        self.analytics.show_loading(True, "Initializing wind tunnel aerodynamic grid...")

        # Step-by-step loading progress animation
        self.after(500, lambda: self.analytics.set_loading_status("Integrating wind speed probability using Weibull factors..."))
        self.after(1200, lambda: self.analytics.set_loading_status("Calculating beam bending moments on structural tower base..."))
        self.after(2000, lambda: self.analytics.set_loading_status("Compiling financial CAPEX ledger and NPV margin predictions..."))
        self.after(3000, self.complete_simulation)

    def complete_simulation(self):
        # Re-enable inputs
        self.console.set_inputs_enabled(True)
        self.analytics.show_loading(False)

        # 1. Decrement runs if applicable
        if self.runs_remaining is not None:
            self.runs_remaining -= 1
            color = Theme.SUCCESS.value if self.runs_remaining >= 4 else (Theme.ALERT.value if self.runs_remaining >= 2 else Theme.DANGER.value)
            self.lbl_runs.configure(text=f"{self.runs_remaining} / 6", text_color=color)

        # 2. Run simulation calculations
        result = SimulationEngine.simulate(self.turbine, self.environment)
        self.last_sim_result = result
        self.simulation_out_of_date = False

        # 3. Update Views
        self.analytics.display_results(result)
        
        # Unsafe check: mean wall thickness > 150mm limit
        is_unsafe = result.mean_wall_thickness > 150.0
        self.cad_canvas.update_safety_state(is_unsafe)

        # 4. Grade & Profit Scorecard Updates
        margin_pct = result.margin * 100.0
        grade = "C"
        grade_color = Theme.TEXT_MAIN.value
        
        if is_unsafe:
            grade = "F"
            grade_color = Theme.DANGER.value
        elif result.npv_profit < 0:
            grade = "D"
            grade_color = Theme.DANGER.value
        else:
            if margin_pct >= 25.0:
                grade = "A+"
                grade_color = Theme.SUCCESS.value
            elif margin_pct >= 15.0:
                grade = "A"
                grade_color = Theme.SUCCESS.value
            elif margin_pct >= 5.0:
                grade = "B"
                grade_color = Theme.INFO.value

        self.lbl_grade.configure(text=grade, text_color=grade_color)
        self.lbl_profit.configure(
            text=f"{result.npv_profit:,.1f} k€", 
            text_color=Theme.SUCCESS.value if result.npv_profit >= 0 else Theme.DANGER.value
        )

        # 5. Evaluate Mission Targets
        self.check_mission_targets(result)

    def check_mission_targets(self, result):
        if self.active_mission_name == "Free Play Sandbox":
            return

        margin_pct = result.margin * 100.0
        thick = result.mean_wall_thickness
        profits = result.npv_profit

        if self.active_mission_name == "The Arctic Gale":
            success = (thick <= 150.0) and (margin_pct >= 10.0) and (profits > 0)
            if success:
                self.show_dialog(
                    "Mission Accomplished!", 
                    f"Congratulations! You successfully designed an offshore WEC that can survive arctic storm gusts.\n\n"
                    f"• Mean Wall Thickness: {thick:.1f} mm (Required: <= 150 mm)\n"
                    f"• Profit Margin: {margin_pct:.1f}% (Required: >= 10.0%)\n"
                    f"• Lifetime Profit: {profits:,.1f} k€"
                )
            elif self.runs_remaining == 0:
                self.show_dialog(
                    "Mission Failed", 
                    "You ran out of simulation runs without meeting the criteria.\n\n"
                    "TIP: The storm bending moments are too high. "
                    "Try reducing Rotor Solidity or Rotor Diameter to decrease wind surface area and load.", 
                    is_err=True
                )
            else:
                self.show_dialog(
                    "Simulation Complete",
                    f"Objectives not yet fully met.\n\n"
                    f"• Mean Wall Thickness: {thick:.1f} / 150 mm {'(OK)' if thick <= 150 else '(FAILED)'}\n"
                    f"• Profit Margin: {margin_pct:.1f}% / 10.0% {'(OK)' if margin_pct >= 10.0 else '(FAILED)'}\n\n"
                    f"Runs Remaining: {self.runs_remaining}. Adjust parameters and try again!", 
                    is_err=True
                )

        elif self.active_mission_name == "The Gentle Breeze":
            aep = result.generated_energy
            cf_pct = result.capacity_factor * 100.0
            tot_capex = result.total_capex
            
            success = (aep >= 1800.0) and (cf_pct >= 35.0) and (tot_capex < 5000.0)
            if success:
                self.show_dialog(
                    "Mission Accomplished!", 
                    f"Excellent work! You engineered a low-wind turbine that hits both energy and budget targets.\n\n"
                    f"• Energy Generated: {aep:,.1f} MWh (Required: >= 1,800 MWh)\n"
                    f"• Capacity Factor: {cf_pct:.1f}% (Required: >= 35.0%)\n"
                    f"• Total CAPEX: {tot_capex:,.1f} k€ (Required: < 5,000 k€)"
                )
            elif self.runs_remaining == 0:
                self.show_dialog(
                    "Mission Failed", 
                    "You ran out of simulation runs without meeting the criteria.\n\n"
                    "TIP: To increase power in low-wind regimes, you need a larger Rotor Diameter. "
                    "To stay under budget, keep the Hub Height compact and choose a cost-effective Drivetrain.", 
                    is_err=True
                )
            else:
                self.show_dialog(
                    "Simulation Complete",
                    f"Objectives not yet fully met.\n\n"
                    f"• Energy Generated: {aep:,.1f} / 1,800 MWh {'(OK)' if aep >= 1800.0 else '(FAILED)'}\n"
                    f"• Capacity Factor: {cf_pct:.1f}% / 35.0% {'(OK)' if cf_pct >= 35.0 else '(FAILED)'}\n"
                    f"• Total CAPEX: {tot_capex:,.1f} / 5,000 k€ {'(OK)' if tot_capex < 5000.0 else '(FAILED)'}\n\n"
                    f"Runs Remaining: {self.runs_remaining}. Adjust parameters and try again!", 
                    is_err=True
                )

        elif self.active_mission_name == "The Community Cooperative":
            success = (margin_pct >= 5.0) and (thick <= 120.0)
            if success:
                self.show_dialog(
                    "Mission Accomplished!", 
                    f"Excellent work! You engineered a community-friendly WEC that is safe and profitable.\n\n"
                    f"• Mean Wall Thickness: {thick:.1f} mm (Required: <= 120 mm)\n"
                    f"• Profit Margin: {margin_pct:.1f}% (Required: >= 5.0%)\n"
                    f"• Lifetime Profit: {profits:,.1f} k€"
                )
            elif self.runs_remaining == 0:
                self.show_dialog(
                    "Mission Failed", 
                    "You ran out of simulation runs without meeting the criteria.\n\n"
                    "TIP: To keep thickness low onshore, avoid extreme heights and large rotor diameters. "
                    "Optimize rotor diameter slightly for maximum revenue at low storm loads.", 
                    is_err=True
                )
            else:
                self.show_dialog(
                    "Simulation Complete",
                    f"Objectives not yet fully met.\n\n"
                    f"• Mean Wall Thickness: {thick:.1f} / 120 mm {'(OK)' if thick <= 120 else '(FAILED)'}\n"
                    f"• Profit Margin: {margin_pct:.1f}% / 5.0% {'(OK)' if margin_pct >= 5.0 else '(FAILED)'}\n\n"
                    f"Runs Remaining: {self.runs_remaining}. Adjust parameters and try again!", 
                    is_err=True
                )

    def show_dialog(self, title, message, is_err=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x240")
        dialog.configure(fg_color=Theme.BG_SURFACE.value)
        
        # Modal configuration
        dialog.transient(self)
        dialog.grab_set()

        title_color = Theme.DANGER.value if is_err else Theme.SUCCESS.value
        ctk.CTkLabel(dialog, text=title.upper(), font=Theme.fonts.SUBTITLE, text_color=title_color).pack(pady=(15, 10))
        
        tb = ctk.CTkTextbox(dialog, fg_color="transparent", text_color=Theme.TEXT_MAIN.value, font=Theme.fonts.BODY, wrap="word", width=380, height=120)  # type: ignore
        tb.pack(padx=15, pady=5)
        tb.insert("0.0", message)
        tb.configure(state="disabled")

        ctk.CTkButton(
            dialog, 
            text="Close", 
            width=120, 
            height=28, 
            fg_color=Theme.BUTTON_BG.value, 
            text_color=Theme.TEXT_MAIN.value, 
            hover_color=Theme.BUTTON_HOVER.value, 
            command=dialog.destroy,
            font=Theme.fonts.MUTED_BOLD
        ).pack(pady=10)