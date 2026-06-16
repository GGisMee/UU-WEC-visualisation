import customtkinter as ctk
from typing import Callable, Any
from wec_visualisation.gui.theme import Theme

class LabeledSlider(ctk.CTkFrame):
    """
    A reusable composite widget that contains a label displaying the current value
    and a slider to modify it.
    """
    def __init__(self, parent, label_template: str, variable: ctk.DoubleVar, 
                 from_:int, to:int, number_of_steps: int, command: Callable, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.label_template = label_template
        self.variable = variable
        self.command = command
        
        # Label to display value
        self.label = ctk.CTkLabel(
            self, 
            text=self.label_template.format(value=self.variable.get()), 
            font=Theme.fonts.BODY_BOLD, 
            text_color=Theme.TEXT_MAIN.value
        )
        self.label.pack(anchor="w", padx=0, pady=(4, 0))
        
        # Slider
        self.slider = ctk.CTkSlider(
            self, 
            from_=from_, 
            to=to, 
            number_of_steps=number_of_steps, 
            variable=self.variable, 
            command=self._on_change,
            progress_color=Theme.SLIDER_PROGRESS.value,
            button_color=Theme.SLIDER_BUTTON.value,
            button_hover_color=Theme.SLIDER_BUTTON_HOVER.value,
            fg_color=Theme.SLIDER_BG.value
        )
        self.slider.pack(fill="x", padx=0, pady=(0, 8))
        
    def _on_change(self, val):
        self.label.configure(text=self.label_template.format(value=self.variable.get()))
        if self.command:
            self.command(val)
            
    def update_label(self):
        self.label.configure(text=self.label_template.format(value=self.variable.get()))

    def configure_slider(self, **kwargs):
        self.slider.configure(**kwargs)


class MetricRow(ctk.CTkFrame):
    """
    A reusable row for displaying key-value metrics with left-aligned keys 
    and right-aligned bold values.
    """
    def __init__(self, parent, label_text: str, initial_value: str, is_bold: bool = False, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        lbl_weight = Theme.fonts.BODY_BOLD if is_bold else Theme.fonts.BODY
        lbl_color = Theme.TEXT_MAIN.value if is_bold else Theme.TEXT_MUTED.value
        
        # We can pass an optional value_color via kwargs or let it default
        self.default_val_color = Theme.INFO.value if is_bold else Theme.TEXT_MAIN.value
        
        ctk.CTkLabel(self, text=label_text, font=lbl_weight, text_color=lbl_color).pack(side="left")
        self.val_lbl = ctk.CTkLabel(self, text=initial_value, font=Theme.fonts.BODY_BOLD, text_color=self.default_val_color)
        self.val_lbl.pack(side="right")
        
    def set_value(self, text: str, text_color: Any = None):
        if text_color:
            self.val_lbl.configure(text=text, text_color=text_color)
        else:
            self.val_lbl.configure(text=text, text_color=self.default_val_color)

class TextInfoBox(ctk.CTkFrame):
    """
    A reusable frame that contains a title and a responsive, read-only textbox
    for displaying multiline descriptions.
    """
    def __init__(self, parent, title_text: str, height: int = 70, **kwargs):
        super().__init__(
            parent,
            fg_color=Theme.BOX_BG.value,
            corner_radius=6,
            border_width=1,
            border_color=Theme.BORDER.value,
            **kwargs
        )
        
        # Title Label
        self.lbl_title = ctk.CTkLabel(
            self,
            text=title_text,
            font=Theme.fonts.HEADER,
            text_color=Theme.ACCENT.value
        )
        self.lbl_title.pack(anchor="w", padx=10, pady=(8, 2))
        
        # Textbox for responsive wrapping without scrollbars
        self.textbox = ctk.CTkTextbox(
            self,
            font=Theme.fonts.MUTED,
            text_color=Theme.TEXT_MUTED.value, # type: ignore
            fg_color="transparent",
            wrap="word",
            height=height,
            activate_scrollbars=False
        )
        self.textbox.pack(anchor="w", fill="both", expand=True, padx=10, pady=(0, 8))
        self.textbox.configure(state="disabled")

    def set_text(self, text: str):
        """Update the text safely by temporarily enabling the textbox."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", text)
        self.textbox.configure(state="disabled")
