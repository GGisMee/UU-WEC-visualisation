# gui/analytics.py
import customtkinter as ctk
import tkinter as tk
import math
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from wec_visualisation.models.simulation import SimulationResult
from wec_visualisation.gui.theme import Theme
from wec_visualisation.gui.components import TextInfoBox

class AnalyticsPanel(ctk.CTkFrame):
    def __init__(self, parent, on_simulate_click):
        super().__init__(
            parent, 
            width=420, 
            fg_color=Theme.BG_SURFACE.value, 
            border_width=1, 
            border_color=Theme.BORDER.value
        )
        self.on_simulate = on_simulate_click
        self.last_result = None
        self._tracked_widgets = []

        # Prevent auto-shrinking
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Title Label
        self.lbl_title = ctk.CTkLabel(
            self, 
            text="ANALYTICS & RESULTS", 
            font=Theme.fonts.SUBTITLE, 
            text_color=Theme.TEXT_ACCENT.value
        )
        self.lbl_title.pack(anchor="w", padx=15, pady=(15, 5))

        # Main Tabview
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
        
        ch_tab = self.tabs.add("Performance Charts")
        au_tab = self.tabs.add("Engineering Audit")
        fn_tab = self.tabs.add("Financial Ledger")

        # ==========================================
        # TAB 1: PERFORMANCE CHARTS
        # ==========================================
        self.charts_frame = ctk.CTkFrame(ch_tab, fg_color=Theme.BG_SURFACE.value)
        self.charts_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.charts_fig = Figure(figsize=(4, 6), dpi=100)
        self.charts_canvas = FigureCanvasTkAgg(self.charts_fig, master=self.charts_frame)
        self.charts_canvas.get_tk_widget().pack(fill="both", expand=True)

        # ==========================================
        # TAB 2: ENGINEERING AUDIT
        # ==========================================
        self.audit_scroll = ctk.CTkScrollableFrame(au_tab, fg_color=Theme.BG_SURFACE.value)
        self.audit_scroll.pack(fill="both", expand=True)

        self.audit_rows = {}
        audit_defs = [
            ("hub_wind", "Hub Average Wind Speed", "- m/s"),
            ("swept_area", "Rotor Swept Area", "- m²"),
            ("rated_power", "Turbine Rated Power", "- kW"),
            ("cap_factor", "Drivetrain Capacity Factor", "- %"),
            ("thrust_load", "Operational Aerodynamic Load", "- kN"),
            ("storm_load", "Storm Load (Survival)", "- kN"),
            ("breaking", "Breaking Utilization", "-"),
            ("slenderness", "Tower Slenderness Ratio (H/2R)", "-"),
            ("buckeling", "Buckling Utilization", "-"),
        ]
        
        for key, label, init_val in audit_defs:
            row = ctk.CTkFrame(self.audit_scroll, fg_color=Theme.BG_SURFACE.value)
            row.pack(fill="x", pady=4, padx=5)
            
            lbl = ctk.CTkLabel(row, text=label, font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value)
            lbl.pack(side="left")
            self._tracked_widgets.append(lbl)
            val_lbl = ctk.CTkLabel(row, text=init_val, font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value)
            val_lbl.pack(side="right")
            self.audit_rows[key] = val_lbl

        # Guidelines Box
        desc_guidelines = (
            "• Buckling and Breaking utilizations must not exceed 1.0.\n"
            "• High solidity blades increase storm torque significantly, requiring thicker tower walls.\n"
            "• Increasing hub height yields higher wind speeds (Wind Shear) but raises gravity bending loads."
        )
        info_guidelines = TextInfoBox(self.audit_scroll, "DESIGN GUIDELINES", height=85)
        info_guidelines.pack(fill="x", pady=10, padx=5)
        info_guidelines.set_text(desc_guidelines)

        # ==========================================
        # TAB 3: FINANCIAL LEDGER
        # ==========================================
        self.ledger_scroll = ctk.CTkScrollableFrame(fn_tab, fg_color=Theme.BG_SURFACE.value)
        self.ledger_scroll.pack(fill="both", expand=True)

        # Cost breakdown bar chart area
        lbl = ctk.CTkLabel(self.ledger_scroll, text="CAPEX COST ALLOCATION BREAKDOWN", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value)
        lbl.pack(anchor="w", padx=5, pady=(5, 2))
        self._tracked_widgets.append(lbl)
        self.capex_frame = ctk.CTkFrame(self.ledger_scroll, fg_color=Theme.BG_SURFACE.value, height=30)
        self.capex_frame.pack(fill="x", padx=5, pady=(0, 10))
        self.capex_frame.pack_propagate(False)
        self.capex_fig = Figure(figsize=(5, 0.3), dpi=100)
        self.capex_canvas = FigureCanvasTkAgg(self.capex_fig, master=self.capex_frame)
        self.capex_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.ledger_rows = {}
        ledger_defs = [
            ("capex_dev", "Development Expenditure (DEVEX)", "- k€"),
            ("capex_turb", "Turbine Rotor Assembly Cost", "- k€"),
            ("capex_driv", "Drivetrain & Nacelle Cost", "- k€"),
            ("capex_tow", "Steel Tower Structure Cost", "- k€"),
            ("capex_found", "Concrete Foundation & Site Cost", "- k€"),
            ("capex_install", "Installation Logistics Cost", "- k€"),
            ("capex_tot", "TOTAL CAPITAL COST (CAPEX)", "- k€", True),
            ("opex", "Annual Operating Costs (OPEX)", "- k€/yr"),
            ("revenue", "Net Annual Yield Revenue", "- k€/yr"),
            ("irr", "Internal Rate of Return (IRR)", "- %"),
            ("margin", "Lifetime Profit Margin", "- %", True),
        ]

        for item in ledger_defs:
            is_bold = len(item) == 4
            key, label, init_val = item[0], item[1], item[2]
            
            row = ctk.CTkFrame(self.ledger_scroll, fg_color=Theme.BG_SURFACE.value)
            row.pack(fill="x", pady=4, padx=5)
            
            lbl_weight = Theme.fonts.BODY_BOLD if is_bold else Theme.fonts.BODY
            lbl_color = Theme.TEXT_MAIN.value if is_bold else Theme.TEXT_MUTED.value
            
            lbl = ctk.CTkLabel(row, text=label, font=lbl_weight, text_color=lbl_color)
            lbl.pack(side="left")
            self._tracked_widgets.append(lbl)
            val_lbl = ctk.CTkLabel(row, text=init_val, font=Theme.fonts.BODY_BOLD, text_color=Theme.INFO.value if is_bold else Theme.TEXT_MAIN.value)
            val_lbl.pack(side="right")
            self.ledger_rows[key] = val_lbl

        # ==========================================
        # WARNING BANNER & LOADING OVERLAY
        # ==========================================
        # Warning Banner (shown when inputs change, prompting rerun)
        self.warning_banner = ctk.CTkFrame(self, fg_color=Theme.ALERT_BG.value, height=32, corner_radius=0)
        self.lbl_warning = ctk.CTkLabel(
            self.warning_banner, 
            text="⚠️ Inputs changed. Click 'Run Simulation' to recalculate results.",
            font=Theme.fonts.BODY_BOLD,
            text_color=Theme.ALERT.value
        )
        self.lbl_warning.pack(pady=4)

        # Loading Overlay (covers entire panel during simulation run)
        self.loading_overlay = ctk.CTkFrame(self, fg_color=Theme.BG_SURFACE.value, corner_radius=0)
        self.loading_container = ctk.CTkFrame(self.loading_overlay, fg_color=Theme.BG_SURFACE.value)
        self.loading_container.place(relx=0.5, rely=0.45, anchor="center")

        lbl = ctk.CTkLabel(
            self.loading_container, 
            text="SIMULATION RUNNING", 
            font=Theme.fonts.SUBTITLE, 
            text_color=Theme.ACCENT.value
        )
        lbl.pack(pady=5)
        self._tracked_widgets.append(lbl)
        
        self.lbl_loading_status = ctk.CTkLabel(
            self.loading_container, 
            text="Initializing wind aerodynamic grid...", 
            font=Theme.fonts.BODY, 
            text_color=Theme.TEXT_MAIN.value
        )
        self.lbl_loading_status.pack(pady=(0, 15))

        self.loading_progress = ctk.CTkProgressBar(
            self.loading_container, 
            width=280, 
            progress_color=Theme.ACCENT.value, 
            fg_color=Theme.BG_MAIN.value
        )
        self.loading_progress.pack()

        # Initial clean view
        self.clear_charts()
        self.show_warning_banner(False)

    # ==========================================
    # CONTROLLER INTERFACES
    # ==========================================

    def show_warning_banner(self, show: bool):
        if show:
            self.warning_banner.place(relx=0, rely=0.92, relwidth=1, relheight=0.08)
        else:
            self.warning_banner.place_forget()

    def show_loading(self, show: bool, message: str = ""):
        if show:
            self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.loading_progress.start()
            if message:
                self.lbl_loading_status.configure(text=message)
        else:
            self.loading_progress.stop()
            self.loading_overlay.place_forget()

    def set_loading_status(self, text: str):
        self.lbl_loading_status.configure(text=text)

    def display_results(self, result: SimulationResult, swept_area:float):
        """Displays simulated variables and plots curves."""
        self.last_result = result
        self.show_warning_banner(False)
        self.show_loading(False)

        # 1. Update Audit Tab
        self.audit_rows["hub_wind"].configure(text=f"{result.wind_nacelle:.1f} m/s")
        
        self.audit_rows["swept_area"].configure(text=f"{swept_area:,.1f} m²")
        self.audit_rows["rated_power"].configure(text=f"{result.rated_power:,.1f} kW")
        self.audit_rows["cap_factor"].configure(text=f"{result.capacity_factor * 100:.1f} %")
        self.audit_rows["thrust_load"].configure(text=f"{result.aerodynamical_load:,.1f} kN")
        self.audit_rows["storm_load"].configure(text=f"{result.storm_load:,.1f} kN")
        
        # Highlight utilization if exceeds 1.0 limit
        br_color = Theme.DANGER.value if result.breaking_utilization > 1.0 else Theme.TEXT_MAIN.value
        self.audit_rows["breaking"].configure(text=f"{result.breaking_utilization:.2f}", text_color=br_color)
        self.audit_rows["slenderness"].configure(text=f"{result.slenderness_ratio:.2f}")

        bu_color = Theme.DANGER.value if result.buckeling_utilization > 1.0 else Theme.TEXT_MAIN.value
        self.audit_rows["buckeling"].configure(text=f"{result.buckeling_utilization:.2f}", text_color=bu_color)

        # 2. Update Ledger Tab
        caps = result.capex_components
        if isinstance(caps, dict):
            self.ledger_rows["capex_dev"].configure(text=f"{caps.get('devex', 0.0):,.1f} k€")
            self.ledger_rows["capex_turb"].configure(text=f"{caps.get('rotor', 0.0):,.1f} k€")
            self.ledger_rows["capex_driv"].configure(text=f"{caps.get('drivetrain', 0.0):,.1f} k€")
            self.ledger_rows["capex_tow"].configure(text=f"{caps.get('tower', 0.0):,.1f} k€")
            self.ledger_rows["capex_found"].configure(text=f"{caps.get('foundation', 0.0):,.1f} k€")
            self.ledger_rows["capex_install"].configure(text=f"{caps.get('installation', 0.0):,.1f} k€")
        else:
            if "capex_dev" in self.ledger_rows:
                self.ledger_rows["capex_dev"].configure(text="0.0 k€")
            if "capex_install" in self.ledger_rows:
                self.ledger_rows["capex_install"].configure(text="0.0 k€")
            self.ledger_rows["capex_turb"].configure(text=f"{caps[0]:,.1f} k€")
            self.ledger_rows["capex_driv"].configure(text=f"{caps[1]:,.1f} k€")
            self.ledger_rows["capex_tow"].configure(text=f"{caps[2]:,.1f} k€")
            self.ledger_rows["capex_found"].configure(text=f"{caps[3]:,.1f} k€")
        self.ledger_rows["capex_tot"].configure(text=f"{result.total_capex:,.1f} k€")
        self.ledger_rows["opex"].configure(text=f"{result.annual_opex:,.1f} k€/yr")
        self.ledger_rows["revenue"].configure(text=f"{result.annual_revenue:,.1f} k€/yr")
        
        # Display IRR
        irr_val = result.IRR
        irr_text = f"{irr_val * 100:.1f} %" if hasattr(irr_val, '__float__') or isinstance(irr_val, float) else "- %"
        self.ledger_rows["irr"].configure(text=irr_text)

        # Profit Margin
        margin_val = result.margin * 100.0
        margin_color = Theme.SUCCESS.value if margin_val >= 0 else Theme.DANGER.value
        self.ledger_rows["margin"].configure(text=f"{margin_val:.1f} %", text_color=margin_color)

        # 3. Redraw Charts & Capex Horizontal Bar
        self.draw_performance_curves()
        self.redraw_capex_bar()

    def clear_charts(self):
        """Matplotlib chart drawing loops"""
        self.charts_fig.clear()
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1
        bg_color = Theme.BLUEPRINT_BG.value[idx]
        muted_color = Theme.TEXT_MUTED.value[idx]

        self.charts_fig.patch.set_facecolor(bg_color)
        ax = self.charts_fig.add_subplot(111)
        ax.set_facecolor(bg_color)
        ax.text(0.5, 0.5, "[ Simulation Out of Date ]\nClick 'Run Simulation' to plot curves.",
                ha='center', va='center', color=muted_color, fontweight='bold', fontsize=12)
        ax.axis('off')
        
        self.charts_canvas.draw()

        self.capex_fig.clear()
        self.capex_fig.patch.set_facecolor(Theme.BG_INPUT.value[idx])
        self.capex_canvas.draw()

        # Update styling
        self.configure(fg_color=Theme.BG_SURFACE.value, border_color=Theme.BORDER.value)

    def draw_performance_curves(self):
        res = self.last_result
        if not res:
            self.clear_charts()
            return

        self.charts_fig.clear()
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        bg_color = Theme.BLUEPRINT_BG.value[idx]
        chart_bg = Theme.CHART_BG.value[idx]
        text_color = Theme.TEXT_MAIN.value[idx]
        muted_color = Theme.TEXT_MUTED.value[idx]
        info_color = Theme.INFO.value[idx]
        accent_color = Theme.ACCENT.value[idx]
        border_color = Theme.BORDER.value[idx]
        success_color = Theme.SUCCESS.value[idx]
        danger_color = Theme.DANGER.value[idx]

        self.charts_fig.patch.set_facecolor(bg_color)

        # Subplots stacked vertically
        ax1 = self.charts_fig.add_subplot(211)
        ax2 = self.charts_fig.add_subplot(212)

        for ax in (ax1, ax2):
            ax.set_facecolor(chart_bg)
            ax.tick_params(colors=muted_color)
            for spine in ax.spines.values():
                spine.set_color(border_color)
            ax.grid(True, color=border_color, linestyle='--', alpha=0.5)

        # --- Plot 1: Weibull ---
        max_v = 25.0
        v_arr = np.linspace(0.1, max_v, 200)
        prob_arr = res.get_weibull_prob(v_arr)

        ax1.plot(v_arr, prob_arr, color=info_color, linewidth=2)
        ax1.set_title("Weibull Wind Speed Curve", color=info_color, fontweight='bold')
        ax1.set_xlabel("Wind Speed (m/s)", color=muted_color)
        ax1.set_ylabel("Probability Density", color=muted_color)
        
        ax1.axvline(res.cut_in_speed, color=success_color, linestyle='--', alpha=0.8, label="Cut-in")
        ax1.axvline(res.cut_out_speed, color=danger_color, linestyle='--', alpha=0.8, label="Cut-out")
        ax1.legend(loc="upper right", facecolor=chart_bg, edgecolor=border_color, labelcolor=text_color)
        ax1.set_xlim(0, max_v)
        ax1.set_ylim(bottom=0)

        # --- Plot 2: Power Curve ---
        p_arr = [res.get_power_at_wind_speed(v) for v in v_arr]
        ax2.plot(v_arr, p_arr, color=accent_color, linewidth=2)
        ax2.set_title("Turbine Power Curve (kW)", color=accent_color, fontweight='bold')
        ax2.set_xlabel("Wind Speed (m/s)", color=muted_color)
        ax2.set_ylabel("Power output (kW)", color=muted_color)
        ax2.set_xlim(0, max_v)
        ax2.set_ylim(bottom=0)
        
        self.charts_fig.tight_layout()
        self.charts_canvas.draw()

    def redraw_capex_bar(self):
        res = self.last_result
        if not res or not hasattr(res, "capex_components"):
            return

        caps = res.capex_components
        tot = sum(caps.values()) if isinstance(caps, dict) else sum(caps)
        if tot <= 0:
            return

        self.capex_fig.clear()
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        bg_input_color = Theme.BG_INPUT.value[idx]
        self.capex_fig.patch.set_facecolor(bg_input_color)

        ax = self.capex_fig.add_subplot(111)
        ax.set_facecolor(bg_input_color)
        ax.axis('off')

        if isinstance(caps, dict):
            keys = ["devex", "rotor", "drivetrain", "tower", "foundation", "installation"]
            colors = [Theme.BORDER.value[idx], Theme.INFO.value[idx], Theme.SUCCESS.value[idx],
                      Theme.ACCENT.value[idx], Theme.CONCRETE.value[idx], Theme.ALERT.value[idx]]
            values = [caps.get(k, 0.0) for k in keys]
        else:
            values = caps
            colors = [Theme.INFO.value[idx], Theme.SUCCESS.value[idx], Theme.ACCENT.value[idx], Theme.CONCRETE.value[idx]]

        left = 0.0
        for val, color in zip(values, colors):
            width = val / tot
            ax.barh(0, width, left=left, color=color, height=0.8)
            left += width

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        self.capex_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.capex_canvas.draw()