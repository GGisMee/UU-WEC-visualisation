# gui/app.py
import os
import customtkinter as ctk
import tkinter as tk
from PIL import Image
from wec_visualisation.models.turbine import WindTurbine, Generator, Gearbox
from wec_visualisation.gui.language import LanguageManager
from wec_visualisation.models.environment import SiteEnvironment, DefaultEnvironments, SSNGenerator
from wec_visualisation.models.simulation import SimulationEngine
from wec_visualisation.models.simulation import PresetConfigurations
from wec_visualisation.models.mission import DefaultMissions
from wec_visualisation.gui.console import ConsolePanel
from wec_visualisation.gui.canvas import CADCanvas
from wec_visualisation.gui.analytics import AnalyticsPanel
from wec_visualisation.gui.theme import Theme
from wec_visualisation.gui.components import ToolTip, ToastNotification



class UnifiedSimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING & LOOK SETUP ---
        self.scale_factor = 2
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
        self.language_var = ctk.StringVar(value="english")
        self.lang_manager = LanguageManager(default_lang="english")
        
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
            on_mission_change_callback=self.on_mission_change,
            on_simulate_callback=self.run_simulation,
            lang_manager=self.lang_manager
        )
        self.paned_window.add(self.console, minsize=380, stretch="never")

        self.cad_canvas = CADCanvas(
            self.paned_window, 
            self.turbine,
            lang_manager=self.lang_manager
        )
        self.paned_window.add(self.cad_canvas, minsize=400, stretch="always")

        self.analytics = AnalyticsPanel(
            self.paned_window,
            on_simulate_click=self.run_simulation,
            on_export_click=self.export_results,
            lang_manager=self.lang_manager
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
        
        mission_text_frame = ctk.CTkFrame(left_header, fg_color="transparent")
        mission_text_frame.pack(side="left")
        
        self.lbl_active_mission_title = ctk.CTkLabel(
            mission_text_frame, 
            text="ACTIVE MISSION", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.TEXT_MUTED.value,
            padx=0,
            height=12
        )
        self.lbl_active_mission_title.pack(anchor="w")
        
        self.lbl_active_mission = ctk.CTkLabel(
            mission_text_frame, 
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
        self.lbl_zoom = ctk.CTkLabel(scale_frame, text="ZOOM", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value)
        self.lbl_zoom.pack(anchor="w")
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
        self.lbl_theme = ctk.CTkLabel(theme_frame, text="THEME", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value)
        self.lbl_theme.pack(anchor="w")
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

        # Language Toggle
        lang_frame = ctk.CTkFrame(right_header, fg_color="transparent")
        lang_frame.pack(side="left", padx=(0, 15))
        self.lbl_lang = ctk.CTkLabel(lang_frame, text="LANG", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value)
        self.lbl_lang.pack(anchor="w")
        
        flag_name = self.lang_manager.get("flag_icon")
        if flag_name:
            icon_path = self.lang_manager.get_asset_path(os.path.join("assets", "icons", str(flag_name)))
            self.current_flag_img = ctk.CTkImage(
                light_image=Image.open(icon_path),
                size=(16, 16)
            )
        else:
            self.current_flag_img = None

        self.btn_language = ctk.CTkButton(
            lang_frame,
            text="",
            image=self.current_flag_img,
            command=self.toggle_language,
            width=30,
            height=24,
            fg_color=Theme.BG_INPUT.value,
            hover_color=Theme.BUTTON_HOVER.value,
        )
        self.btn_language.pack(anchor="w")

        # 1. R&D Runs Remaining Scorecard
        self.runs_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.runs_card.pack(side="left", padx=5)
        self.runs_card.pack_propagate(False)
        self.lbl_runs_title = ctk.CTkLabel(self.runs_card, text="R&D RUNS REMAINING", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0)
        self.lbl_runs_title.pack(pady=(10, 2))
        self.runs_tooltip = ToolTip(self.lbl_runs_title, "Number of simulation attempts left to successfully meet all mission constraints.", small=True)
        self.lbl_runs = ctk.CTkLabel(self.runs_card, text="∞ / ∞", font=Theme.fonts.TITLE, text_color=Theme.SUCCESS.value, height=22, pady=0, padx=0)
        self.lbl_runs.pack(pady=(0, 10))

        # 2. Constraints Met Scorecard
        self.constraints_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.constraints_card.pack(side="left", padx=5)
        self.constraints_card.pack_propagate(False)
        self.lbl_constraints_title = ctk.CTkLabel(self.constraints_card, text="CONSTRAINTS MET", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0)
        self.lbl_constraints_title.pack(pady=(10, 2))
        self.lbl_constraints_met = ctk.CTkLabel(self.constraints_card, text="N/A", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value, height=22, pady=0, padx=0)
        self.lbl_constraints_met.pack(pady=(0, 10))

        # 3. Lifetime Profit Scorecard
        self.profit_card = ctk.CTkFrame(right_header, fg_color=Theme.BG_INPUT.value, width=140, height=60, border_width=1, border_color=Theme.BORDER.value)
        self.profit_card.pack(side="left", padx=5)
        self.profit_card.pack_propagate(False)
        self.lbl_profit_title = ctk.CTkLabel(self.profit_card, text="LIFETIME PROFIT", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value, height=14, pady=0, padx=0)
        self.lbl_profit_title.pack(pady=(10, 2))
        self.lbl_profit = ctk.CTkLabel(self.profit_card, text="- k€", font=Theme.fonts.TITLE, text_color=Theme.TEXT_MUTED.value, height=22, pady=0, padx=0)
        self.lbl_profit.pack(pady=(0, 10))



    def toggle_language(self):
        if self.language_var.get() == "english":
            self.language_var.set("swedish")
            self.lang_manager.load_language("swedish")
        else:
            self.language_var.set("english")
            self.lang_manager.load_language("english")
        self.update_language()

    def update_flag_button(self):
        flag_name = self.lang_manager.get("flag_icon")
        if flag_name:
            icon_path = self.lang_manager.get_asset_path(os.path.join("assets", "icons", str(flag_name)))
            self.current_flag_img = ctk.CTkImage(
                light_image=Image.open(icon_path),
                size=(16, 16)
            )
            self.btn_language.configure(image=self.current_flag_img)

    def update_language(self):
        self.update_flag_button()
        
        # Update header labels
        self.lbl_active_mission_title.configure(text=self.lang_manager.get("header.lbl_active_mission"))
        self.lbl_zoom.configure(text=self.lang_manager.get("header.lbl_zoom"))
        self.lbl_theme.configure(text=self.lang_manager.get("header.lbl_theme"))
        self.lbl_lang.configure(text=self.lang_manager.get("header.lbl_lang"))
        
        self.lbl_runs_title.configure(text=self.lang_manager.get("header.lbl_runs"))
        if hasattr(self, 'runs_tooltip'):
            self.runs_tooltip.update_text(str(self.lang_manager.get("tooltips.runs", "Number of simulation attempts left to successfully meet all mission constraints.")))
            
        self.lbl_constraints_title.configure(text=self.lang_manager.get("header.lbl_constraints"))
        self.lbl_profit_title.configure(text=self.lang_manager.get("header.lbl_profit"))
        
        # Update Theme Dropdown Option values
        themes = self.lang_manager.get("themes", {})
        if isinstance(themes, dict):
            self.theme_menu.configure(values=[str(themes.get(k, k)) for k in ["Dark", "Light", "System"]])
            self._current_theme_eng = getattr(self, '_current_theme_eng', "System")
            self.theme_menu.set(str(themes.get(self._current_theme_eng, self._current_theme_eng)))
            
        # Propagate to console
        if hasattr(self, "console"):
            self.console.update_language()
            
        if hasattr(self, "cad_canvas"):
            self.cad_canvas.update_language()
            
        if hasattr(self, "analytics"):
            self.analytics.update_language()

    # ==========================================
    # CONTROLLER EVENT HANDLING
    # ==========================================
    def on_inputs_changed(self):
        """Called live when a slider, button, or dropdown in ConsolePanel is toggled."""
        self.cad_canvas.update_geometry()
        self.simulation_out_of_date = True
        self.analytics.show_warning_banner(True)

    def get_baseline_environment(self, mission_name: str) -> SiteEnvironment:
        if mission_name == "The Arctic Gale":
            return DefaultEnvironments.ARCTIC_GALE.create()
        elif mission_name == "The Gentle Breeze":
            return DefaultEnvironments.THE_GENTLE_BREEZE.create()
        elif mission_name == "The Community Cooperative":
            return DefaultEnvironments.THE_COMMUNITY_COOPERATIVE.create()
        return DefaultEnvironments.SANDBOX.create()

    def on_ssn_changed(self, ssn: str):
        """Called when a valid 12-digit SSN is entered in ConsolePanel."""
        baseline_env = self.get_baseline_environment(self.active_mission.name)
        self.environment.avg_wind_10 = baseline_env.avg_wind_10
        self.environment.roughness = baseline_env.roughness
        self.environment.survival_gust = baseline_env.survival_gust
        self.environment.k_factor = baseline_env.k_factor
        self.environment.electricity_price = baseline_env.electricity_price
        self.environment.green_certificate = baseline_env.green_certificate
        self.environment.inflation = baseline_env.inflation
        self.environment.interest = baseline_env.interest
        
        SSNGenerator.apply_ssn_to_env(ssn, self.environment)
        self.console.update_from_models()
        self.on_inputs_changed()
        self.console.info_mission.set_text(
            f"{self.active_mission.name}: Environment updated via birthdate (SSN month/day: {ssn[4:6]}/{ssn[6:8]}).\n"
            f"Avg. Wind: {self.environment.avg_wind_10:.1f} m/s, Roughness: {self.environment.roughness:.1f} mm."
        )

    def on_theme_change(self, choice: str):
        """Called when appearance mode selection changes in dropdown."""
        # Find english key since choice might be translated
        themes = self.lang_manager.get("themes", {})
        eng_choice = choice
        if isinstance(themes, dict):
            for k, v in themes.items():
                if v == choice:
                    eng_choice = k
                    break
        
        self._current_theme_eng = eng_choice
        ctk.set_appearance_mode(eng_choice.lower())
        # Let CustomTkinter propagate color updates before updating canvas drawings
        self.after(50, self.update_theme_drawings)

    def on_scale_dropdown(self, choice: str):
        pct = int(choice.replace("%", ""))
        self.apply_scale(pct / 100.0)

    def adjust_scale(self, delta):
        new_scale = self.scale_factor + delta
        self.apply_scale(new_scale)
        
    def reset_scale(self):
        self.apply_scale(2)

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
        
        ssn = self.console.ssn_var.get()
        if SSNGenerator.validate(ssn):
            self.on_ssn_changed(ssn)

    # ==========================================
    # SIMULATION EXECUTION LOOP
    # ==========================================
    def run_simulation(self):
        ssn = self.console.ssn_var.get()
        if not SSNGenerator.validate(ssn):
            ToastNotification(self, str(self.lang_manager.get("dialog.invalid_ssn_msg")), title=str(self.lang_manager.get("dialog.invalid_ssn_title")), is_err=True, duration=0)
            return

        # Check budget runs remaining
        if self.runs_remaining is not None and self.runs_remaining <= 0:
            ToastNotification(
                self, 
                str(self.lang_manager.get("dialog.out_of_budget_msg")),
                title=str(self.lang_manager.get("dialog.out_of_budget_title")), 
                is_err=True,
                duration=0
            )
            return

        # Disable controls during simulation
        self.console.set_inputs_enabled(False)
        self.analytics.show_loading(True, "Initializing wind tunnel aerodynamic grid...")

        # Step-by-step loading progress animation
        self.after(500, lambda: self.analytics.set_loading_status("Integrating wind speed probability using Weibull factors..."))
        self.after(1200, lambda: self.analytics.set_loading_status("Calculating beam bending moments on structural tower base...")) 
        self.after(2000, lambda: self.analytics.set_loading_status("Compiling financial CAPEX report and NPV margin predictions..."))
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

        # 2. Simulate calculations
        result = SimulationEngine.simulate(self.turbine, self.environment, PresetConfigurations.v0.value)
        self.last_sim_result = result
        self.simulation_out_of_date = False

        # 3. Update Views
        self.analytics.display_results(result, self.turbine.swept_area)
        
        # Unsafe check: buckling or breaking utilization exceeds 1.0
        is_unsafe = (result.buckling_utilization > 1.0) or (result.breaking_utilization > 1.0)
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
            ToastNotification(self, f"{self.lang_manager.get('dialog.mission_success_msg')}{details}", title=str(self.lang_manager.get("dialog.mission_success_title")), duration=0)
        elif self.runs_remaining == 0:
            tip = ""
            if self.active_mission.name == "The Arctic Gale":
                tip = str(self.lang_manager.get("dialog.tip_arctic"))
            elif self.active_mission.name == "The Gentle Breeze":
                tip = str(self.lang_manager.get("dialog.tip_breeze"))
            elif self.active_mission.name == "The Community Cooperative":
                tip = str(self.lang_manager.get("dialog.tip_community"))
                
            ToastNotification(
                self, 
                f"{self.lang_manager.get('dialog.mission_failed_msg')}{tip}",
                title=str(self.lang_manager.get("dialog.mission_failed_title")), 
                is_err=True,
                duration=0
            )


    def export_results(self):
        if not self.last_sim_result:
            ToastNotification(self, str(self.lang_manager.get("export.no_results", "No simulation results to export. Please run a simulation first.")), is_err=True)
            return

        import tkinter.filedialog as fd
        from wec_visualisation.models.output import Saver
        
        path = fd.askdirectory(title="Select Folder to Save Exported Results")
        if not path:
            return

        saver = Saver()
        
        # 1. TOML
        saver.toml.append("turbine.rotor_diameter", self.turbine.rotor_diameter)
        saver.toml.append("turbine.height", self.turbine.height)
        saver.toml.append("results.generated_energy", self.last_sim_result.generated_energy)
        saver.toml.append("results.npv_profit", self.last_sim_result.npv_profit)
        saver.toml.append("results.total_capex", self.last_sim_result.total_capex)
        saver.toml.append("results.capacity_factor", self.last_sim_result.capacity_factor)
        
        # 2. CSV
        if hasattr(self.last_sim_result, 'wind_speeds') and hasattr(self.last_sim_result, 'power_curve'):
            saver.csv.append(
                headers=["Wind Speed", "Power Curve"],
                rows=[[ws, p] for ws, p in zip(self.last_sim_result.wind_speeds, self.last_sim_result.power_curve)]
            )
        
        # 3. PDF and Plots
        saver.pdf.append("heading", "Wind Turbine Simulation Report")
        saver.pdf.append("text", f"Energy Output: {self.last_sim_result.generated_energy:.2f} GWh")
        saver.pdf.append("text", f"NPV Profit: {self.last_sim_result.npv_profit:.2f} k€")
        saver.pdf.append("text", f"Capacity Factor: {self.last_sim_result.capacity_factor*100:.1f}%")
        
        if hasattr(self.analytics, 'charts_fig'):
            saver.plots.append("performance_charts", self.analytics.charts_fig)
            saver.pdf.append("heading", "Performance Charts")
            saver.pdf.append("image", self.analytics.charts_fig)

        if hasattr(self.analytics, 'capex_fig'):
            saver.plots.append("capex_chart", self.analytics.capex_fig)
            saver.pdf.append("heading", "CAPEX Distribution")
            saver.pdf.append("image", self.analytics.capex_fig)
            
        try:
            saver.save(path)
            ToastNotification(self, f"{self.lang_manager.get('export.success', 'Results exported successfully to')}\n{path}/simulation_results.zip", duration=4000)
        except Exception as e:
            ToastNotification(self, f"{self.lang_manager.get('export.failed', 'Failed to Export:')}\n{str(e)}", is_err=True, duration=5000)

if __name__ == "__main__":
    app = UnifiedSimulatorApp()
    app.mainloop()
