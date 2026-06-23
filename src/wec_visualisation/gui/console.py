# gui/console.py
import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
from wec_visualisation.models.mission import Mission
from wec_visualisation.models.turbine import WindTurbine
from wec_visualisation.models.environment import SiteEnvironment, SSNGenerator
from wec_visualisation.gui.theme import Theme
from wec_visualisation.models.turbine import Generator, Gearbox
from wec_visualisation.gui.components import LabeledSlider, MetricRow, TextInfoBox

class ConstraintRow(ctk.CTkFrame):
    """
    - Status symbol: green ✓ (passed), red ✗ (failed), or gray — (pending)
    - Constraint name (left)
    - Target requirement and/or actual evaluated value (right)
    """
    def __init__(self, parent, constraint_name: str, target_text: str, passed: bool | None, actual_text: str | None = None):
        super().__init__(parent, fg_color=Theme.BG_SURFACE.value)
        
        # Status Symbol (✓, ✗, —)
        if passed is None:
            symbol = "—"
            color = Theme.TEXT_MUTED.value
        elif passed:
            symbol = "✓"
            color = Theme.SUCCESS.value
        else:
            symbol = "✗"
            color = Theme.DANGER.value
            
        self.lbl_status = ctk.CTkLabel(
            self,
            text=symbol,
            font=(Theme.fonts.family, 14, "bold"),
            text_color=color,
            width=20,
            padx=0
        )
        self.lbl_status.pack(side="left", padx=(0, 5))
        
        # Constraint Name (Left-aligned)
        self.lbl_name = ctk.CTkLabel(
            self,
            text=constraint_name,
            font=Theme.fonts.BODY_BOLD,
            text_color=Theme.TEXT_MAIN.value,
            anchor="w",
            padx=0
        )
        self.lbl_name.pack(side="left", padx=5)
        
        # Detail / Result Text (Right-aligned)
        detail_text = actual_text if actual_text else f"Req: {target_text}"
        self.lbl_details = ctk.CTkLabel(
            self,
            text=detail_text,
            font=Theme.fonts.MUTED,
            text_color=Theme.TEXT_MUTED.value,
            anchor="e",
            justify="right",
            padx=0
        )
        self.lbl_details.pack(side="right", fill="x", expand=True, padx=(5, 0))


