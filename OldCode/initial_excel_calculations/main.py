import customtkinter as ctk
import math
from initial_excel_calculations.economics import Economics
from initial_excel_calculations.energy_calculations import EnergyCalculations
from initial_excel_calculations.user_input import InputData

class VindApp(ctk.CTk):
    """
    Main Application class for the Wind Power Simulator Pro.

    Provides a graphical user interface (GUI) using CustomTkinter to interact
    with the wind power simulation models.

    Attributes
    ----------
    name_var : ctk.StringVar
        Observable string for the user's name.
    ssn_var : ctk.StringVar
        Observable string for the Social Security Number.
    diam_var : ctk.DoubleVar
        Observable float for the turbine rotor diameter.
    height_var : ctk.DoubleVar
        Observable float for the turbine tower height.
    """
    def __init__(self):
        super().__init__()

        # --- WINDOW SETTINGS ---
        self.title("Wind Power Simulator Pro")
        self.geometry("500x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- APP VARIABLES ---
        self.name_var = ctk.StringVar(value="Gustav Gamstedt")
        self.ssn_var = ctk.StringVar(value="199801281234")
        self.diam_var = ctk.DoubleVar(value=37.0)
        self.height_var = ctk.DoubleVar(value=44.0)

        # --- CREATE UI ---
        self.create_widgets()
        self.update_calculations()

    def create_widgets(self):
        """
        Initialize and arrange all UI components in the main window.
        """
        # Main Title
        title = ctk.CTkLabel(self, text="Wind Turbine Simulator", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # --- INPUT SECTION ---
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(input_frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(input_frame, textvariable=self.name_var).grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="SSN (YYYYMMDDXXXX):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(input_frame, textvariable=self.ssn_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        input_frame.columnconfigure(1, weight=1)

        # Slider 1: Diameter
        self.lbl_diam = ctk.CTkLabel(self, text="Diameter: 37.0 m", font=("Arial", 16))
        self.lbl_diam.pack(pady=(15, 5))
        self.slider_diam = ctk.CTkSlider(self, from_=10, to=200, number_of_steps=190, variable=self.diam_var, command=self.update_calculations)
        self.slider_diam.pack(pady=5, fill="x", padx=40)

        # Slider 2: Height
        self.lbl_height = ctk.CTkLabel(self, text="Height: 44.0 m", font=("Arial", 16))
        self.lbl_height.pack(pady=(15, 5))
        self.slider_height = ctk.CTkSlider(self, from_=10, to=200, number_of_steps=190, variable=self.height_var, command=self.update_calculations)
        self.slider_height.pack(pady=5, fill="x", padx=40)

        # --- VISUALIZATION BOX ---
        self.vis_frame = ctk.CTkFrame(self, width=380, height=100, fg_color="#1a1a24")
        self.vis_frame.pack(pady=10)
        self.vis_frame.pack_propagate(False)

        self.vis_title = ctk.CTkLabel(self.vis_frame, text="Profitability Margin", font=("Arial", 12), text_color="#888888")
        self.vis_title.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self.vis_frame, width=300, height=15, progress_color="#00FFFF")
        self.progress.pack(pady=10)
        self.progress.set(0)

        # --- OUTPUT ---
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.lbl_power = ctk.CTkLabel(self.output_frame, text="Rated Power: 0.0 kW", font=("Arial", 14))
        self.lbl_power.pack(pady=2)

        self.lbl_energy = ctk.CTkLabel(self.output_frame, text="Annual Energy: 0.0 MWh", font=("Arial", 14))
        self.lbl_energy.pack(pady=2)

        self.lbl_profit = ctk.CTkLabel(self.output_frame, text="Total Profit: 0.0 k€", font=("Arial", 14))
        self.lbl_profit.pack(pady=2)

        self.lbl_margin = ctk.CTkLabel(self.output_frame, text="0.0%", font=("Arial", 36, "bold"), text_color="#00FFFF")
        self.lbl_margin.pack(pady=10)

    def update_calculations(self, *args):
        """
        Triggered when input variables change. 
        
        Runs the full simulation pipeline and updates the UI labels 
        and visualizations.

        Parameters
        ----------
        *args : list
            Optional arguments passed by Tkinter events.
        """
        try:
            name = self.name_var.get()
            ssn = self.ssn_var.get()
            diam = self.diam_var.get()
            height = self.height_var.get()

            # Update labels
            self.lbl_diam.configure(text=f"Diameter: {diam:.1f} m")
            self.lbl_height.configure(text=f"Height: {height:.1f} m")

            # Perform simulation
            input_data = InputData(name, ssn, diam=int(diam), height=int(height))
            energy_calc = EnergyCalculations(input_data)
            results = energy_calc.calculate()
            econ = Economics(input_data, results)
            capex = econ.capital_costs()
            profits, margin = econ.calculate_profits()

            # Update UI
            self.lbl_power.configure(text=f"Rated Power: {results.rated_power:.1f} kW")
            self.lbl_energy.configure(text=f"Annual Energy: {results.generated_energy:.1f} MWh")
            self.lbl_profit.configure(text=f"Total Profit: {profits:.1f} k€")
            self.lbl_margin.configure(text=f"{margin*100:.1f}%")
            
            # Update progress bar (scale margin 0-100% to 0-1.0)
            self.progress.set(max(0, min(margin, 1.0)))
        except Exception as e:
            # Silently fail or log if SSN is invalid while typing
            pass

if __name__ == "__main__":
    app = VindApp()
    app.mainloop()
