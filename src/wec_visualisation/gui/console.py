# gui/console.py
import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
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
        on_mission_change_callback: Callable
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
        
        # Prevent auto-shrinking so panel stays exactly width=380
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Tkinter variables for managing GUI input state
        self.name_var = tk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = tk.StringVar(value="199801281234")
        self.rotor_diameter_var = tk.DoubleVar(value=turbine.rotor_diameter)
        self.height_var = tk.DoubleVar(value=turbine.height)
        self.top_diameter_var = tk.DoubleVar(value=turbine.top_diameter)
        self.bottom_diameter_var = tk.DoubleVar(value=turbine.bottom_diameter)
        self.wall_thickness_var = tk.DoubleVar(value=turbine.wall_thickness * 1000.0)
        self.solidity_var = tk.DoubleVar(value=turbine.solidity)
        self.blades_var = tk.StringVar(value=f"{turbine.blades} Blades")
        self.gearbox_var = tk.StringVar(value=turbine.gearbox.value)
        self.generator_var = tk.StringVar(value=turbine.generator.value)

        # Tracers for input changes
        self.ssn_var.trace_add("write", self.on_ssn_trace)

        self.create_widgets()
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
                "Free Play Sandbox", 
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
        
        # Grid layout for compact parameters (5 rows x 2 columns)
        self.env_box.columnconfigure(0, weight=1)
        self.env_box.columnconfigure(1, weight=1)
        
        # Row 0: Site Type & Elec Price
        self.lbl_env_site = ctk.CTkLabel(self.env_box, text="Site Type: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_site.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="w")
        
        self.lbl_env_price = ctk.CTkLabel(self.env_box, text="Elec. Price: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_price.grid(row=0, column=1, padx=10, pady=(6, 2), sticky="w")
        
        # Row 1: Avg Wind (10m) & Lifetime
        self.lbl_env_wind = ctk.CTkLabel(self.env_box, text="Wind (10m): -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_wind.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        self.lbl_env_lifetime = ctk.CTkLabel(self.env_box, text="Lifetime: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_lifetime.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        # Row 2: Survival Gust & Downtime
        self.lbl_env_gust = ctk.CTkLabel(self.env_box, text="Survival Gust: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_gust.grid(row=2, column=0, padx=10, pady=2, sticky="w")
        
        self.lbl_env_downtime = ctk.CTkLabel(self.env_box, text="Downtime: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_downtime.grid(row=2, column=1, padx=10, pady=2, sticky="w")
        
        # Row 3: Roughness & Weibull Shape
        self.lbl_env_roughness = ctk.CTkLabel(self.env_box, text="Roughness (z0): -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_roughness.grid(row=3, column=0, padx=10, pady=(2, 6), sticky="w")
        
        self.lbl_env_weibull = ctk.CTkLabel(self.env_box, text="Weibull k: -", font=Theme.fonts.MUTED, text_color=Theme.TEXT_MAIN.value, anchor="w", padx=0)
        self.lbl_env_weibull.grid(row=3, column=1, padx=10, pady=(2, 6), sticky="w")

        # Mission Constraints label
        lbl = ctk.CTkLabel(
            self.mission_scroll, 
            text="Mission Constraints:", 
            font=Theme.fonts.BODY_BOLD, 
            text_color=Theme.TEXT_MAIN.value
        )
        lbl.pack(anchor="w", padx=5, pady=(5, 2))
        self._tracked_widgets.append(lbl)
        
        # Regular frame (since parent is already scrollable, avoiding nested scrollbars)
        self.constraints_scroll = ctk.CTkFrame(
            self.mission_scroll, 
            fg_color=Theme.BG_SURFACE.value
        )
        self.constraints_scroll.pack(fill="x", expand=True, padx=5, pady=5)

        p_tab = self.tabs.add("Physical Specs")
        d_tab = self.tabs.add("Drivetrain")

        # ==========================================
        # TAB 1: PHYSICAL SPECS
        # ==========================================
        # Designer Name
        lbl = ctk.CTkLabel(p_tab, text="Designer Name", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value)
        lbl.pack(anchor="w", padx=5, pady=(5, 0))
        self._tracked_widgets.append(lbl)
        self.ent_name = ctk.CTkEntry(
            p_tab, 
            textvariable=self.name_var, 
            height=26, 
            fg_color=Theme.BG_INPUT.value, 
            border_color=Theme.BORDER.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.ent_name.pack(fill="x", padx=5, pady=(0, 5))

        # General Title
        lbl = ctk.CTkLabel(p_tab, text="Physical Details", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value)
        lbl.pack(anchor="w", padx=5, pady=(15, 2))
        self._tracked_widgets.append(lbl)

        # SSN Field
        ctk.CTkLabel(p_tab, text="SSN (YYYYMMDDXXXX)", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value).pack(anchor="w", padx=5, pady=(2, 0))
        self.ent_ssn = ctk.CTkEntry(
            p_tab, 
            textvariable=self.ssn_var, 
            height=26, 
            fg_color=Theme.BG_INPUT.value, 
            border_color=Theme.BORDER.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.ent_ssn.pack(fill="x", padx=5, pady=(0, 10))

        # Sliders
        # Rotor Diameter
        self.slider_rotor_diameter = LabeledSlider(p_tab, "Rotor Diameter: {value:.1f} m", self.rotor_diameter_var, 30, 150, 120, self.on_slider_move)
        self.slider_rotor_diameter.pack(fill="x", padx=5, pady=(0, 10))

        # Solidity
        self.slider_solidity = LabeledSlider(p_tab, "Rotor Solidity: {value:.1f} %", self.solidity_var, 1, 10, 90, self.on_slider_move)
        self.slider_solidity.pack(fill="x", padx=5, pady=(0, 10))

        # Tower dimensions container
        self.tower_box = ctk.CTkFrame(
            p_tab, 
            fg_color=Theme.BOX_BG.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self.tower_box.pack(fill="x", padx=5, pady=(5, 10))

        ctk.CTkLabel(
            self.tower_box, 
            text="TOWER GEOMETRY", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.ACCENT.value
        ).pack(anchor="w", padx=10, pady=(8, 2))

        # 1. Hub Height
        self.slider_height = LabeledSlider(self.tower_box, "Hub Height: {value:.1f} m", self.height_var, 40, 160, 120, self.on_slider_move)
        self.slider_height.pack(fill="x", padx=10, pady=(0, 8))

        # 2. Top Diameter
        self.slider_top_diam = LabeledSlider(self.tower_box, "Top Diameter: {value:.2f} m", self.top_diameter_var, 1, 8, 65, self.on_slider_move)
        self.slider_top_diam.pack(fill="x", padx=10, pady=(0, 8))

        # 3. Bottom Diameter
        self.slider_bottom_diam = LabeledSlider(self.tower_box, "Base Diameter: {value:.2f} m", self.bottom_diameter_var, 1, 12, 100, self.on_slider_move)
        self.slider_bottom_diam.pack(fill="x", padx=10, pady=(0, 8))

        # 4. Wall Thickness
        self.slider_wall_thickness = LabeledSlider(self.tower_box, "Wall Thickness: {value:.1f} mm", self.wall_thickness_var, 10, 250, 240, self.on_slider_move)
        self.slider_wall_thickness.pack(fill="x", padx=10, pady=(0, 10))


        # Blades Count Segmented Button
        lbl = ctk.CTkLabel(p_tab, text="Number of Blades", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value)
        lbl.pack(anchor="w", padx=5, pady=(5, 0))
        self._tracked_widgets.append(lbl)
        self.seg_blades = ctk.CTkSegmentedButton(
            p_tab, 
            values=["2 Blades", "3 Blades", "4 Blades"], 
            variable=self.blades_var,
            command=self.on_segmented_click,
            selected_color=Theme.ACCENT.value,
            selected_hover_color=Theme.ACCENT_HOVER.value,
            unselected_color=Theme.BG_INPUT.value,
            unselected_hover_color=Theme.BG_MAIN.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.seg_blades.pack(fill="x", padx=5, pady=5)

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
        self.turbine.solidity = self.solidity_var.get()

        # Notify parent app
        self.on_change()

    def on_segmented_click(self, choice):
        """
        Handle segmented button click for blade count selection.
        
        Parameters
        ----------
        choice : str
            The selected segmented button value (e.g. "3 Blades").
        """
        # Extract number of blades (e.g. "3 Blades" -> 3)
        num_blades = int(choice.split()[0])
        self.turbine.blades = num_blades
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
        ssn = self.ssn_var.get()
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
        self.solidity_var.set(self.turbine.solidity)
        self.blades_var.set(f"{self.turbine.blades} Blades")
        self.gearbox_var.set(self.turbine.gearbox.value)
        self.generator_var.set(self.turbine.generator.value)

        # Update physical spec labels via components
        self.slider_rotor_diameter.update_label()
        self.slider_height.update_label()
        self.slider_top_diam.update_label()
        self.slider_bottom_diam.update_label()
        self.slider_wall_thickness.update_label()
        self.slider_solidity.update_label()

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
        self.lbl_env_site.configure(text=f"Site Type: {site_type}")
        
        self.lbl_env_price.configure(
            text=f"Elec. Price: {env.electricity_price} €/MWh" if env.electricity_price is not None else "Elec. Price: - €/MWh"
        )
        self.lbl_env_wind.configure(
            text=f"Wind (10m): {env.avg_wind_10:.1f} m/s (Hub: {wind_hub:.1f} m/s)" if env.avg_wind_10 else "Wind: - m/s"
        )
        self.lbl_env_lifetime.configure(
            text=f"Lifetime: {self.turbine.lifetime} years"
        )
        self.lbl_env_gust.configure(
            text=f"Survival Gust: {env.survival_gust:.1f} m/s" if env.survival_gust else "Survival Gust: - m/s"
        )
        self.lbl_env_downtime.configure(
            text=f"Downtime: {self.turbine.downtime:.1f}%" if self.turbine.downtime is not None else "Downtime: - %"
        )
        self.lbl_env_roughness.configure(
            text=f"Roughness (z0): {env.roughness:.2f} mm" if env.roughness else "Roughness (z0): - mm"
        )
        self.lbl_env_weibull.configure(
            text=f"Weibull k: {env.k_factor:.2f}" if env.k_factor else "Weibull k: -"
        )

    def update_mission_view(self, mission, report=None):
        """
        Updates the mission selection UI, active description, and constraints list.
        """
        # Ensure dropdown value matches the mission
        display_names = {
            "Sandbox": "Free Play Sandbox",
            "Arctic Gale": "The Arctic Gale",
            "The Gentle Breeze": "The Gentle Breeze",
            "The Community Cooperative": "The Community Cooperative"
        }
        name_to_set = display_names.get(mission.name, mission.name)
        self.mission_menu.set(name_to_set)

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
                row.pack(fill="x", pady=4)
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
                row.pack(fill="x", pady=4)
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
        self.slider_rotor_diameter.configure_slider(state=state)
        self.slider_height.configure_slider(state=state)
        self.slider_top_diam.configure_slider(state=state)
        self.slider_bottom_diam.configure_slider(state=state)
        self.slider_wall_thickness.configure_slider(state=state)
        self.slider_solidity.configure_slider(state=state)
        self.seg_blades.configure(state=state)
        self.combo_gearbox.configure(state=state)
        self.combo_generator.configure(state=state)
        self.ent_name.configure(state=state)
        self.ent_ssn.configure(state=state)