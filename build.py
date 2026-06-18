import PyInstaller.__main__
import customtkinter
import os

# Get path to customtkinter to include its assets (themes, fonts, etc.)
customtkinter_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    'src/wec_visualisation/main.py',
    '--name=WEC_Simulator',
    '--onefile',
    '--windowed',  # Prevent console window from appearing on Windows
    f'--add-data={customtkinter_path}:customtkinter',  # Include CTk assets
    '--clean',
])

print("Build complete! Check the 'dist' directory for the executable.")
