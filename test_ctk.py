import tkinter as tk
import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x300")

def toggle():
    current = ctk.get_appearance_mode()
    new_mode = "Dark" if current == "Light" else "Light"
    ctk.set_appearance_mode(new_mode)

btn = ctk.CTkButton(app, text="Toggle", command=toggle)
btn.pack(pady=10)

pw = tk.PanedWindow(app)
pw.pack(fill="both", expand=True)

frame = ctk.CTkFrame(pw, fg_color=("red", "blue"))
pw.add(frame)

lbl = ctk.CTkLabel(frame, text="Hello", text_color=("black", "white"))
lbl.pack(pady=20)

app.after(1000, toggle)
app.after(2000, app.destroy)
app.mainloop()
