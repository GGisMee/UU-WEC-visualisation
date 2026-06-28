import customtkinter as ctk
from typing import Callable, Any
from wec_visualisation.gui.theme import Theme

class LabeledSlider(ctk.CTkFrame):
    """
    A reusable composite widget that contains a label displaying the current value
    and a slider to modify it.
    """
    def __init__(self, parent, label_template: str, variable: ctk.DoubleVar, 
                 from_:int, to:int, number_of_steps: int, command: Callable, tooltip_text: str|None = None, **kwargs):
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
        self.label.pack(anchor="w", padx=0, pady=(2, 0))
        
        self.tooltip = None
        if tooltip_text:
            self.tooltip = ToolTip(self.label, tooltip_text, small=True)
        
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
        self.slider.pack(fill="x", padx=0, pady=(0, 2))
        
    def _on_change(self, val):
        self.label.configure(text=self.label_template.format(value=self.variable.get()))
        if self.command:
            self.command(val)
            
    def update_label(self):
        self.label.configure(text=self.label_template.format(value=self.variable.get()))

    def update_label_template(self, new_template):
        self.label_template = new_template
        self.update_label()

    def configure_slider(self, **kwargs):
        self.slider.configure(**kwargs)
        
    def update_tooltip(self, new_text: str):
        if self.tooltip:
            self.tooltip.update_text(new_text)


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

class DataTable(ctk.CTkFrame):
    """
    A reusable table component with styled headers, alternating row colors,
    and optional summary rows.
    """
    def __init__(self, parent, headers: list[str], header_tooltips: list[str | None] | None = None, **kwargs):
        super().__init__(
            parent,
            fg_color=Theme.BG_SURFACE.value,
            border_width=1,
            border_color=Theme.BORDER.value,
            corner_radius=4,
            **kwargs
        )
        self.headers = headers
        self.header_tooltips = header_tooltips
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.num_cols = len(headers)
        for col in range(self.num_cols):
            self.grid_frame.grid_columnconfigure(col, weight=1)
            
        self.draw_headers()
        self.row_count = 1  # 0 is headers
        
    def draw_headers(self):
        for col, text in enumerate(self.headers):
            lbl = ctk.CTkLabel(self.grid_frame, text=text, font=Theme.fonts.BODY_BOLD, text_color=Theme.TEXT_MAIN.value, fg_color=Theme.BOX_BG.value, corner_radius=0)
            lbl.grid(row=0, column=col, sticky="nsew", pady=(0, 1), ipadx=5, ipady=4)
            if self.header_tooltips and col < len(self.header_tooltips) and self.header_tooltips[col]:
                ToolTip(lbl, self.header_tooltips[col], small=True)

    def add_row(self, row_data: list, text_colors: list | None = None, is_summary: bool = False):
        bg_color = Theme.BOX_BG.value if is_summary else (Theme.BG_SURFACE.value if self.row_count % 2 != 0 else Theme.BG_INPUT.value)
        font = Theme.fonts.BODY_BOLD if is_summary else Theme.fonts.BODY
        
        pady = (1, 0) if is_summary else 0
        
        for col, text in enumerate(row_data):
            color = text_colors[col] if text_colors and col < len(text_colors) and text_colors[col] else Theme.TEXT_MAIN.value
            lbl = ctk.CTkLabel(self.grid_frame, text=str(text), font=font if col > 0 else Theme.fonts.BODY_BOLD, text_color=color, fg_color=bg_color, corner_radius=0)
            lbl.grid(row=self.row_count, column=col, sticky="nsew", pady=pady, ipadx=5, ipady=4 if is_summary else 2)
            
        self.row_count += 1
        
    def clear_rows(self):
        # Keep headers (row=0), destroy everything else
        for widget in self.grid_frame.winfo_children():
            info = widget.grid_info()
            if int(info.get("row", 0)) > 0:
                widget.destroy()
        self.row_count = 1



class ToolTip:
    """
    A hover-based tooltip overlay that appears after a delay.
    """
    def __init__(self, widget, text, delay=500, small=False):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.small = small
        self.tooltip_window = None
        self.id = None
        self.mouse_x = 0
        self.mouse_y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)
        self.widget.bind("<ButtonPress>", self.leave)

    def update_text(self, new_text: str):
        self.text = new_text

    def enter(self, event=None):
        if event:
            self.mouse_x = event.x_root
            self.mouse_y = event.y_root
        self.schedule()

    def motion(self, event):
        self.mouse_x = event.x_root
        self.mouse_y = event.y_root

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self):
        if self.tooltip_window:
            return
        
        # Offset slightly from the mouse to prevent flicker
        x = self.mouse_x + 20
        y = self.mouse_y + 20
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        cr = 4 if self.small else 8
        frame = ctk.CTkFrame(tw, fg_color=Theme.BOX_BG.value, corner_radius=cr, border_width=1, border_color=Theme.BORDER.value)
        frame.pack(fill="both", expand=True)
        
        fnt = Theme.fonts.MUTED if self.small else Theme.fonts.BODY
        px = 8 if self.small else 16
        py = 8 if self.small else 16
        wl = 200 if self.small else 350
        
        label = ctk.CTkLabel(
            frame, 
            text=self.text, 
            justify='left',
            text_color=Theme.TEXT_MAIN.value,
            font=fnt,
            wraplength=wl
        )
        label.pack(padx=px, pady=py)

    def hidetip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()
