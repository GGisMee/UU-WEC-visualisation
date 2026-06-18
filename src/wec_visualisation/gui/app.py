# gui/app.py
import os
import customtkinter as ctk
import tkinter as tk
from wec_visualisation.models.turbine import WindTurbine, Generator, Gearbox
from wec_visualisation.models.environment import SiteEnvironment, DefaultEnvironments, SSNGenerator
from wec_visualisation.models.simulation import SimulationEngine
from wec_visualisation.models.simulation import PresetConfigurations
from wec_visualisation.models.mission import DefaultMissions
from wec_visualisation.gui.console import ConsolePanel
from wec_visualisation.gui.canvas import CADCanvas
from wec_visualisation.gui.analytics import AnalyticsPanel
from wec_visualisation.gui.theme import Theme


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
        
    import platform
    if platform.system() == "Linux":
        try:
            import tkinter as tk
            temp_root = tk.Tk()
            temp_root.withdraw()
            dpi = temp_root.winfo_fpixels('1i')
            temp_root.destroy()
            scale = dpi / 96.0
            return max(1.0, min(scale, 3.0))
        except Exception:
            pass

    return 1.0  # Fallback to 1.0 and let OS native scaling handle it

class UnifiedSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING & LOOK SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)
        
        self.bind("<Control-plus>", lambda e: self.adjust_scale(0.25))
        self.bind("<Control-equal>", lambda e: self.adjust_scale(0.25))
        self.bind("<Control-minus>", lambda e: self.adjust_scale(-0.25))
        self.bind("<Control-0>", lambda e: self.reset_scale())
        self.bind("<Control-MouseWheel>", self.on_mousewheel_scale)
        
        self.title("Wind Power Simulator Pro")
        self.geometry("1200x750")
        self.minsize(1000, 700)
        self.configure(fg_color=Theme.BG_MAIN.value)
        ctk.set_appearance_mode("system")

        # --- STATE INITIALIZATION ---
        self.turbine = WindTurbine(
            rotor_diameter=95.0, 
            height=105.0, 
            top_diameter=1.5,
            bottom_diameter=2.6,
            solidity=0.035, 
            gearbox=Gearbox.MEDIUM_SPEED, 
            generator=Generator.DFIG
        )
        self.environment = DefaultEnvironments.SANDBOX.create()
        self.active_mission = DefaultMissions.SANDBOX.create(self.environment)
        self.runs_remaining = None
        self.simulation_out_of_date = True
        self.last_sim_result = None

        # --- LAYOUT GRID CONFIGURATION ---
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Core Workspace panels
        self.grid_columnconfigure(0, weight=1)

        # --- WIDGET CREATION ---
        self.create_header()

        mode_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        self.paned_window = tk.PanedWindow(
            self, 
            orient=tk.HORIZONTAL, 
            sashwidth=6,
            sashrelief=tk.FLAT,
            bg=Theme.BG_MAIN.value[mode_idx],
            bd=0
        )
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 10))

        # Instantiate modular panel frames
        self.console = ConsolePanel(
            self.paned_window,
            self.turbine,
            self.environment,
            on_change_callback=self.on_inputs_changed,
            on_ssn_callback=self.on_ssn_changed,
            on_mission_change_callback=self.on_mission_change
        )
        self.paned_window.add(self.console, minsize=380, stretch="never")

        self.cad_canvas = CADCanvas(
            self.paned_window, 
            self.turbine,
            on_simulate_click=self.run_simulation
        )
        self.paned_window.add(self.cad_canvas, minsize=400, stretch="always")

        self.analytics = AnalyticsPanel(
            self.paned_window,
            on_simulate_click=self.run_simulation
        )
        self.paned_window.add(self.analytics, minsize=420, stretch="never")

        # Apply initial values to console views
        self.on_mission_change("Sandbox")

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

        # Left Column: Active Mission Display
        left_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_header.grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        ctk.CTkLabel(
            left_header, 
            text="ACTIVE MISSION", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.TEXT_MUTED.value,
            padx=0,
            height=12
        ).pack(anchor="w")
        
        self.lbl_active_mission = ctk.CTkLabel(
            left_header, 
            text="Sandbox",
            font=Theme.fonts.TITLE,
            text_color=Theme.ACCENT.value,
            padx=0,
            height=20
        )
        self.lbl_active_mission.pack(anchor="w", pady=(2, 0))

        # Right Column: Theme selection + scorecards
        right_header = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_header.grid(row=0, column=1, sticky="e", padx=15, pady=10)

        # UI Scaling Dropdown
        scale_frame = ctk.CTkFrame(right_header, fg_color="transparent")
        scale_frame.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(scale_frame, text="ZOOM", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(anchor="w")
        self.scale_menu = ctk.CTkOptionMenu(
            scale_frame,
            values=["75%", "100%", "125%", "150%", "200%", "250%", "300%"],
            command=self.on_scale_dropdown,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BUTTON_BG.value,
            button_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value,
            width=80,
            height=24,
            font=Theme.fonts.MUTED
        )
        self.scale_menu.pack(anchor="w")
        
        # Determine initial selection based on self.scale_factor
        pct = int(self.scale_factor * 100)
        closest = min([75, 100, 125, 150, 200, 250, 300], key=lambda x: abs(x - pct))
        self.scale_menu.set(f"{closest}%")

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
        self.theme_menu.set("System")

        # 1. R&D Runs Remaining Scorecard
        self.runs_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.runs_card.pack(side="left", padx=5)
        self.runs_card.pack_propagate(False)
        ctk.CTkLabel(self.runs_card, text="R&D RUNS REMAINING", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0).pack(pady=(10, 2))
        self.lbl_runs = ctk.CTkLabel(self.runs_card, text="∞ / ∞", font=Theme.fonts.TITLE, text_color=Theme.SUCCESS.value, height=22, pady=0, padx=0)
        self.lbl_runs.pack(pady=(0, 10))

        # 2. Constraints Met Scorecard
        self.constraints_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.constraints_card.pack(side="left", padx=5)
        self.constraints_card.pack_propagate(False)
        ctk.CTkLabel(self.constraints_card, text="CONSTRAINTS MET", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0).pack(pady=(10, 2))
        self.lbl_constraints_met = ctk.CTkLabel(self.constraints_card, text="N/A", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value, height=22, pady=0, padx=0)
        self.lbl_constraints_met.pack(pady=(0, 10))

        # 3. Lifetime Profit Scorecard
        self.profit_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.profit_card.pack(side="left", padx=5)
        self.profit_card.pack_propagate(False)
        ctk.CTkLabel(self.profit_card, text="LIFETIME PROFIT", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0).pack(pady=(10, 2))
        self.lbl_profit = ctk.CTkLabel(self.profit_card, text="- k€", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value, height=22, pady=0, padx=0)
        self.lbl_profit.pack(pady=(0, 10))

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
        if self.active_mission.name == "Sandbox":
            SSNGenerator.apply_ssn_to_env(ssn, self.environment)
            self.console.update_from_models()
            self.on_inputs_changed()
            self.console.info_mission.set_text(
                f"Sandbox: Environment updated via birthdate (SSN month/day: {ssn[4:6]}/{ssn[6:8]}).\n"
                f"Medelvind: {self.environment.avg_wind_10:.1f} m/s, Råhet: {self.environment.roughness:.1f} mm."
            )

    def on_theme_change(self, choice: str):
        """Called when appearance mode selection changes in dropdown."""
        ctk.set_appearance_mode(choice.lower())
        # Let CustomTkinter propagate color updates before updating canvas drawings
        self.after(50, self.update_theme_drawings)

    def on_scale_dropdown(self, choice: str):
        pct = int(choice.replace("%", ""))
        self.apply_scale(pct / 100.0)

    def adjust_scale(self, delta):
        new_scale = self.scale_factor + delta
        self.apply_scale(new_scale)
        
    def reset_scale(self):
        self.apply_scale(load_scale_factor())

    def on_mousewheel_scale(self, event):
        if event.delta > 0:
            self.adjust_scale(0.1)
        elif event.delta < 0:
            self.adjust_scale(-0.1)

    def apply_scale(self, new_scale):
        new_scale = max(0.5, min(new_scale, 3.5))
        if abs(new_scale - self.scale_factor) < 0.01:
            return
            
        self.scale_factor = new_scale
        pct = int(self.scale_factor * 100)
        
        closest = min([75, 100, 125, 150, 200, 250, 300], key=lambda x: abs(x - pct))
        self.scale_menu.set(f"{closest}%")
        
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)
        self.after(50, self.update_theme_drawings)

    def update_theme_drawings(self):
        """Redraws manual tk.Canvas drawings with new theme color tokens."""
        self.configure(fg_color=Theme.BG_MAIN.value)
        mode_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        self.paned_window.configure(bg=Theme.BG_MAIN.value[mode_idx])
        self.cad_canvas.update_geometry()
        self.console.update_from_models()
        self.analytics.draw_performance_curves()
        self.analytics.redraw_capex_bar()

    def on_mission_change(self, choice: str):
        self.simulation_out_of_date = True
        self.analytics.show_warning_banner(True)

        # 1. Map selection names to Environment & Mission configurations
        if choice == "Sandbox":
            self.environment = DefaultEnvironments.SANDBOX.create()
            self.active_mission = DefaultMissions.SANDBOX.create(self.environment)
            self.runs_remaining = None
            self.lbl_runs.configure(text="∞ / ∞", text_color=Theme.SUCCESS.value)
        
        elif choice == "The Arctic Gale":
            self.environment = DefaultEnvironments.ARCTIC_GALE.create()
            self.active_mission = DefaultMissions.ARCTIC_GALE.create(self.environment)
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)
            
        elif choice == "The Gentle Breeze":
            self.environment = DefaultEnvironments.THE_GENTLE_BREEZE.create()
            self.active_mission = DefaultMissions.THE_GENTLE_BREEZE.create(self.environment)
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)

        elif choice == "The Community Cooperative":
            self.environment = DefaultEnvironments.THE_COMMUNITY_COOPERATIVE.create()
            self.active_mission = DefaultMissions.THE_COMMUNITY_COOPERATIVE.create(self.environment)
            self.runs_remaining = 6
            self.lbl_runs.configure(text="6 / 6", text_color=Theme.SUCCESS.value)

        # Update active mission display in topbar
        self.lbl_active_mission.configure(text=self.active_mission.name)

        # 2. Update panel child frames
        self.console.environment = self.environment
        self.console.update_from_models()
        self.console.update_mission_view(self.active_mission)
        self.analytics.clear_charts()
        self.cad_canvas.update_safety_state(False)

        # Reset scorecards
        self.lbl_constraints_met.configure(text="N/A", text_color=Theme.TEXT_MUTED.value)
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
                "You have used all 6 simulation runs for this mission.\nPlease select a new mission or restart.", 
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
        result = SimulationEngine.simulate(self.turbine, self.environment, PresetConfigurations.v0.value)
        self.last_sim_result = result
        self.simulation_out_of_date = False

        # 3. Update Views
        self.analytics.display_results(result, self.turbine.swept_area)
        
        # Unsafe check: buckling or breaking utilization exceeds 1.0
        is_unsafe = (result.buckeling_utilization > 1.0) or (result.breaking_utilization > 1.0)
        self.cad_canvas.update_safety_state(is_unsafe)

        # 4. Scorecard Updates
        self.lbl_profit.configure(
            text=f"{result.npv_profit:,.1f} k€", 
            text_color=Theme.SUCCESS.value if result.npv_profit >= 0 else Theme.DANGER.value
        )

        # 5. Evaluate Mission Targets
        report = self.active_mission.evaluate(self.turbine, result)
        self.console.update_mission_view(self.active_mission, report)

        # Update constraints met scorecard
        if len(self.active_mission.constraints) > 0:
            passed_count = sum(1 for e in report.evaluations if e.passed)
            total_count = len(report.evaluations)
            color = Theme.SUCCESS.value if passed_count == total_count else Theme.DANGER.value
            self.lbl_constraints_met.configure(text=f"{passed_count} / {total_count}", text_color=color)
        else:
            self.lbl_constraints_met.configure(text="N/A", text_color=Theme.TEXT_MUTED.value)

        self.check_mission_targets(report)

    def check_mission_targets(self, report):
        if not self.active_mission.constraints:
            return

        if report.success:
            details = "\n".join([f"• {e.actual_value_text}" for e in report.evaluations])
            self.show_dialog(
                "Mission Accomplished!", 
                f"Congratulations! You successfully designed a WEC that meets all criteria.\n\n"
                f"{details}"
            )
        elif self.runs_remaining == 0:
            tip = ""
            if self.active_mission.name == "The Arctic Gale":
                tip = "TIP: The storm bending moments are too high. Try reducing Rotor Solidity or Rotor Diameter to decrease wind surface area and load."
            elif self.active_mission.name == "The Gentle Breeze":
                tip = "TIP: To increase power in low-wind regimes, you need a larger Rotor Diameter. To stay under budget, keep the Hub Height compact and choose a cost-effective Drivetrain."
            elif self.active_mission.name == "The Community Cooperative":
                tip = "TIP: To keep structure safe onshore, avoid extreme heights and large rotor diameters. Optimize rotor diameter slightly for maximum revenue at low storm loads."
                
            self.show_dialog(
                "Mission Failed", 
                f"You ran out of simulation runs without meeting the criteria.\n\n{tip}", 
                is_err=True
            )

    def show_dialog(self, title, message, is_err=False):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x240")
        dialog.configure(fg_color=Theme.BG_SURFACE.value)
        
        # Modal configuration
        dialog.transient(self)
        
        # Delay grab_set and focus_set to prevent blank/white window bugs on some OS
        dialog.after(100, dialog.focus_set)
        dialog.after(150, dialog.grab_set)

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