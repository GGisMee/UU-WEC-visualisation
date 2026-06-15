# gui/console.py
import customtkinter as ctk
import tkinter as tk
import math
from typing import Callable
from src.wec_visualisation.models.turbine import WindTurbine
from src.wec_visualisation.models.environment import SiteEnvironment, SSNGenerator
from src.wec_visualisation.gui.theme import Theme
from src.wec_visualisation.models.turbine import Generator, Gearbox
from src.wec_visualisation.gui.components import LabeledSlider, MetricRow

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
    """

    def __init__(
        self, 
        parent, 
        turbine: WindTurbine, 
        environment: SiteEnvironment, 
        on_change_callback: Callable,
        on_ssn_callback: Callable
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
        """
        super().__init__(
            parent, 
            width=320, 
            fg_color=Theme.BG_SURFACE.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self.turbine = turbine
        self.environment = environment
        self.on_change = on_change_callback
        self.on_ssn = on_ssn_callback
        
        # Prevent auto-shrinking so panel stays exactly width=320
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
            fg_color="transparent",
            segmented_button_fg_color=Theme.BOX_BG.value,
            segmented_button_selected_color=Theme.TAB_SELECTED.value,
            segmented_button_selected_hover_color=Theme.TAB_SELECTED_HOVER.value,
            segmented_button_unselected_color=Theme.BOX_BG.value,
            segmented_button_unselected_hover_color=Theme.BUTTON_HOVER.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        p_tab = self.tabs.add("Physical Specs")
        d_tab = self.tabs.add("Drivetrain")
        e_tab = self.tabs.add("Env & Economics")

        # ==========================================
        # TAB 1: PHYSICAL SPECS
        # ==========================================
        # Designer Name
        ctk.CTkLabel(p_tab, text="Designer Name", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value).pack(anchor="w", padx=5, pady=(5, 0))
        self.ent_name = ctk.CTkEntry(
            p_tab, 
            textvariable=self.name_var, 
            height=26, 
            fg_color=Theme.BG_INPUT.value, 
            border_color=Theme.BORDER.value,
            text_color=Theme.TEXT_MAIN.value
        )
        self.ent_name.pack(fill="x", padx=5, pady=(0, 5))

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
        ctk.CTkLabel(p_tab, text="Number of Blades", font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value).pack(anchor="w", padx=5, pady=(5, 0))
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
        ctk.CTkLabel(d_tab, text="Gearbox Technology", font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value).pack(anchor="w", padx=5, pady=(10, 2))
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

        ctk.CTkLabel(d_tab, text="Generator Type", font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value).pack(anchor="w", padx=5, pady=(10, 2))
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
        drivetrain_info = ctk.CTkFrame(
            d_tab, 
            fg_color=Theme.BOX_BG.value, 
            corner_radius=6, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        drivetrain_info.pack(fill="both", expand=True, padx=5, pady=10)
        
        self.lbl_drivetrain_desc = ctk.CTkLabel(
            drivetrain_info, 
            text="",
            font=Theme.fonts.MUTED,
            text_color=Theme.TEXT_MUTED.value,
            wraplength=260,
            justify="left"
        )
        self.lbl_drivetrain_desc.pack(padx=10, pady=10, fill="both", expand=True)

        # ==========================================
        # TAB 3: ENV & ECONOMICS (READ-ONLY)
        # ==========================================
        self.env_scroll = ctk.CTkScrollableFrame(
            e_tab, 
            fg_color=Theme.BG_SURFACE.value
        )
        self.env_scroll.pack(fill="both", expand=True, padx=2, pady=2)

        self.env_rows = {}
        env_labels = [
            ("avg_wind", "Avg Wind (10m):", "- m/s"),
            ("roughness", "Roughness Length (z0):", "- mm"),
            ("survival", "Survival Wind Gust:", "- m/s"),
            ("weibull_k", "Weibull Shape (k):", "-"),
            ("downtime", "Annual Downtime:", "- %"),
            ("lifetime", "Project Lifetime:", "- yrs"),
            ("price", "Electricity Price:", "- €/MWh"),
            ("green_cert", "Green Certificate:", "- €/MWh"),
            ("inflation", "Inflation Rate:", "- %"),
            ("interest", "Interest Rate:", "- %"),
        ]

        for key, text, init in env_labels:
            row = MetricRow(self.env_scroll, text, init)
            row.pack(fill="x", pady=2, padx=2)
            self.env_rows[key] = row

        # Mission Objectives box
        self.objectives_box = ctk.CTkFrame(
            self.env_scroll, 
            fg_color=Theme.BOX_BG.value, 
            corner_radius=6,
            border_width=1,
            border_color=Theme.BORDER.value
        )
        self.objectives_box.pack(fill="x", pady=10, padx=2)
        
        ctk.CTkLabel(
            self.objectives_box, 
            text="MISSION TARGETS", 
            font=Theme.fonts.HEADER, 
            text_color=Theme.ACCENT.value
        ).pack(anchor="w", padx=8, pady=(6, 2))
        
        self.lbl_objectives = ctk.CTkLabel(
            self.objectives_box, 
            text="Sandbox: Explore freely.", 
            font=Theme.fonts.MUTED, 
            text_color=Theme.TEXT_MUTED.value,
            wraplength=240,
            justify="left"
        )
        self.lbl_objectives.pack(anchor="w", padx=8, pady=(0, 8))

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

    # ==========================================
    # PUBLIC/VIEW INTERFACES
    # ==========================================
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
        gear = self.gearbox_var.get()
        gen = self.generator_var.get()
        if gear == "None (Direct Drive)":
            desc = f"Direct Drive + {gen}: No gearbox eliminates high-wear parts and reduces maintenance. However, the multi-pole generator increases weight and structural CAPEX."
        else:
            desc = f"{gear} + {gen}: Geared drivetrain configuration. Standard, cost-effective design with a lighter nacelle, but requires scheduled gearbox inspections."
        self.lbl_drivetrain_desc.configure(text=desc)

    def update_env_view(self):
        """
        Update the read-only display rows for environmental and economics values.
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

        # Update environment labels
        self.env_rows["avg_wind"].set_value(f"{env.avg_wind_10:.1f} m/s (Hub: {wind_hub:.1f} m/s)" if env.avg_wind_10 else "- m/s")
        self.env_rows["roughness"].set_value(f"{env.roughness:.2f} mm" if env.roughness else "- mm")
        self.env_rows["survival"].set_value(f"{env.survival_gust:.1f} m/s" if env.survival_gust else "- m/s")
        self.env_rows["weibull_k"].set_value(f"{env.k_factor:.2f}" if env.k_factor else "-")
        self.env_rows["downtime"].set_value(f"{self.turbine.downtime:.1f} %" if self.turbine.downtime is not None else "- %")
        self.env_rows["lifetime"].set_value(f"{self.turbine.lifetime} yrs" if self.turbine.lifetime else "- yrs")
        self.env_rows["price"].set_value(f"{env.electricity_price} €/MWh" if env.electricity_price is not None else "- €/MWh")
        self.env_rows["green_cert"].set_value(f"{env.green_certificate} €/MWh" if env.green_certificate is not None else "- €/MWh")
        self.env_rows["inflation"].set_value(f"{env.inflation:.1f} %" if env.inflation is not None else "- %")
        self.env_rows["interest"].set_value(f"{env.interest:.1f} %" if env.interest is not None else "- %")

    def set_objectives_text(self, text: str):
        """
        Set the mission objectives description label text.
        
        Parameters
        ----------
        text : str
            The text description to show.
        """
        self.lbl_objectives.configure(text=text)

    def set_inputs_enabled(self, enabled: bool):
        """
        Enable or disable interactive widgets on the console panel.
        
        Parameters
        ----------
        enabled : bool
            True to enable inputs, False to disable.
        """
        state = "normal" if enabled else "disabled"
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