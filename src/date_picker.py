"""Date picker widget for CustomTkinter."""

import tkinter as tk
from datetime import datetime, date
from typing import Callable

import customtkinter as ctk
from tkcalendar import Calendar


class DatePickerButton(ctk.CTkFrame):
    """A button that opens a calendar popup for date selection."""

    def __init__(
        self,
        parent,
        placeholder: str = "Select date",
        date_format: str = "%Y-%m-%d",
        on_date_change: Callable[[date | None], None] | None = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.date_format = date_format
        self.on_date_change = on_date_change
        self.selected_date: date | None = None
        self.placeholder = placeholder
        self.popup: tk.Toplevel | None = None

        self._create_widgets()

    def _create_widgets(self):
        """Create the button and clear button."""
        # Date display/button
        self.date_btn = ctk.CTkButton(
            self,
            text=self.placeholder,
            command=self._show_calendar,
            width=130,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            text_color=("gray40", "gray60")
        )
        self.date_btn.pack(side="left")

        # Clear button
        self.clear_btn = ctk.CTkButton(
            self,
            text="x",
            command=self._clear_date,
            width=28,
            fg_color="transparent",
            hover_color=("gray75", "gray35"),
            text_color=("gray50", "gray50")
        )
        self.clear_btn.pack(side="left", padx=(2, 0))

    def _show_calendar(self):
        """Show calendar popup."""
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None
            return

        # Create popup window
        self.popup = tk.Toplevel(self)
        self.popup.title("")
        self.popup.overrideredirect(True)  # Remove window decorations

        # Position popup below the button
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 5
        self.popup.geometry(f"+{x}+{y}")

        # Create calendar
        if self.selected_date:
            cal = Calendar(
                self.popup,
                selectmode="day",
                year=self.selected_date.year,
                month=self.selected_date.month,
                day=self.selected_date.day,
                background="gray20",
                foreground="white",
                selectbackground="#1f6aa5",
                headersbackground="gray30",
                headersforeground="white",
                normalbackground="gray25",
                normalforeground="white",
                weekendbackground="gray30",
                weekendforeground="white",
                othermonthbackground="gray20",
                othermonthforeground="gray50",
                bordercolor="gray40"
            )
        else:
            today = date.today()
            cal = Calendar(
                self.popup,
                selectmode="day",
                year=today.year,
                month=today.month,
                day=today.day,
                background="gray20",
                foreground="white",
                selectbackground="#1f6aa5",
                headersbackground="gray30",
                headersforeground="white",
                normalbackground="gray25",
                normalforeground="white",
                weekendbackground="gray30",
                weekendforeground="white",
                othermonthbackground="gray20",
                othermonthforeground="gray50",
                bordercolor="gray40"
            )
        cal.pack(padx=5, pady=5)

        # Select button
        select_btn = ctk.CTkButton(
            self.popup,
            text="Select",
            command=lambda: self._on_date_selected(cal.selection_get()),
            width=100
        )
        select_btn.pack(pady=(0, 5))

        # Close popup when clicking outside
        self.popup.bind("<FocusOut>", self._on_popup_focus_out)
        self.popup.focus_set()

    def _on_popup_focus_out(self, event):
        """Handle popup losing focus."""
        # Small delay to allow button clicks to register
        if self.popup:
            self.popup.after(100, self._check_and_close_popup)

    def _check_and_close_popup(self):
        """Check if popup should be closed."""
        if self.popup and not self.popup.focus_get():
            self.popup.destroy()
            self.popup = None

    def _on_date_selected(self, selected: date):
        """Handle date selection from calendar."""
        self.selected_date = selected
        self._update_display()

        if self.popup:
            self.popup.destroy()
            self.popup = None

        if self.on_date_change:
            self.on_date_change(self.selected_date)

    def _clear_date(self):
        """Clear the selected date."""
        self.selected_date = None
        self._update_display()

        if self.on_date_change:
            self.on_date_change(None)

    def _update_display(self):
        """Update the button text."""
        if self.selected_date:
            text = self.selected_date.strftime(self.date_format)
            self.date_btn.configure(
                text=text,
                text_color=("gray10", "gray90")
            )
        else:
            self.date_btn.configure(
                text=self.placeholder,
                text_color=("gray40", "gray60")
            )

    def get_date(self) -> date | None:
        """Get the selected date."""
        return self.selected_date

    def set_date(self, new_date: date | None):
        """Set the date programmatically."""
        self.selected_date = new_date
        self._update_display()

    def get_datetime(self) -> datetime | None:
        """Get selected date as datetime."""
        if self.selected_date:
            return datetime.combine(self.selected_date, datetime.min.time())
        return None