class ConsolePanel(ctk.CTkFrame):
    """
    A control console panel frame for the Wind Power Simulator.
    
    Provides tabbed views for input configuration (Physical Specs, Drivetrain)
    and a read-only list of environmental and economics variables.
    
    Attributes
    ----------
    turbine : WindTurbine
        The wind turbine configuration model.
    environment : SiteEnvironment
        The site environment configurations.
    on_change : Callable
        Callback function triggered when parameters change.
    on_ssn : Callable
        Callback function triggered when a valid SSN is entered.
    on_mission_change_callback : Callable
        Callback function triggered when the active mission changes.
    """

    def __init__(
        self, 
        parent, 
        turbine: WindTurbine, 
        environment: SiteEnvironment, 
        on_change_callback: Callable,
        on_ssn_callback: Callable,
        on_mission_change_callback: Callable,
        on_simulate_callback: Callable
    ):
        """
        Initialize the ConsolePanel.
        
        Parameters
        ----------
        parent : ctk.CTkFrame or ctk.CTk
            The parent Tkinter widget.
        turbine : WindTurbine
            The turbine model instance to modify.
        environment : SiteEnvironment
            The current environment properties instance.
        on_change_callback : Callable
            Triggered on slider/menu change.
        on_ssn_callback : Callable
            Triggered on valid SSN entry.
        on_mission_change_callback : Callable
            Triggered on mission selection change.
        """
        super().__init__(
            parent, 
            width=380, 
            fg_color=Theme.BG_SURFACE.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self._tracked_widgets = []
        self.turbine = turbine
        self.environment = environment
        self.on_change = on_change_callback
        self.on_ssn = on_ssn_callback
        self.on_mission_change_callback = on_mission_change_callback
        self.on_simulate = on_simulate_callback
        
        # Prevent auto-shrinking so panel stays exactly width=380
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Tkinter variables for managing GUI input state
        self.name_var = tk.StringVar(value="")
        self.ssn_var = tk.StringVar(value="")
        self.rotor_diameter_var = tk.DoubleVar(value=turbine.rotor_diameter)
        self.height_var = tk.DoubleVar(value=turbine.height)
        self.top_diameter_var = tk.DoubleVar(value=turbine.top_diameter)
        self.bottom_diameter_var = tk.DoubleVar(value=turbine.bottom_diameter)
        self.wall_thickness_var = tk.DoubleVar(value=turbine.wall_thickness * 1000.0)
        self.solidity_var = tk.DoubleVar(value=turbine.solidity * 100.0)
        self.gearbox_var = tk.StringVar(value=turbine.gearbox.value)
        self.generator_var = tk.StringVar(value=turbine.generator.value)

        self.create_widgets()

        # Bindings for input changes (replacing trace_add for CTkEntry placeholder fix)
        self.ent_name.bind("<KeyRelease>", lambda e: self.name_var.set(self.ent_name.get()))
        self.ent_ssn.bind("<KeyRelease>", self.on_ssn_trace)

        self.update_env_view()
        self.update_drivetrain_desc()

    def create_widgets(self):
        """
        Create and arrange GUI widgets inside the tab views.
        """
        # 1. Title Label
        self.lbl_title = ctk.CTkLabel(
            self, 
            text="CONTROL CONSOLE", 
            font=Theme.fonts.TITLE, 
            text_color=Theme.TEXT_ACCENT.value
        )
        self.lbl_title.pack(anchor="w", padx=15, pady=(15, 5))

        # 2. Main Tabs Widget
        self.tabs = ctk.CTkTabview(
            self, 
            fg_color=Theme.BG_SURFACE.value,
            segmented_button_fg_color=Theme.BOX_BG.value,
            segmented_button_selected_color=Theme.TAB_SELECTED.value,
            segmented_button_selected_hover_color=Theme.TAB_SELECTED_HOVER.value,
            segmented_button_unselected_color=Theme.BOX_BG.value,
            segmented_button_unselected_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        m_tab = self.tabs.add("Mission")
        
        # Main scrollable frame to prevent layout clipping and inner scrollbars
        self.mission_scroll = ctk.CTkScrollableFrame(m_tab, fg_color=Theme.BG_SURFACE.value)
        self.mission_scroll.pack(fill="both", expand=True)

        # Select Active Mission label
        lbl = ctk.CTkLabel(
            self.mission_scroll, 
            text="Select Active Mission:", 
            font=Theme.fonts.BODY_BOLD, 
            text_color=Theme.TEXT_MAIN.value
        )
        lbl.pack(anchor="w", padx=5, pady=(5, 2))
        self._tracked_widgets.append(lbl)
        
        self.mission_menu = ctk.CTkOptionMenu(
            self.mission_scroll, 
            values=[
                "Sandbox", 
                "The Arctic Gale", 
                "The Gentle Breeze", 
                "The Community Cooperative"
            ],
            command=self.on_mission_change_callback,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BUTTON_BG.value,
            button_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value,
            width=320,
            height=28,
            font=Theme.fonts.BODY
        )
        self.mission_menu.pack(anchor="w", padx=5, pady=(2, 10))
        
        # Mission Description frame
        self.info_mission = TextInfoBox(self.mission_scroll, "MISSION DESCRIPTION", height=70)
        self.info_mission.pack(fill="x", padx=5, pady=(0, 10))
        
        # Compact Environment & Economics Box
        self.env_box = ctk.CTkFrame(
            self.mission_scroll,
            fg_color=Theme.BOX_BG.value,
            corner_radius=6,
            border_width=1,
            border_color=Theme.BORDER.value
        )
        self.env_box.pack(fill="x", padx=5, pady=(0, 10))
        
        # Grid layout for compact parameters (4 rows x 4 columns)
        self.env_box.columnconfigure(0, weight=0) # Title 1
        self.env_box.columnconfigure(1, weight=1) # Value 1
        self.env_box.columnconfigure(2, weight=0) # Title 2
        self.env_box.columnconfigure(3, weight=1) # Value 2
        
        self.env_labels = {}
        env_params = [
            ("Site Type:", "site"), ("Elec. Price:", "price"),
            ("Wind (10m):", "wind"), ("Lifetime:", "lifetime"),
            ("Survival Gust:", "gust"), ("Downtime:", "downtime"),
            ("Roughness (z0):", "roughness"), ("Weibull k:", "weibull")
        ]
        
        for i, (title, key) in enumerate(env_params):
            row = i // 2
            col = (i % 2) * 2
            pady_top = 6 if row == 0 else 2
            pady_bot = 6 if row == 3 else 2
            
            lbl_t = ctk.CTkLabel(self.env_box, text=title, font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value)
            lbl_t.grid(row=row, column=col, padx=(10, 5), pady=(pady_top, pady_bot), sticky="w")
            self._tracked_widgets.append(lbl_t)
            
            lbl_v = ctk.CTkLabel(self.env_box, text="-", font=Theme.fonts.BODY, text_color=Theme.TEXT_MAIN.value)
            lbl_v.grid(row=row, column=col+1, padx=(0, 10), pady=(pady_top, pady_bot), sticky="w")
            self.env_labels[key] = lbl_v

        # Mission Constraints label
        lbl = ctk.CTkLabel(
            self.mission_scroll, 
            text="Mission Constraints:", 
            font=Theme.fonts.BODY_BOLD, 
            text_color=Theme.TEXT_MAIN.value
        )
        lbl.pack(anchor="w", padx=5, pady=(5, 0))
        self._tracked_widgets.append(lbl)
        
        # Regular frame (since parent is already scrollable, avoiding nested scrollbars)
        self.constraints_scroll = ctk.CTkFrame(
            self.mission_scroll, 
            fg_color=Theme.BG_SURFACE.value
        )
        self.constraints_scroll.pack(fill="x", expand=True, padx=5, pady=(0, 5))

        p_tab = self.tabs.add("Physical Specs")
        d_tab = self.tabs.add("Drivetrain")

        # ==========================================
        # TAB 1: PHYSICAL SPECS
        # ==========================================
        # Designer Name
        lbl = ctk.CTkLabel(p_tab, text="User Name", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value)
        lbl.pack(anchor="w", padx=5, pady=(2, 0))
        self._tracked_widgets.append(lbl)
        self.ent_name = ctk.CTkEntry(
            p_tab, 
            placeholder_text = "Forename Surname",
            height=26, 
            fg_color=Theme.BG_INPUT.value, 
            border_color=Theme.BORDER.value,
            text_color=Theme.TEXT_MAIN.value,
            placeholder_text_color=Theme.TEXT_MUTED.value
        )
        self.ent_name.pack(fill="x", padx=5, pady=(0, 2))

        # SSN Field
        ctk.CTkLabel(p_tab, text="SSN", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value).pack(anchor="w", padx=5, pady=(2, 0))
        self.ent_ssn = ctk.CTkEntry(
            p_tab, 
            placeholder_text = "YYYYMMDDXXXX",
            height=26, 
            fg_color=Theme.BG_INPUT.value, 
            border_color=Theme.BORDER.value,
            text_color=Theme.TEXT_MAIN.value,
            placeholder_text_color=Theme.TEXT_MUTED.value
        )
        self.ent_ssn.pack(fill="x", padx=5, pady=(0, 5))

        # Sliders
        self.sliders = {}
        main_sliders = [
            ("rotor_diameter", "Rotor Diameter: {value:.1f} m", self.rotor_diameter_var, 30, 150, 120),
            ("solidity", "Rotor Solidity: {value:.1f} %", self.solidity_var, 1, 10, 90)
        ]
        for key, title, var, min_v, max_v, steps in main_sliders:
            slider = LabeledSlider(p_tab, title, var, min_v, max_v, steps, self.on_slider_move)
            slider.pack(fill="x", padx=5, pady=1)
            self.sliders[key] = slider

        # Tower dimensions container
        self.tower_box = ctk.CTkFrame(
            p_tab, 
            fg_color=Theme.BOX_BG.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self.tower_box.pack(fill="x", padx=5, pady=(2, 5))

        lbl = ctk.CTkLabel(
            self.tower_box, 
            text="TOWER GEOMETRY", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.ACCENT.value
        )
        lbl.pack(anchor="w", padx=10, pady=(4, 2))
        self._tracked_widgets.append(lbl)

        tower_sliders = [
            ("height", "Hub Height: {value:.1f} m", self.height_var, 40, 160, 120),
            ("top_diam", "Top Diameter: {value:.2f} m", self.top_diameter_var, 1, 8, 65),
            ("bottom_diam", "Base Diameter: {value:.2f} m", self.bottom_diameter_var, 1, 12, 100),
            ("wall_thickness", "Wall Thickness: {value:.1f} mm", self.wall_thickness_var, 10, 250, 240)
        ]
        for key, title, var, min_v, max_v, steps in tower_sliders:
            slider = LabeledSlider(self.tower_box, title, var, min_v, max_v, steps, self.on_slider_move)
            pb = 5 if key == "wall_thickness" else 1
            slider.pack(fill="x", padx=10, pady=(0, pb))
            self.sliders[key] = slider

        # Action Button
        self.btn_simulate = ctk.CTkButton(
            p_tab, 
            text="RUN SIMULATION", 
            font=Theme.fonts.BODY_BOLD, 
            fg_color=Theme.BUTTON_BG.value, 
            hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value,
            height=34,
            command=self.on_simulate
        )
        self.btn_simulate.pack(fill="x", padx=5, pady=(20, 10))


        # ==========================================
        # TAB 2: DRIVETRAIN
        # ==========================================
        lbl = ctk.CTkLabel(
            d_tab, 
            text="POWER CONVERSION SYSTEM", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.TEXT_MUTED.value
        )
        lbl.pack(anchor="w", padx=5, pady=(10, 5))
        self._tracked_widgets.append(lbl)

        lbl = ctk.CTkLabel(d_tab, text="Gearbox Technology", font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value)
        lbl.pack(anchor="w", padx=5, pady=(10, 2))
        self._tracked_widgets.append(lbl)
        self.combo_gearbox = ctk.CTkOptionMenu(
            d_tab, 
            values=["None (Direct Drive)", "Medium-Speed", "High-Speed"],
            variable=self.gearbox_var,
            command=self.on_dropdown_select,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BORDER.value,
            button_hover_color=Theme.TEXT_ACCENT.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.combo_gearbox.pack(fill="x", padx=5, pady=(0, 15))

        lbl = ctk.CTkLabel(d_tab, text="Generator Type", font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value)
        lbl.pack(anchor="w", padx=5, pady=(10, 2))
        self._tracked_widgets.append(lbl)
        self.combo_generator = ctk.CTkOptionMenu(
            d_tab, 
            values=["Synchronous", "Asynchronous", "DFIG"],
            variable=self.generator_var,
            command=self.on_dropdown_select,
            fg_color=Theme.BG_INPUT.value,
            button_color=Theme.BORDER.value,
            button_hover_color=Theme.TEXT_ACCENT.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.combo_generator.pack(fill="x", padx=5, pady=(0, 15))

        # Drivetrain description frame
        self.info_drivetrain = TextInfoBox(d_tab, "DRIVETRAIN OVERVIEW", height=70)
        self.info_drivetrain.pack(fill="both", expand=True, padx=5, pady=10)





    # ==========================================
    # EVENT HANDLERS
    # ==========================================
    def on_slider_move(self, *args):
        """
        Handle slider movement events and update the turbine model.
        
        Parameters
        ----------
        *args : tuple
            Variable arguments from Tkinter event.
        """
        # Update model directly
        self.turbine.rotor_diameter = self.rotor_diameter_var.get()
        self.turbine.height = self.height_var.get()
        self.turbine.top_diameter = self.top_diameter_var.get()
        self.turbine.bottom_diameter = self.bottom_diameter_var.get()
        self.turbine.wall_thickness = self.wall_thickness_var.get() / 1000.0
        self.turbine.solidity = self.solidity_var.get() / 100.0

        # Notify parent app
        self.on_change()


    def on_dropdown_select(self, *args):
        """
        Handle dropdown selector events for gearbox and generator.
        
        Parameters
        ----------
        *args : tuple
            Variable arguments from Tkinter event.
        """
        self.turbine.gearbox = Gearbox(self.gearbox_var.get())
        self.turbine.generator = Generator(self.generator_var.get())
        self.update_drivetrain_desc()
        self.on_change()

    def on_ssn_trace(self, *args):
        """
        Trace and validate changes to the SSN entry field.
        
        Parameters
        ----------
        *args : tuple
            Variable arguments from Tkinter trace event.
        """
        ssn = self.ent_ssn.get()
        self.ssn_var.set(ssn)
        if SSNGenerator.validate(ssn):
            self.on_ssn(ssn)

    def update_from_models(self):
        """
        Update all GUI variables and elements to match current model values.
        """
        # 1. Update Tkinter variables from Turbine model
        self.rotor_diameter_var.set(self.turbine.rotor_diameter)
        self.height_var.set(self.turbine.height)
        self.top_diameter_var.set(self.turbine.top_diameter)
        self.bottom_diameter_var.set(self.turbine.bottom_diameter)
        self.wall_thickness_var.set(self.turbine.wall_thickness * 1000.0)
        self.solidity_var.set(self.turbine.solidity * 100.0)
        self.gearbox_var.set(self.turbine.gearbox.value)
        self.generator_var.set(self.turbine.generator.value)

        # Update physical spec labels via components
        for slider in self.sliders.values():
            slider.update_label()

        # Update views
        self.update_env_view()
        self.update_drivetrain_desc()

    def update_drivetrain_desc(self):
        """
        Update the informational description text for the selected drivetrain options.
        """
        self.info_drivetrain.set_text(self.turbine.generator_gearbox_description)

    def update_env_view(self):
        """
        Update the read-only display labels for environmental and economics values.
        """
        if not self.environment:
            return
        
        env = self.environment
        
        # Calculate hub-height average wind speed for visualization
        z0 = env.roughness / 1000.0
        # Check that we have a valid height to prevent math domain error
        height = self.turbine.height if self.turbine.height > 0 else 10.0
        if env.avg_wind_10 is not None and z0 > 0:
            wind_hub = env.avg_wind_10 * (math.log(height / z0) / math.log(10.0 / z0))
        else:
            wind_hub = 0.0

        # Update environment labels in the compact grid
        site_type = "Offshore" if env.is_offshore else "Onshore"
        self.env_labels["site"].configure(text=f"{site_type}")
        
        self.env_labels["price"].configure(
            text=f"{env.electricity_price:.1f} €/MWh" if env.electricity_price is not None else "- €/MWh"
        )
        self.env_labels["wind"].configure(
            text=f"{env.avg_wind_10:.1f} m/s" if env.avg_wind_10 else "- m/s"
        )
        self.env_labels["lifetime"].configure(
            text=f"{self.turbine.lifetime} years"
        )
        self.env_labels["gust"].configure(
            text=f"{env.survival_gust:.1f} m/s" if env.survival_gust else "- m/s"
        )
        self.env_labels["downtime"].configure(
            text=f"{self.turbine.downtime:.1f}%" if self.turbine.downtime is not None else "- %"
        )
        self.env_labels["roughness"].configure(
            text=f"{env.roughness:.2f} mm" if env.roughness else "- mm"
        )
        self.env_labels["weibull"].configure(
            text=f"{env.k_factor:.2f}" if env.k_factor else "-"
        )

    def update_mission_view(self, mission:Mission, report=None):
        """
        Updates the mission selection UI, active description, and constraints list.
        """
        self.mission_menu.set(mission.name)

        self.info_mission.set_text(mission.description)

        # Update the environment view for the current active mission
        self.update_env_view()

        # Clear existing constraints in the scroll container
        for child in self.constraints_scroll.winfo_children():
            child.destroy()

        if not mission.constraints:
            lbl = ctk.CTkLabel(
                self.constraints_scroll,
                text="No constraints for Sandbox mode.\nExplore parameters freely!",
                font=Theme.fonts.BODY,
                text_color=Theme.TEXT_MUTED.value,
                justify="center"
            )
            lbl.pack(pady=20, fill="x")
            self._tracked_widgets.append(lbl)
            return

        if report is None:
            # Show targets in pending state
            for c in mission.constraints:
                row = ConstraintRow(
                    self.constraints_scroll,
                    constraint_name=c.constraint_name,
                    target_text=f"{c.check} {c.target} {c.unit}",
                    passed=None
                )
                row.pack(fill="x", pady=1)
                self._tracked_widgets.append(row)
        else:
            # Show evaluations
            for eval_res in report.evaluations:
                row = ConstraintRow(
                    self.constraints_scroll,
                    constraint_name=eval_res.constraint_name,
                    target_text=eval_res.target_text,
                    passed=eval_res.passed,
                    actual_text=eval_res.actual_value_text
                )
                row.pack(fill="x", pady=1)
                self._tracked_widgets.append(row)

    def set_inputs_enabled(self, enabled: bool):
        """
        Enable or disable interactive widgets on the console panel.
        
        Parameters
        ----------
        enabled : bool
            True to enable inputs, False to disable.
        """
        state = "normal" if enabled else "disabled"
        self.mission_menu.configure(state=state)
        self.combo_gearbox.configure(state=state)
        self.combo_generator.configure(state=state)
        self.ent_name.configure(state=state)
        self.ent_ssn.configure(state=state)
        self.btn_simulate.configure(state=state)
        
        for slider in self.sliders.values():
            slider.configure_slider(state=state)