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


# --- DESIGN SYSTEM COLORS (Technical Notebook Theme) ---
BG_COLOR = "#0C0F17"         # Dark matte background
PANEL_BG = "#131A26"         # Slate panels
CARD_BG = "#1A2333"          # Notebook card highlights
ACCENT_CYAN = "#06B6D4"      # Technical cyan
ACCENT_GREEN = "#10B981"     # Math green
ACCENT_ORANGE = "#F97316"    # Highlight orange
GRID_COLOR = "#223147"       # Graph grids
TEXT_MAIN = "#F3F4F6"        # Main text
TEXT_MUTED = "#9CA3AF"       # Muted text

class EngineeringNotebookApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

        # --- WINDOW SETUP ---
        self.title("Wind Physics & Engineering Notebook - Mockup C")
        self.geometry("1120x730")
        self.minsize(1050, 680)
        ctk.set_appearance_mode("dark")

        # --- STATE VARIABLES ---
        self.name_var = ctk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = ctk.StringVar(value="199801281234")
        self.roughness_var = ctk.StringVar(value="Grasslands (z0 = 0.05m)")
        
        self.diam_var = ctk.DoubleVar(value=95.0)
        self.height_var = ctk.DoubleVar(value=105.0)
        
        self.gearbox_var = ctk.StringVar(value="Medium Ratio")
        self.generator_var = ctk.StringVar(value="DFIG")

        self.create_layout()
        self.recalculate()

    def create_layout(self):
        # Configure columns: Left (Inputs), Right (Charts & Education)
        self.grid_columnconfigure(0, weight=3, minsize=320) # Controls
        self.grid_columnconfigure(1, weight=7, minsize=700) # Charts & Formulas
        self.grid_rowconfigure(0, weight=1)

        # ----------------------------------------------------
        # 1. LEFT COLUMN: PARAMETER NOTEBOOK
        # ----------------------------------------------------
        self.left_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.left_frame.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="nsew")
        
        # Header
        left_title = ctk.CTkLabel(self.left_frame, text="NOTEBOOK INPUTS", font=scaled_font("Montserrat", 16, "bold"), text_color=ACCENT_CYAN)
        left_title.pack(pady=(20, 15), padx=20, anchor="w")

        # Scrollable inputs
        scroll = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ID & Environment
        ctk.CTkLabel(scroll, text="Student Name", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
        self.ent_name = ctk.CTkEntry(scroll, textvariable=self.name_var, fg_color="#1A2333", border_color=GRID_COLOR, font=scaled_font("Arial", 12))
        self.ent_name.pack(fill="x", pady=(2, 10))
        self.ent_name.bind("<KeyRelease>", lambda e: self.recalculate())

        ctk.CTkLabel(scroll, text="SSN (12 Digits)", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
        self.ent_ssn = ctk.CTkEntry(scroll, textvariable=self.ssn_var, fg_color="#1A2333", border_color=GRID_COLOR, font=scaled_font("Arial", 12))
        self.ent_ssn.pack(fill="x", pady=(2, 10))
        self.ent_ssn.bind("<KeyRelease>", lambda e: self.recalculate())

        # Roughness presets
        ctk.CTkLabel(scroll, text="Surface Roughness (z0)", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
        self.opt_roughness = ctk.CTkOptionMenu(scroll, values=["Smooth Sea (z0 = 0.0002m)", "Grasslands (z0 = 0.05m)", "Suburbs/Forest (z0 = 0.3m)", "City/Dense Forest (z0 = 1.0m)"], 
                                               variable=self.roughness_var, command=self.on_roughness_change, font=scaled_font("Arial", 12),
                                               fg_color="#1A2333", button_color="#26344B")
        self.opt_roughness.pack(fill="x", pady=(2, 15))

        # Sliders
        self.lbl_diam = ctk.CTkLabel(scroll, text="Rotor Diameter: 95.0 m", font=scaled_font("Arial", 13))
        self.lbl_diam.pack(anchor="w", pady=(5, 0))
        self.slider_diam = ctk.CTkSlider(scroll, from_=10, to=200, variable=self.diam_var, progress_color=ACCENT_CYAN, command=self.on_slider_change)
        self.slider_diam.pack(fill="x", pady=(2, 12))

        self.lbl_height = ctk.CTkLabel(scroll, text="Hub Height: 105.0 m", font=scaled_font("Arial", 13))
        self.lbl_height.pack(anchor="w", pady=(5, 0))
        self.slider_height = ctk.CTkSlider(scroll, from_=10, to=200, variable=self.height_var, progress_color=ACCENT_CYAN, command=self.on_slider_change)
        self.slider_height.pack(fill="x", pady=(2, 15))

        # Drivetrain options
        ctk.CTkLabel(scroll, text="Gearbox Technology", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
        self.opt_gearbox = ctk.CTkOptionMenu(scroll, values=["None (Direct Drive)", "Medium Ratio", "High-Speed Gearbox"], 
                                              variable=self.gearbox_var, command=self.on_combo_change, fg_color="#1A2333", font=scaled_font("Arial", 12))
        self.opt_gearbox.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(scroll, text="Generator Selection", font=scaled_font("Arial", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 0))
        self.opt_generator = ctk.CTkOptionMenu(scroll, values=["Synchronous", "Asynchronous", "DFIG"], 
                                                variable=self.generator_var, command=self.on_combo_change, fg_color="#1A2333", font=scaled_font("Arial", 12))
        self.opt_generator.pack(fill="x", pady=(2, 15))


        # ----------------------------------------------------
        # 2. RIGHT COLUMN: CHARTS & FORMULA VIEW
        # ----------------------------------------------------
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=(10, 15), pady=15, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure((0, 1), weight=1) # Two large charts

        # --- CHART 1: WEIBULL WIND SPEED DISTRIBUTION ---
        self.chart1_frame = ctk.CTkFrame(self.right_frame, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.chart1_frame.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="nsew")
        self.chart1_frame.grid_columnconfigure(0, weight=1)
        self.chart1_frame.grid_rowconfigure(1, weight=1)

        c1_header = ctk.CTkFrame(self.chart1_frame, fg_color="transparent")
        c1_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))
        ctk.CTkLabel(c1_header, text="Weibull Wind Speed Distribution", font=scaled_font("Montserrat", 13, "bold"), text_color=TEXT_MAIN).pack(side="left")
        self.lbl_weibull_params = ctk.CTkLabel(c1_header, text="k = 0.0, A = 0.0 m/s", font=scaled_font("Arial", 11), text_color=ACCENT_CYAN)
        self.lbl_weibull_params.pack(side="right")

        self.canvas_weibull = tk.Canvas(self.chart1_frame, bg=BG_COLOR, highlightthickness=0)
        self.canvas_weibull.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 12))
        self.canvas_weibull.bind("<Configure>", lambda e: self.draw_weibull())

        # --- CHART 2: POWER CURVE & FORMULAS ---
        self.chart2_frame = ctk.CTkFrame(self.right_frame, fg_color=PANEL_BG, corner_radius=16, border_width=1, border_color=GRID_COLOR)
        self.chart2_frame.grid(row=1, column=0, padx=0, pady=(10, 0), sticky="nsew")
        
        self.chart2_frame.grid_columnconfigure(0, weight=6, minsize=420) # Power curve plot
        self.chart2_frame.grid_columnconfigure(1, weight=4, minsize=260) # Physics explanations
        self.chart2_frame.grid_rowconfigure(0, weight=1)

        # Plot Container (Left of chart 2 frame)
        self.plot2_container = ctk.CTkFrame(self.chart2_frame, fg_color="transparent")
        self.plot2_container.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=12)
        self.plot2_container.grid_columnconfigure(0, weight=1)
        self.plot2_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.plot2_container, text="Turbine Electrical Power Curve", font=scaled_font("Montserrat", 13, "bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.canvas_power = tk.Canvas(self.plot2_container, bg=BG_COLOR, highlightthickness=0)
        self.canvas_power.grid(row=1, column=0, sticky="nsew")
        self.canvas_power.bind("<Configure>", lambda e: self.draw_power_curve())

        # Physics Explanations (Right of chart 2 frame)
        self.edu_container = ctk.CTkFrame(self.chart2_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=GRID_COLOR)
        self.edu_container.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=12)
        
        edu_title = ctk.CTkLabel(self.edu_container, text="PHYSICS REFERENCE", font=scaled_font("Montserrat", 11, "bold"), text_color=ACCENT_CYAN)
        edu_title.pack(anchor="w", padx=12, pady=(10, 8))

        # Display Formulas in text format
        self.create_formula_box(self.edu_container, "Betz Limit Power Formula", "P_aero = 0.5 * rho * A * v^3 * Cp\nCp <= 16/27 (59.3%)")
        self.create_formula_box(self.edu_container, "Wind Shear Profile", "u(z) = u_10 * ln(z/z0) / ln(10/z0)")

        # Brief dynamic stats
        self.stats_frame = ctk.CTkFrame(self.edu_container, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=12, pady=5)
        
        self.lbl_rated_power = ctk.CTkLabel(self.stats_frame, text="Rated Power: 0 kW", font=scaled_font("Arial", 12, "bold"))
        self.lbl_rated_power.pack(anchor="w", pady=2)
        
        self.lbl_drivetrain_eff = ctk.CTkLabel(self.stats_frame, text="Drivetrain η: 0.0%", font=scaled_font("Arial", 12))
        self.lbl_drivetrain_eff.pack(anchor="w", pady=2)

        self.lbl_limit_status = ctk.CTkLabel(self.stats_frame, text="Operating limits: Safe", font=scaled_font("Arial", 12), text_color=ACCENT_GREEN)
        self.lbl_limit_status.pack(anchor="w", pady=2)

    def create_formula_box(self, parent, title, formula_text):
        box = ctk.CTkFrame(parent, fg_color="#0C0F17", corner_radius=8, border_width=1, border_color=GRID_COLOR)
        box.pack(fill="x", padx=12, pady=6)
        
        ctk.CTkLabel(box, text=title, font=scaled_font("Arial", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=8, pady=(6, 1))
        
        # Simulated math font look
        lbl_formula = ctk.CTkLabel(box, text=formula_text, font=scaled_font("Consolas", 10), text_color=ACCENT_GREEN, justify="left")
        lbl_formula.pack(anchor="w", padx=8, pady=(1, 8))

    # --- HANDLERS ---
    def on_slider_change(self, val):
        self.lbl_diam.configure(text=f"Rotor Diameter: {self.diam_var.get():.1f} m")
        self.lbl_height.configure(text=f"Hub Height: {self.height_var.get():.1f} m")
        self.recalculate()

    def on_roughness_change(self, val):
        self.recalculate()

    def on_combo_change(self, val):
        self.recalculate()

    # --- MATH & REDRAW ---
    def recalculate(self):
        # Graceful SSN parsing
        ssn = self.ssn_var.get().strip()
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

        # Roughness translation
        r_preset = self.roughness_var.get()
        if "Smooth Sea" in r_preset:
            z0 = 0.0002
        elif "Grasslands" in r_preset:
            z0 = 0.05
        elif "Suburbs" in r_preset:
            z0 = 0.3
        else:
            z0 = 1.0

        # Calculations
        self.k = (11 + m_factor) / 10 # Weibull k
        avg_U10 = (6 + d_factor / 10) - height / 50
        avg_U10 = max(2.0, avg_U10)
        
        # Log profile hub wind speed
        self.wind_nacelle = max(2.0, avg_U10 * math.log(max(1.1, height/z0)) / math.log(max(1.1, 10/z0)))
        
        g_arg = 1.0 + (1.0 / self.k)
        gamma_approx = 1.0
        if 1.0 <= g_arg <= 2.0:
            gamma_approx = 1.0 - 0.5772 * (g_arg - 1) + 0.9224 * ((g_arg - 1) ** 2) - 0.8984 * ((g_arg - 1) ** 3)
        self.weibull_A = self.wind_nacelle / max(0.5, gamma_approx)

        self.lbl_weibull_params.configure(text=f"k (shape) = {self.k:.2f}, A (scale) = {self.weibull_A:.2f} m/s")

        # Wind turbine power parameters
        self.cut_in = max(2.0, self.wind_nacelle * 0.4)
        self.rated_speed = max(6.0, self.wind_nacelle * 1.5)
        self.cut_out = min(30.0, self.rated_speed * 2.2)

        swept_area = math.pi * (diam / 2) ** 2
        capture_efficiency = max(0.25, 0.54 - m_factor / 100)
        efficiency_drivetrain = max(0.6, 0.94 - (pin_val - round(pin_val, -2)) / 400)
        
        # Options adjust efficiency
        gearbox = self.gearbox_var.get()
        if gearbox == "None (Direct Drive)":
            efficiency_drivetrain += 0.03
        elif gearbox == "High-Speed Gearbox":
            efficiency_drivetrain -= 0.02

        self.rated_power = 0.62 * (self.rated_speed ** 3) * swept_area * capture_efficiency * efficiency_drivetrain / 1000
        
        # Update text
        self.lbl_rated_power.configure(text=f"Rated Power: {self.rated_power:.1f} kW")
        self.lbl_drivetrain_eff.configure(text=f"Drivetrain η: {efficiency_drivetrain*100:.1f}%")
        
        ratio = height / diam
        if ratio > 4.0 or ratio < 0.4:
            self.lbl_limit_status.configure(text="⚠ Critical geometry ratio!", text_color=ACCENT_ORANGE)
        else:
            self.lbl_limit_status.configure(text="✓ Structural geometry OK", text_color=ACCENT_GREEN)

        # Redraw
        self.draw_weibull()
        self.draw_power_curve()

    def draw_weibull(self):
        """
        Draws the Weibull probability density curve on canvas_weibull.
        """
        if not hasattr(self, 'canvas_weibull') or self.canvas_weibull.winfo_width() < 10:
            return

        self.canvas_weibull.delete("all")
        w = self.canvas_weibull.winfo_width()
        h = self.canvas_weibull.winfo_height()

        # Scale factor for drawings
        scale = self.scale_factor

        # Margins
        mx, my = int(45 * scale), int(25 * scale)
        plot_w = w - 2 * mx
        plot_h = h - 2 * my

        # Draw axis lines
        self.canvas_weibull.create_line(mx, my, mx, h - my, fill=TEXT_MUTED, width=1.5 * scale)
        self.canvas_weibull.create_line(mx, h - my, w - mx, h - my, fill=TEXT_MUTED, width=1.5 * scale)

        # Labels
        self.canvas_weibull.create_text(mx - int(10 * scale), my, text="p(v)", fill=TEXT_MUTED, anchor="e", font=("Arial", int(9 * scale)))
        self.canvas_weibull.create_text(w - mx, h - my + int(15 * scale), text="Wind Speed (m/s)", fill=TEXT_MUTED, anchor="ne", font=("Arial", int(9 * scale)))

        # Max Wind Speed represented = 30 m/s
        max_v = 30.0
        # Peak probability estimation to scale Y axis
        mode = self.weibull_A * (((self.k - 1) / self.k) ** (1/self.k)) if self.k > 1 else 1.0
        peak_y = self.weibull_pdf(mode)
        max_y = max(0.1, peak_y * 1.3)

        # Draw grids
        v_steps = 6
        for i in range(v_steps + 1):
            val = (max_v / v_steps) * i
            x = mx + (val / max_v) * plot_w
            self.canvas_weibull.create_line(x, my, x, h - my, fill=GRID_COLOR, dash=(2, 3), width=1 * scale)
            self.canvas_weibull.create_text(x, h - my + int(10 * scale), text=f"{val:.0f}", fill=TEXT_MUTED, font=("Arial", int(8 * scale)))

        # Plot curves
        points = []
        res = 120
        for i in range(res + 1):
            v = (max_v / res) * i
            y_val = self.weibull_pdf(v)
            
            x = mx + (v / max_v) * plot_w
            y = h - my - (y_val / max_y) * plot_h
            points.append((x, y))

        # Shade operational zone: Cut-in to Cut-out
        cut_in_x = mx + (self.cut_in / max_v) * plot_w
        cut_out_x = mx + (self.cut_out / max_v) * plot_w
        
        # Build polygon under curve inside operational zone
        shade_pts = []
        shade_pts.append((cut_in_x, h - my))
        for x, y in points:
            # map back to wind speed
            v = ((x - mx) / plot_w) * max_v
            if self.cut_in <= v <= self.cut_out:
                shade_pts.append((x, y))
        shade_pts.append((cut_out_x, h - my))
        
        if len(shade_pts) > 2:
            flat_pts = []
            for px, py in shade_pts:
                flat_pts.extend([px, py])
            self.canvas_weibull.create_polygon(flat_pts, fill="#0E303A", outline="")

        # Draw Weibull curve line
        flat_points = []
        for px, py in points:
            flat_points.extend([px, py])
        self.canvas_weibull.create_line(flat_points, fill=ACCENT_CYAN, width=2.5 * scale)

        # Draw markers/text for Cut-in & Cut-out limits
        self.canvas_weibull.create_line(cut_in_x, my, cut_in_x, h - my, fill=ACCENT_ORANGE, dash=(3, 2), width=1 * scale)
        self.canvas_weibull.create_text(cut_in_x, my - int(10 * scale), text="Cut-In", fill=ACCENT_ORANGE, font=("Arial", int(8 * scale)))
        
        self.canvas_weibull.create_line(cut_out_x, my, cut_out_x, h - my, fill=ACCENT_ORANGE, dash=(3, 2), width=1 * scale)
        self.canvas_weibull.create_text(cut_out_x, my - int(10 * scale), text="Cut-Out", fill=ACCENT_ORANGE, font=("Arial", int(8 * scale)))

    def draw_power_curve(self):
        """
        Draws the turbine power curve.
        """
        if not hasattr(self, 'canvas_power') or self.canvas_power.winfo_width() < 10:
            return

        self.canvas_power.delete("all")
        w = self.canvas_power.winfo_width()
        h = self.canvas_power.winfo_height()

        # Scale factor
        scale = self.scale_factor

        mx, my = int(40 * scale), int(20 * scale)
        plot_w = w - 2 * mx
        plot_h = h - 2 * my

        self.canvas_power.create_line(mx, my, mx, h - my, fill=TEXT_MUTED, width=1.5 * scale)
        self.canvas_power.create_line(mx, h - my, w - mx, h - my, fill=TEXT_MUTED, width=1.5 * scale)

        max_v = 30.0
        max_p = self.rated_power * 1.25

        # Grids
        for i in range(6):
            val = (max_v / 5) * i
            x = mx + (val / max_v) * plot_w
            self.canvas_power.create_line(x, my, x, h - my, fill=GRID_COLOR, dash=(2, 3), width=1 * scale)
            self.canvas_power.create_text(x, h - my + int(10 * scale), text=f"{val:.0f}", fill=TEXT_MUTED, font=("Arial", int(8 * scale)))

        # Power curve points
        points = []
        res = 120
        for i in range(res + 1):
            v = (max_v / res) * i
            
            # 4 Zones
            if v < self.cut_in:
                p = 0.0
            elif v <= self.rated_speed:
                # Cubic rise
                p_ratio = (v - self.cut_in) / (self.rated_speed - self.cut_in)
                p = self.rated_power * (p_ratio ** 3)
            elif v <= self.cut_out:
                p = self.rated_power
            else:
                p = 0.0
                
            x = mx + (v / max_v) * plot_w
            y = h - my - (p / max_p) * plot_h
            points.append((x, y))

        flat_pts = []
        for px, py in points:
            flat_pts.extend([px, py])
            
        self.canvas_power.create_line(flat_pts, fill=ACCENT_GREEN, width=2.5 * scale)

        # Highlight zones with labels
        rated_x = mx + (self.rated_speed / max_v) * plot_w
        self.canvas_power.create_line(rated_x, my, rated_x, h - my, fill=TEXT_MUTED, dash=(4, 4), width=1 * scale)
        
        # Draw Zone labels
        # Zone 1
        z1_cx = mx + (self.cut_in / max_v) * plot_w / 2
        self.canvas_power.create_text(z1_cx, h - my - int(15 * scale), text="Zone 1\n(Idle)", fill=TEXT_MUTED, font=("Arial", int(8 * scale)), justify="center")
        
        # Zone 2
        z2_cx = (mx + (self.cut_in / max_v) * plot_w + rated_x) / 2
        self.canvas_power.create_text(z2_cx, h - my - int(40 * scale), text="Zone 2\n(Variable)", fill=TEXT_MUTED, font=("Arial", int(8 * scale)), justify="center")
        
        # Zone 3
        cut_out_x = mx + (self.cut_out / max_v) * plot_w
        z3_cx = (rated_x + cut_out_x) / 2
        self.canvas_power.create_text(z3_cx, h - my - int(80 * scale), text="Zone 3\n(Capped)", fill=TEXT_MUTED, font=("Arial", int(8 * scale)), justify="center")

        # Label Y axis values
        self.canvas_power.create_text(mx - int(8 * scale), h - my - (self.rated_power / max_p) * plot_h, text=f"{self.rated_power:.0f}kW", fill=ACCENT_GREEN, anchor="e", font=("Arial", int(8 * scale), "bold"))

    def weibull_pdf(self, v):
        if v <= 0 or self.weibull_A <= 0:
            return 0
        return (self.k / self.weibull_A) * ((v / self.weibull_A) ** (self.k - 1)) * math.exp(-((v / self.weibull_A) ** self.k))

if __name__ == "__main__":
    app = EngineeringNotebookApp()
    app.mainloop()
