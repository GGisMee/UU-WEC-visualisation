# main.py
from wec_visualisation.gui.app import UnifiedSimulatorApp
from scipy.optimize import least_squares

if __name__ == "__main__":
    app = UnifiedSimulatorApp()
    app.mainloop()
