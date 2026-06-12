# gui/analytics.py
import customtkinter as ctk
import tkinter as tk
import math
from models.simulation import SimulationResult
from gui.theme import Theme

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
            fg_color="transparent",
            segmented_button_selected_color=Theme.TAB_SELECTED.value,
            segmented_button_selected_hover_color=Theme.TAB_SELECTED_HOVER.value,
            segmented_button_unselected_color=Theme.BUTTON_BG.value,
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
        mode_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        self.charts_canvas = tk.Canvas(ch_tab, bg=Theme.BLUEPRINT_BG.value[mode_idx], highlightthickness=0)
        self.charts_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.charts_canvas.bind("<Configure>", lambda e: self.draw_performance_curves())

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
            ("wall_thickness", "Mean Tower Wall Thickness", "- mm"),
            ("slenderness", "Tower Slenderness Ratio (H/2R)", "-"),
            ("safety_margin", "Thickness Safety Margin", "-"),
        ]
        
        for key, label, init_val in audit_defs:
            row = ctk.CTkFrame(self.audit_scroll, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            ctk.CTkLabel(row, text=label, font=Theme.fonts.BODY, text_color=Theme.TEXT_MUTED.value).pack(side="left")
            val_lbl = ctk.CTkLabel(row, text=init_val, font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value)
            val_lbl.pack(side="right")
            self.audit_rows[key] = val_lbl

        # Guidelines Box
        guidelines_box = ctk.CTkFrame(
            self.audit_scroll, 
            fg_color=Theme.BOX_BG.value, 
            corner_radius=6,
            border_width=1,
            border_color=Theme.BORDER.value
        )
        guidelines_box.pack(fill="x", pady=10, padx=5)
        ctk.CTkLabel(guidelines_box, text="DESIGN GUIDELINES", font=Theme.fonts.HEADER, text_color=Theme.ACCENT.value).pack(anchor="w", padx=10, pady=(8, 2))
        
        desc_guidelines = (
            "• Mean Wall Thickness must not exceed 150.0 mm.\n"
            "• High solidity blades increase storm torque significantly, requiring thicker tower walls.\n"
            "• Increasing hub height yields higher wind speeds (Wind Shear) but raises gravity bending loads."
        )
        ctk.CTkLabel(guidelines_box, text=desc_guidelines, font=Theme.fonts.MUTED, text_color=Theme.TEXT_MUTED.value, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        # ==========================================
        # TAB 3: FINANCIAL LEDGER
        # ==========================================
        self.ledger_scroll = ctk.CTkScrollableFrame(fn_tab, fg_color=Theme.BG_SURFACE.value)
        self.ledger_scroll.pack(fill="both", expand=True)

        # Cost breakdown bar chart area
        ctk.CTkLabel(self.ledger_scroll, text="CAPEX COST ALLOCATION BREAKDOWN", font=Theme.fonts.HEADER, text_color=Theme.TEXT_MUTED.value).pack(anchor="w", padx=5, pady=(5, 2))
        mode_idx = 0 if ctk.get_appearance_mode() == "Light" else 1
        self.capex_canvas = tk.Canvas(self.ledger_scroll, bg=Theme.BG_INPUT.value[mode_idx], highlightthickness=0, height=25)
        self.capex_canvas.pack(fill="x", padx=5, pady=(0, 10))
        self.capex_canvas.bind("<Configure>", lambda e: self.redraw_capex_bar())

        self.ledger_rows = {}
        ledger_defs = [
            ("capex_turb", "Turbine Rotor Assembly Cost", "- k€"),
            ("capex_driv", "Drivetrain & Nacelle Cost", "- k€"),
            ("capex_tow", "Steel Tower Structure Cost", "- k€"),
            ("capex_found", "Concrete Foundation & Site Cost", "- k€"),
            ("capex_tot", "TOTAL CAPITAL COST (CAPEX)", "- k€", True),
            ("opex", "Annual Operating Costs (OPEX)", "- k€/yr"),
            ("revenue", "Net Annual Yield Revenue", "- k€/yr"),
            ("irr", "Internal Rate of Return (IRR)", "- %"),
            ("margin", "Lifetime Profit Margin", "- %", True),
        ]

        for item in ledger_defs:
            is_bold = len(item) == 4
            key, label, init_val = item[0], item[1], item[2]
            
            row = ctk.CTkFrame(self.ledger_scroll, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            lbl_weight = Theme.fonts.BODY_BOLD if is_bold else Theme.fonts.BODY
            lbl_color = Theme.TEXT_MAIN.value if is_bold else Theme.TEXT_MUTED.value
            
            ctk.CTkLabel(row, text=label, font=lbl_weight, text_color=lbl_color).pack(side="left")
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
        self.loading_container = ctk.CTkFrame(self.loading_overlay, fg_color="transparent")
        self.loading_container.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            self.loading_container, 
            text="SUPERCOMPUTER SIMULATION RUNNING", 
            font=Theme.fonts.SUBTITLE, 
            text_color=Theme.ACCENT.value
        ).pack(pady=5)
        
        self.lbl_loading_status = ctk.CTkLabel(
            self.loading_container, 
            text="Initializing wind tunnel aerodynamic grid...", 
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

    def display_results(self, result: SimulationResult):
        """Displays simulated variables and plots curves."""
        self.last_result = result
        self.show_warning_banner(False)
        self.show_loading(False)

        # 1. Update Audit Tab
        self.audit_rows["hub_wind"].configure(text=f"{result.wind_nacelle:.1f} m/s")
        
        # Calculate swept area from parent turbine
        swept = self.parent_turbine_swept_area()
        self.audit_rows["swept_area"].configure(text=f"{swept:,.1f} m²")
        self.audit_rows["rated_power"].configure(text=f"{result.rated_power:,.1f} kW")
        self.audit_rows["cap_factor"].configure(text=f"{result.capacity_factor * 100:.1f} %")
        self.audit_rows["thrust_load"].configure(text=f"{result.aerodynamical_load:,.1f} kN")
        self.audit_rows["storm_load"].configure(text=f"{result.storm_load:,.1f} kN")
        
        # Highlight wall thickness if exceeds 150mm limit
        thick_color = Theme.DANGER.value if result.mean_wall_thickness > 150.0 else Theme.TEXT_MAIN.value
        self.audit_rows["wall_thickness"].configure(text=f"{result.mean_wall_thickness:.1f} mm", text_color=thick_color)
        self.audit_rows["slenderness"].configure(text=f"{result.slenderness_ratio:.2f}")

        # Safety thickness margin (150mm / mean_wall_thickness)
        safety_margin = 150.0 / result.mean_wall_thickness if result.mean_wall_thickness > 0 else 0.0
        sm_color = Theme.SUCCESS.value if safety_margin >= 1.5 else (Theme.ALERT.value if safety_margin >= 1.0 else Theme.DANGER.value)
        self.audit_rows["safety_margin"].configure(text=f"{safety_margin:.2f}", text_color=sm_color)

        # 2. Update Ledger Tab
        caps = result.capex_components
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
        if hasattr(irr_val, 'root'):
            irr_text = f"{irr_val.root * 100:.1f} %"
        self.ledger_rows["irr"].configure(text=irr_text)

        # Profit Margin
        margin_val = result.margin * 100.0
        margin_color = Theme.SUCCESS.value if margin_val >= 0 else Theme.DANGER.value
        self.ledger_rows["margin"].configure(text=f"{margin_val:.1f} %", text_color=margin_color)

        # 3. Redraw Charts & Capex Horizontal Bar
        self.draw_performance_curves()
        self.redraw_capex_bar()

    def parent_turbine_swept_area(self) -> float:
        parent = self.master
        while parent and not hasattr(parent, "turbine"):
            parent = parent.master
        if parent and hasattr(parent, "turbine"):
            return parent.turbine.swept_area
        return 0.0

    # ==========================================
    # CHART DRAWING LOOPS (tk.Canvas)
    # ==========================================
    def clear_charts(self):
        w = self.charts_canvas.winfo_width()
        h = self.charts_canvas.winfo_height()
        if w < 10 or h < 10:
            return
        
        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1
        bg_color = Theme.BLUEPRINT_BG.value[idx]
        muted_color = Theme.TEXT_MUTED.value[idx]

        self.charts_canvas.delete("all")
        self.charts_canvas.configure(bg=bg_color)
        self.charts_canvas.create_text(
            w // 2, 
            h // 2, 
            text="[ Simulation Out of Date ]\nClick 'Run Simulation' to plot curves.", 
            fill=muted_color, 
            font=Theme.fonts.BODY_BOLD, 
            justify="center"
        )

        # Update styling
        self.configure(fg_color=Theme.BG_SURFACE.value, border_color=Theme.BORDER.value)

    def draw_performance_curves(self):
        w = self.charts_canvas.winfo_width()
        h = self.charts_canvas.winfo_height()
        if w < 10 or h < 10:
            return

        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1

        bg_color = Theme.BLUEPRINT_BG.value[idx]
        text_color = Theme.TEXT_MAIN.value[idx]
        muted_color = Theme.TEXT_MUTED.value[idx]
        info_color = Theme.INFO.value[idx]
        accent_color = Theme.ACCENT.value[idx]
        border_color = Theme.BORDER.value[idx]
        success_color = Theme.SUCCESS.value[idx]
        danger_color = Theme.DANGER.value[idx]

        self.charts_canvas.delete("all")
        self.charts_canvas.configure(bg=bg_color)

        res = self.last_result
        if not res:
            self.clear_charts()
            return

        pad = 25
        plot_w = (w - 3 * pad) // 2
        plot_h = h - 2 * pad

        # ------------------------------------------
        # PLOT 1: Weibull Wind Speed Distribution
        # ------------------------------------------
        x1_offset = pad
        y_offset = pad
        
        self.charts_canvas.create_rectangle(x1_offset, y_offset, x1_offset + plot_w, y_offset + plot_h, fill=Theme.CHART_BG.value[idx], outline=border_color)
        self.charts_canvas.create_text(x1_offset + plot_w // 2, y_offset - 10, text="Weibull Wind Speed Curve", fill=info_color, font=Theme.fonts.HEADER)

        k = res.weibull_k
        C = res.weibull_C
        
        points = []
        max_v = 25.0
        max_prob = 0.12  # Reference height scaling
        
        for i in range(plot_w):
            v = (i / plot_w) * max_v
            if v > 0:
                prob = (k / C) * ((v / C) ** (k - 1)) * math.exp(-((v / C) ** k))
            else:
                prob = 0.0
                
            px = x1_offset + i
            py = y_offset + plot_h - int((prob / max_prob) * plot_h)
            py = max(y_offset, min(y_offset + plot_h, py))
            points.append((px, py))

        if len(points) > 1:
            self.charts_canvas.create_line(points, fill=info_color, width=2)

        # Shaded operational limits
        cut_in_x = int((res.cut_in_speed / max_v) * plot_w)
        cut_out_x = int((res.cut_out_speed / max_v) * plot_w)
        self.charts_canvas.create_line(x1_offset + cut_in_x, y_offset, x1_offset + cut_in_x, y_offset + plot_h, fill=success_color, dash=(4, 4))
        self.charts_canvas.create_text(x1_offset + cut_in_x + 12, y_offset + 15, text="Cut-in", fill=success_color, font=(Theme.fonts.family, 7), angle=90)

        self.charts_canvas.create_line(x1_offset + cut_out_x, y_offset, x1_offset + cut_out_x, y_offset + plot_h, fill=danger_color, dash=(4, 4))
        self.charts_canvas.create_text(x1_offset + cut_out_x - 8, y_offset + 15, text="Cut-out", fill=danger_color, font=(Theme.fonts.family, 7), angle=90)

        # Plot labels/ticks
        self.charts_canvas.create_text(x1_offset + 15, y_offset + plot_h + 10, text="0", fill=muted_color, font=(Theme.fonts.family, 8))
        self.charts_canvas.create_text(x1_offset + plot_w - 15, y_offset + plot_h + 10, text="25m/s", fill=muted_color, font=(Theme.fonts.family, 8))

        # ------------------------------------------
        # PLOT 2: Turbine Power Curve
        # ------------------------------------------
        x2_offset = 2 * pad + plot_w
        
        self.charts_canvas.create_rectangle(x2_offset, y_offset, x2_offset + plot_w, y_offset + plot_h, fill=Theme.CHART_BG.value[idx], outline=border_color)
        self.charts_canvas.create_text(x2_offset + plot_w // 2, y_offset - 10, text="Turbine Power Curve (kW)", fill=accent_color, font=Theme.fonts.HEADER)

        p_points = []
        p_rated = res.rated_power
        v_rated = res.rated_wind_speed
        
        for i in range(plot_w):
            v = (i / plot_w) * max_v
            if v < res.cut_in_speed:
                p = 0.0
            elif v < v_rated:
                p = p_rated * ((v - res.cut_in_speed) / (v_rated - res.cut_in_speed)) ** 3
            elif v < res.cut_out_speed:
                p = p_rated
            else:
                p = 0.0
                
            px = x2_offset + i
            py = y_offset + plot_h - int((p / (p_rated * 1.1)) * plot_h) if p_rated > 0 else y_offset + plot_h
            py = max(y_offset, min(y_offset + plot_h, py))
            p_points.append((px, py))

        if len(p_points) > 1:
            self.charts_canvas.create_line(p_points, fill=accent_color, width=2)

        # Plot labels
        self.charts_canvas.create_text(x2_offset + 15, y_offset + plot_h + 10, text="0", fill=muted_color, font=(Theme.fonts.family, 8))
        self.charts_canvas.create_text(x2_offset + plot_w - 15, y_offset + plot_h + 10, text="25m/s", fill=muted_color, font=(Theme.fonts.family, 8))
        self.charts_canvas.create_text(x2_offset + 25, y_offset + 12, text=f"{int(p_rated)}kW", fill=text_color, font=(Theme.fonts.family, 8))

        # Update styling
        self.configure(fg_color=Theme.BG_SURFACE.value, border_color=Theme.BORDER.value)

    def redraw_capex_bar(self):
        w = self.capex_canvas.winfo_width()
        h = self.capex_canvas.winfo_height()
        if w < 10 or h < 10:
            return

        mode = ctk.get_appearance_mode()
        idx = 0 if mode == "Light" else 1
        bg_input_color = Theme.BG_INPUT.value[idx]

        self.capex_canvas.delete("all")
        self.capex_canvas.configure(bg=bg_input_color)

        res = self.last_result
        if not res or not hasattr(res, "capex_components"):
            return

        caps = res.capex_components
        tot = sum(caps)
        if tot <= 0:
            return

        # Ratios
        w_turb = int((caps[0] / tot) * w)
        w_driv = int((caps[1] / tot) * w)
        w_tow = int((caps[2] / tot) * w)

        # Colors from theme
        c_turb = Theme.INFO.value[idx]
        c_driv = Theme.SUCCESS.value[idx]
        c_tow = Theme.ACCENT.value[idx]
        c_found = Theme.CONCRETE.value[idx]

        self.capex_canvas.create_rectangle(0, 0, w_turb, h, fill=c_turb, outline="")
        self.capex_canvas.create_rectangle(w_turb, 0, w_turb + w_driv, h, fill=c_driv, outline="")
        self.capex_canvas.create_rectangle(w_turb + w_driv, 0, w_turb + w_driv + w_tow, h, fill=c_tow, outline="")
        self.capex_canvas.create_rectangle(w_turb + w_driv + w_tow, 0, w, h, fill=c_found, outline="")