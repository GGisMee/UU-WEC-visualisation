import customtkinter as ctk

class ScaleTestApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("Linux High-DPI Font Scaling Lab")
        self.geometry("550x400")
        
        self.scale_factor = 1.0
        
        # Create UI
        self.create_widgets()

    def create_widgets(self):
        # Top title (unscaled font configuration, customtkinter will scale it automatically)
        self.title_lbl = ctk.CTkLabel(self, text="DPI Scaling Experiment", font=("Arial", 20, "bold"))
        self.title_lbl.pack(pady=15)

        # Frame for controls
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.pack(fill="x", padx=20, pady=10)

        # Scale slider
        self.lbl_scale = ctk.CTkLabel(self.ctrl_frame, text="Active Scale Factor: 1.0x", font=("Arial", 12))
        self.lbl_scale.pack(pady=(10, 2))
        
        self.slider = ctk.CTkSlider(self.ctrl_frame, from_=1.0, to=2.5, number_of_steps=15, command=self.on_slider_change)
        self.slider.set(1.0)
        self.slider.pack(fill="x", padx=20, pady=(0, 15))

        # Sample box to show the difference
        self.sample_frame = ctk.CTkFrame(self, fg_color="#1E293B")
        self.sample_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Labels with standard unscaled font sizes (customtkinter scales these automatically!)
        self.lbl_small = ctk.CTkLabel(self.sample_frame, text="Small Text (font=('Arial', 11))", font=("Arial", 11))
        self.lbl_small.pack(pady=10)

        self.lbl_medium = ctk.CTkLabel(self.sample_frame, text="Medium Text (font=('Arial', 14))", font=("Arial", 14), text_color="#10B981")
        self.lbl_medium.pack(pady=10)

        self.lbl_large = ctk.CTkLabel(self.sample_frame, text="Large Text (font=('Arial', 18))", font=("Arial", 18), text_color="#00D2FF")
        self.lbl_large.pack(pady=10)

        # Test Button
        self.btn = ctk.CTkButton(self.sample_frame, text="Interactive Button (font=('Arial', 13))", font=("Arial", 13))
        self.btn.pack(pady=10)

    def on_slider_change(self, val):
        self.scale_factor = round(val, 2)
        self.lbl_scale.configure(text=f"Active Scale Factor: {self.scale_factor}x")
        
        # Apply CustomTkinter widget and window scaling.
        # CustomTkinter automatically handles scaling for all widget dimensions and fonts!
        ctk.set_widget_scaling(self.scale_factor)
        ctk.set_window_scaling(self.scale_factor)

if __name__ == "__main__":
    app = ScaleTestApp()
    app.mainloop()
