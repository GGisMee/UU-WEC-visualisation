# gui/theme.py
from enum import Enum

class FusionTheme(Enum):
    # Format: VALUE = ("light_mode_hex", "dark_mode_hex")
    BG_MAIN = ("#F5F5F5", "#3B4453")
    BG_SURFACE = ("#FFFFFF", "#2C3440")
    BG_INPUT = ("#FFFFFF", "#282828")
    TEXT_MAIN = ("#000000", "#F5F5F5")
    TEXT_MUTED = ("#3C3C3C", "#9CA3AF")  # Improved readability in dark mode
    BORDER = ("#C8C8C8", "#505864")
    ACCENT = ("#ED742E", "#ED742E")  # Fusion 360 Orange
    DELETE_HOVER = ("#BE3035", "#FF8D92")
    
    # Tooltip
    TOOLTIP_BG = ("#272E3A", "#161F2D")
    TOOLTIP_TEXT = ("#E8ECF2", "#DCE5F1")
    TOOLTIP_BORDER = ("#4A5361", "#3E4A5E")
    
    # Scrollbar
    SCROLLBAR_TRACK = ("#E6E6E6", "#222832")
    SCROLLBAR_THUMB = ("#AAAAAA", "#626C7A")
    SCROLLBAR_THUMB_HOVER = ("#8C8C8C", "#7A8492")
    
    # Status Colors
    SUCCESS = ("#059669", "#10B981")     # Emerald Green
    ALERT = ("#D9A300", "#FFD000")       # Alert Yellow
    DANGER = ("#E11D48", "#FF3E6C")      # Cyber Red
    INFO = ("#00A3C4", "#00D2FF")        # Electric Cyan
