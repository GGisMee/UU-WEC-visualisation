import customtkinter as ctk
import math

class VindApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- FÖNSTERINSTÄLLNINGAR ---
        self.title("Vindkraft Simulator Pro")
        self.geometry("460x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- APPVARIABLER ---
        self.vind_var = ctk.DoubleVar(value=10.0)
        self.radie_var = ctk.DoubleVar(value=40.0)

        # --- SKAPA UI ---
        self.skapa_widgets()
        self.uppdatera_berakning()

    def skapa_widgets(self):
        # Huvudtitel
        titel = ctk.CTkLabel(self, text="Wind Turbine Simulator", font=("Arial", 24, "bold"))
        titel.pack(pady=20)

        # --- VISUALISERINGSRUTA (Simulerad mätare) ---
        self.vis_ram = ctk.CTkFrame(self, width=380, height=100, fg_color="#1a1a24")
        self.vis_ram.pack(pady=10)
        self.vis_ram.pack_propagate(False)

        self.vis_titel = ctk.CTkLabel(self.vis_ram, text="Turbinstatus (Effektindikator)", font=("Arial", 12), text_color="#888888")
        self.vis_titel.pack(pady=5)

        # En framstegsbar som indikerar hur nära maxeffekt vi är
        self.progress = ctk.CTkProgressBar(self.vis_ram, width=300, height=15, progress_color="#00FFFF")
        self.progress.pack(pady=10)
        self.progress.set(0)

        # Slider 1: Vindhastighet
        self.lbl_vind = ctk.CTkLabel(self, text="Vindhastighet: 10.0 m/s", font=("Arial", 16))
        self.lbl_vind.pack(pady=(15, 5))
        
        # Ändrat från px=40 till padx=40 här:
        self.slider_vind = ctk.CTkSlider(self, from_=0, to=30, number_of_steps=30, variable=self.vind_var, command=self.uppdatera_berakning)
        self.slider_vind.pack(pady=5, fill="x", padx=40)

        # Slider 2: Rotorradie
        self.lbl_radie = ctk.CTkLabel(self, text="Rotorradie: 40 m", font=("Arial", 16))
        self.lbl_radie.pack(pady=(15, 5))
        
        # Och ändrat från px=40 till padx=40 här:
        self.slider_radie = ctk.CTkSlider(self, from_=10, to=100, number_of_steps=18, variable=self.radie_var, command=self.uppdatera_berakning)
        self.slider_radie.pack(pady=5, fill="x", padx=40)

        # --- OUTPUT ---
        lbl_output_titel = ctk.CTkLabel(self, text="Genererad Effekt:", font=("Arial", 14), text_color="#888888")
        lbl_output_titel.pack(pady=(30, 5))

        self.lbl_effekt = ctk.CTkLabel(self, text="0.0 kW", font=("Arial", 36, "bold"), text_color="#00FFFF")
        self.lbl_effekt.pack(pady=5)

    def uppdatera_berakning(self, *args):
        vind = self.vind_var.get()
        radie = self.radie_var.get()

        # Uppdatera etiketterna bredvid sliders
        self.lbl_vind.configure(text=f"Vindhastighet: {vind:.1f} m/s")
        self.lbl_radie.configure(text=f"Rotorradie: {int(radie)} m")

        # Fysikberäkning (Cut-in vid 3 m/s, Cut-out vid 25 m/s)
        if vind < 3.0 or vind > 25.0:
            kw = 0.0
        else:
            rho = 1.225
            area = math.pi * (radie ** 2)
            verkningsgrad = 0.45
            effekt_w = 0.5 * rho * area * (vind ** 3) * verkningsgrad
            kw = effekt_w / 1000

        # Uppdatera gränssnittet
        self.lbl_effekt.configure(text=f"{kw:.1f} kW")
        
        # Uppdatera mätaren (max sätter vi till 5000 kW för skalningens skull)
        max_skala = 5000.0
        procent = min(kw / max_skala, 1.0)
        self.progress.set(procent)

if __name__ == "__main__":
    app = VindApp()
    app.mainloop()