import customtkinter as ctk
import subprocess
import sys
import os

# --- DESIGN SYSTEM ---
BG_COLOR = "#0A0D14"
CARD_BG = "#121824"
CARD_BORDER = "#222D42"
ACCENT_BLUE = "#3B82F6"
ACCENT_CYAN = "#06B6D4"
ACCENT_GREEN = "#10B981"
TEXT_MAIN = "#F9FAFB"
TEXT_MUTED = "#9CA3AF"

def load_scale_factor():
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        scale_path = os.path.join(dir_path, "scale.txt")
        if os.path.exists(scale_path):
            with open(scale_path, "r") as f:
                return float(f.read().strip())
    except Exception:
        pass
    return 1.35  # Comfortable default scaling for High-DPI laptop screen on Linux

def save_scale_factor(value):
    try:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        scale_path = os.path.join(dir_path, "scale.txt")
        with open(scale_path, "w") as f:
            f.write(str(value))
    except Exception:
        pass

def scaled_font(family, size, weight=None):
    if weight:
        return (family, size, weight)
    return (family, size)


class UIStudioLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- SCALING SETUP ---
        self.scale_factor = load_scale_factor()
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

        # --- WINDOW SETUP ---
        self.title("Wind Power Simulator - UI Design Studio Launcher")
        self.geometry("620x580")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        
        self.configure(fg_color=BG_COLOR)

        # Header Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(25, 15))
        
        ctk.CTkLabel(title_frame, text="WIND POWER SIMULATOR PRO", font=scaled_font("Montserrat", 10, "bold"), text_color=ACCENT_BLUE).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Select a User Interface Mockup", font=scaled_font("Montserrat", 22, "bold"), text_color=TEXT_MAIN).pack(anchor="w")
        
        desc = ("Evaluate different visual design directions and interaction layouts below. "
                "Each mockup runs in a separate window with interactive models.")
        ctk.CTkLabel(title_frame, text=desc, font=scaled_font("Arial", 12), text_color=TEXT_MUTED, justify="left", wraplength=560).pack(anchor="w", pady=5)

        # Mockup 1 Card
        self.create_mockup_row("Mockup A: Visual CAD Blueprint", 
                               "Focuses on a real-time engineering blueprint sketch that scales turbine geometry and highlights safety margins on a technical canvas.",
                               "Launch CAD Blueprint", ACCENT_CYAN, "mockup_cad_blueprint.py")

        # Mockup 2 Card
        self.create_mockup_row("Mockup B: Management Tycoon Dashboard", 
                               "Features a clean management layout with a projects grade scorecard, circular KPIs, tabbed parameters, and a colorful breakdown bar.",
                               "Launch Tycoon Board", ACCENT_GREEN, "mockup_dashboard.py")

        # Mockup 3 Card
        self.create_mockup_row("Mockup C: Educational Engineering Notebook", 
                               "Designed for classrooms and research, featuring dynamic plot curves for the Weibull distribution and power outputs alongside key equations.",
                               "Launch Notebook", ACCENT_BLUE, "mockup_engineering.py")

        # DPI Settings Footer
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="x", padx=30, pady=(15, 10))
        
        ctk.CTkLabel(settings_frame, text="DPI Scaling (Adjust for laptop screen size):", font=scaled_font("Arial", 11), text_color=TEXT_MUTED).pack(side="left")
        
        scale_options = ["100% (Default)", "120% (Compact)", "135% (Comfortable)", "150% (Large)", "175% (Very Large)", "200% (High-DPI)"]
        
        # Match current scale to options
        initial_val = "135% (Comfortable)"
        if self.scale_factor == 1.0: initial_val = "100% (Default)"
        elif self.scale_factor == 1.2: initial_val = "120% (Compact)"
        elif self.scale_factor == 1.35: initial_val = "135% (Comfortable)"
        elif self.scale_factor == 1.5: initial_val = "150% (Large)"
        elif self.scale_factor == 1.75: initial_val = "175% (Very Large)"
        elif self.scale_factor == 2.0: initial_val = "200% (High-DPI)"
        
        self.opt_scale = ctk.CTkOptionMenu(settings_frame, values=scale_options, command=self.on_scale_change, width=160, height=28,
                                            fg_color=CARD_BG, button_color=CARD_BORDER, button_hover_color=ACCENT_BLUE)
        self.opt_scale.set(initial_val)
        self.opt_scale.pack(side="right")

    def create_mockup_row(self, title, desc_text, btn_text, accent_color, filename):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", padx=30, pady=8)
        
        # Details Left
        details = ctk.CTkFrame(card, fg_color="transparent")
        details.pack(side="left", fill="both", expand=True, padx=15, pady=12)
        
        ctk.CTkLabel(details, text=title, font=scaled_font("Montserrat", 13, "bold"), text_color=accent_color).pack(anchor="w")
        ctk.CTkLabel(details, text=desc_text, font=scaled_font("Arial", 11), text_color=TEXT_MUTED, justify="left", wraplength=340).pack(anchor="w", pady=(2, 0))
        
        # Button Right
        btn = ctk.CTkButton(card, text=btn_text, font=scaled_font("Arial", 12, "bold"), fg_color=accent_color, hover_color=self.darken_color(accent_color),
                             text_color="white" if accent_color != ACCENT_GREEN else "black", width=140, height=36,
                             command=lambda: self.launch_script(filename))
        btn.pack(side="right", padx=15, pady=12)

    def launch_script(self, filename):
        # Resolve full path of script
        dir_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(dir_path, filename)
        
        # Run process detached
        subprocess.Popen([sys.executable, script_path])

    def on_scale_change(self, choice):
        mapping = {
            "100% (Default)": 1.0,
            "120% (Compact)": 1.2,
            "135% (Comfortable)": 1.35,
            "150% (Large)": 1.5,
            "175% (Very Large)": 1.75,
            "200% (High-DPI)": 2.0
        }
        val = mapping.get(choice, 1.35)
        save_scale_factor(val)
        
        # Show message box explaining restart is required
        restart_lbl = ctk.CTkLabel(self, text="* UI scale saved. Please restart launcher to apply changes.", font=scaled_font("Arial", 10), text_color=ACCENT_GREEN)
        restart_lbl.pack(pady=(5, 5))
        self.after(4000, restart_lbl.destroy)

    def darken_color(self, hex_color):
        # Simple color dimmer for hover effects
        if hex_color == ACCENT_CYAN: return "#0891B2"
        if hex_color == ACCENT_GREEN: return "#059669"
        if hex_color == ACCENT_BLUE: return "#2563EB"
        return hex_color

if __name__ == "__main__":
    app = UIStudioLauncher()
    app.mainloop()
