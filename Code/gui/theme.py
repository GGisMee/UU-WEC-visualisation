# gui/theme.py
from enum import Enum, nonmember

class FontStyles:
    """
    A class that defines typography configurations for a given font family.
    
    Attributes
    ----------
    family : str
        The font family name (e.g., "Artifakt Element").
    TITLE : tuple
        Font configuration for large titles.
    SUBTITLE : tuple
        Font configuration for panel subtitles.
    BODY : tuple
        Font configuration for standard body text.
    BODY_BOLD : tuple
        Font configuration for bold body text.
    MUTED : tuple
        Font configuration for small/muted descriptions.
    MUTED_BOLD : tuple
        Font configuration for small/bold descriptions.
    HEADER : tuple
        Font configuration for headers.
    """
    def __init__(self, family: str):
        self.family = family
        self.TITLE = (family, 14, "bold")
        self.SUBTITLE = (family, 12, "bold")
        self.BODY = (family, 11)
        self.BODY_BOLD = (family, 11, "bold")
        self.MUTED = (family, 10)
        self.MUTED_BOLD = (family, 10, "bold")
        self.HEADER = (family, 9, "bold")


class FusionTheme(Enum):
    """
    Autodesk Fusion 360-inspired color theme tokens (Light/Dark mode hex pairs).
    """
    # Format: VALUE = ("light_mode_hex", "dark_mode_hex")
    BG_MAIN = ("#F5F5F5", "#3B4453")
    BG_SURFACE = ("#FFFFFF", "#2C3440")
    BG_INPUT = ("#F0F0F0", "#202630")
    TEXT_MAIN = ("#000000", "#F5F5F5")
    TEXT_MUTED = ("#5F6B7C", "#9CA3AF")
    BORDER = ("#C8C8C8", "#505864")
    BORDER_HOVER = ("#A0A0A0", "#707884")
    
    # Orange Accents
    ACCENT = ("#ED742E", "#ED742E")
    ACCENT_HOVER = ("#CC5200", "#CC5200")
    TEXT_ACCENT = ("#ED742E", "#ED742E")
    
    # Button Colors
    BUTTON_BG = ("#E0E5EC", "#3A4454")
    BUTTON_HOVER = ("#D0D5DC", "#4A5464")
    TAB_SELECTED = ("#ED742E", "#ED742E")
    TAB_SELECTED_HOVER = ("#CC5200", "#CC5200")
    BOX_BG = ("#F5F5F5", "#3B4453")
    
    # Alert / Status Colors
    SUCCESS = ("#059669", "#10B981")
    ALERT = ("#D9A300", "#FFD000")
    ALERT_BG = ("#FEF3C7", "#332B12")
    DANGER = ("#E11D48", "#FF3E6C")
    INFO = ("#00A3C4", "#00D2FF")
    
    # Slider Styles
    SLIDER_BG = ("#F0F0F0", "#202630")
    SLIDER_PROGRESS = ("#ED742E", "#ED742E")
    SLIDER_BUTTON = ("#ED742E", "#ED742E")
    SLIDER_BUTTON_HOVER = ("#CC5200", "#CC5200")
    
    # Blueprint Canvas Elements
    BLUEPRINT_BG = ("#E6ECF5", "#0B132B")
    BLUEPRINT_GRID = ("#D3DCEB", "#121D33")
    BLUEPRINT_STEEL = ("#4A5568", "#64748B")
    BLUEPRINT_BASE = ("#2D3748", "#1E293B")
    BLUEPRINT_BLADE = ("#FFFFFF", "#F8FAFC")
    CHART_BG = ("#FFFFFF", "#0F172A")
    CONCRETE = ("#7F8C8D", "#4B5563")

    # Define typography hierarchy directly inside the Enum using enum.nonmember
    fonts = nonmember(FontStyles("Artifakt Element"))


class Futuristic(Enum):
    """
    Futuristic Cyber-Slate & Tech Orange color theme tokens (Light/Dark mode hex pairs)
    inspired by the design of mockup_unified_challenge.
    """
    # Format: VALUE = ("light_mode_hex", "dark_mode_hex")
    BG_MAIN = ("#E6F0FA", "#080D16")
    BG_SURFACE = ("#F0F4F8", "#111827") 
    BG_INPUT = ("#DCE4EC", "#1A2238")
    TEXT_MAIN = ("#0F172A", "#F9FAFB")
    TEXT_MUTED = ("#475569", "#9CA3AF")
    BORDER = ("#CBD5E1", "#2D3748")
    BORDER_HOVER = ("#94A3B8", "#475569")
    
    # Tech Orange Accent
    ACCENT = ("#FF7A00", "#FF7A00")
    ACCENT_HOVER = ("#CC6200", "#CC6200")
    TEXT_ACCENT = ("#00A3C4", "#00D2FF")
    
    # Button Colors
    BUTTON_BG = ("#D3DFEE", "#223147")
    BUTTON_HOVER = ("#00A3C4", "#00D2FF")
    TAB_SELECTED = ("#3B8ED0", "#1F6AA5")
    TAB_SELECTED_HOVER = ("#2C74B3", "#1A5B8C")
    BOX_BG = ("#CBD5E1", "#2D3748")
    
    # Alert / Status Colors
    SUCCESS = ("#059669", "#10B981")
    ALERT = ("#D9A300", "#FFD000")
    ALERT_BG = ("#FEF3C7", "#332B12")
    DANGER = ("#E11D48", "#FF3E6C")
    INFO = ("#00A3C4", "#00D2FF")
    
    # Slider Styles
    SLIDER_BG = ("#E2E8F0", "#2D3748")
    SLIDER_PROGRESS = ("#94A3B8", "#64748B")
    SLIDER_BUTTON = ("#00A3C4", "#00D2FF")
    SLIDER_BUTTON_HOVER = ("#0082A0", "#00B4DB")
    
    # Blueprint Canvas Elements
    BLUEPRINT_BG = ("#E6ECF5", "#0B132B")
    BLUEPRINT_GRID = ("#D3DCEB", "#121D33")
    BLUEPRINT_STEEL = ("#475569", "#334155")
    BLUEPRINT_BASE = ("#1E293B", "#1E293B")
    BLUEPRINT_BLADE = ("#F8FAFC", "#F8FAFC")
    CHART_BG = ("#FFFFFF", "#10172A")
    CONCRETE = ("#6B7280", "#4B5563")

    # Define typography hierarchy directly inside the Enum using enum.nonmember
    fonts = nonmember(FontStyles("Montserrat"))


# --- SETUP CONFIGURATION ---
# Select active theme here: FusionTheme or Futuristic
Theme = FusionTheme
