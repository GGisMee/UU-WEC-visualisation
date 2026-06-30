import PyInstaller.__main__
import customtkinter
import os

# Get path to customtkinter to include its assets (themes, fonts, etc.)
customtkinter_path = os.path.dirname(customtkinter.__file__)

import subprocess
import shutil
import sys

sep = os.pathsep

# 1. Obfuscate the code with PyArmor
print("Obfuscating source code with PyArmor...")
# Clean any previous obfuscation runs
shutil.rmtree("obfuscated_src", ignore_errors=True)

# Generate obfuscated code into the 'obfuscated_src' directory
subprocess.run([sys.executable, "-m", "pyarmor.cli", "gen", "-O", "obfuscated_src", "-r", "src/wec_visualisation"], check=True)

# 2. Build the obfuscated code using PyInstaller
print("Building executable with PyInstaller...")
customtkinter_path = os.path.dirname(customtkinter.__file__)

import glob
runtime_pkg = os.path.basename(glob.glob("obfuscated_src/pyarmor_runtime_*")[0])

# Because PyArmor obfuscates imports, PyInstaller can't auto-detect them.
# We manually collect all our modules as hidden imports to guarantee inclusion.
hidden_imports = []
for root, dirs, files in os.walk("src/wec_visualisation"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            mod = path.replace("src/", "").replace(os.sep, ".").replace(".py", "")
            hidden_imports.extend(['--hidden-import', mod])

# Add critical third-party and standard library dependencies that PyInstaller misses
hidden_imports.extend([
    '--hidden-import', 'tomllib',
    '--hidden-import', 'tomli_w',
    '--hidden-import', 'customtkinter',
    '--hidden-import', 'tkinter',
    '--hidden-import', 'tkinter.filedialog',
    '--hidden-import', 'matplotlib',
    '--hidden-import', 'matplotlib.figure',
    '--hidden-import', 'matplotlib.backends.backend_tkagg',
    '--hidden-import', 'matplotlib.backends.backend_pdf',
    '--hidden-import', 'matplotlib.image',
    '--hidden-import', 'matplotlib.pyplot',
    '--hidden-import', 'numpy',
    '--hidden-import', 'numpy.polynomial',
    '--hidden-import', 'scipy',
    '--hidden-import', 'scipy.interpolate',
    '--hidden-import', 'scipy.special',
    '--hidden-import', 'scipy.optimize',
    '--hidden-import', 'PIL',
    '--hidden-import', 'PIL.Image',
    '--hidden-import', 'csv',
    '--hidden-import', 'zipfile',
    '--hidden-import', 'tempfile',
])

pyinstaller_args = [
    'obfuscated_src/wec_visualisation/main.py',
    '--name=WEC_Visualisation',
    '--onefile',
    '--windowed',
    f'--add-data={customtkinter_path}{sep}customtkinter',
    f'--add-data=src/wec_visualisation/assets{sep}assets',  # <-- ÄNDRAD HÄR
    '--paths=obfuscated_src',
    f'--hidden-import={runtime_pkg}',
    '--clean',
] + hidden_imports


PyInstaller.__main__.run(pyinstaller_args)

# 3. Clean up the temporary obfuscated source
shutil.rmtree("obfuscated_src", ignore_errors=True)

print("Build complete! Check the 'dist' directory for the highly secure executable.")
