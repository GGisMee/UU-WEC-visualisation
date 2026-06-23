import customtkinter as ctk
import tkinter as tk

app = ctk.CTk()
var = tk.StringVar(value="")
e1 = ctk.CTkEntry(app, placeholder_text="No variable")
e1.pack(pady=10)
e2 = ctk.CTkEntry(app, textvariable=var, placeholder_text="With variable")
e2.pack(pady=10)

# Check internal state or just run and quit? We can't see the GUI easily unless we take a screenshot or just check the source code of CTkEntry.
# Let's inspect CTkEntry code.
import inspect
print("CTkEntry code:")
# print(inspect.getsource(ctk.CTkEntry._activate_placeholder))
