"""Preview window for displaying search results with selectable emails."""

import customtkinter as ctk
from typing import Callable

from .email_client import EmailMessage


class EmailRow(ctk.CTkFrame):
    """Single email row with checkbox and details."""

    def __init__(
        self,
        parent,
        email: EmailMessage,
        on_toggle: Callable[["EmailRow", bool], None] | None = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.email = email
        self.on_toggle = on_toggle
        self.selected = ctk.BooleanVar(value=True)

        self._create_widgets()

    def _create_widgets(self):
        """Create row widgets."""
        self.configure(fg_color="transparent")

        # Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.selected,
            command=self._on_check_changed,
            width=24
        )
        self.checkbox.pack(side="left", padx=(5, 10))

        # Email details frame
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.pack(side="left", fill="x", expand=True)

        # Sender
        sender_text = self.email.sender[:40] + "..." if len(self.email.sender) > 40 else self.email.sender
        ctk.CTkLabel(
            details_frame,
            text=sender_text,
            font=("", 12, "bold"),
            anchor="w"
        ).pack(anchor="w")

        # Subject
        subject_text = self.email.subject[:60] + "..." if len(self.email.subject) > 60 else self.email.subject
        ctk.CTkLabel(
            details_frame,
            text=subject_text,
            font=("", 11),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w")

        # Date and attachments
        date_str = self.email.date.strftime("%Y-%m-%d %H:%M")
        att_text = f"{self.email.attachment_count} attachment(s)"
        info_text = f"{date_str}  |  {att_text}"

        ctk.CTkLabel(
            details_frame,
            text=info_text,
            font=("", 10),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w")

        # Attachment names (if any)
        if self.email.attachment_names:
            names = ", ".join(self.email.attachment_names[:3])
            if len(self.email.attachment_names) > 3:
                names += f" (+{len(self.email.attachment_names) - 3} more)"

            ctk.CTkLabel(
                details_frame,
                text=f"Files: {names}",
                font=("", 10),
                text_color="#888888",
                anchor="w"
            ).pack(anchor="w", pady=(2, 0))

    def _on_check_changed(self):
        """Handle checkbox change."""
        if self.on_toggle:
            self.on_toggle(self, self.selected.get())

    def is_selected(self) -> bool:
        """Check if row is selected."""
        return self.selected.get()

    def set_selected(self, selected: bool):
        """Set selection state."""
        self.selected.set(selected)


class PreviewWindow(ctk.CTkToplevel):
    """Window showing search results with email selection."""

    def __init__(
        self,
        parent,
        emails: list[EmailMessage],
        on_download: Callable[[list[EmailMessage]], None] | None = None
    ):
        super().__init__(parent)

        self.emails = emails
        self.on_download = on_download
        self.email_rows: list[EmailRow] = []

        self.title("Preview Results")
        self.geometry("700x600")
        self.minsize(500, 400)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._populate_emails()
        self._update_summary()

    def _create_widgets(self):
        """Create window widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header with summary
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        self.summary_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=("", 14, "bold")
        )
        self.summary_label.pack(side="left", padx=10, pady=10)

        self.size_label = ctk.CTkLabel(
            header_frame,
            text="",
            text_color="gray"
        )
        self.size_label.pack(side="right", padx=10, pady=10)

        # Select all / none buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Select All",
            command=self._select_all,
            width=100
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="Select None",
            command=self._select_none,
            width=100
        ).pack(side="left")

        # Scrollable email list
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            bottom_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
            fg_color="gray"
        ).pack(side="right", padx=(5, 0))

        self.download_btn = ctk.CTkButton(
            bottom_frame,
            text="Download Selected",
            command=self._on_download_click,
            width=150
        )
        self.download_btn.pack(side="right")

    def _populate_emails(self):
        """Add email rows to the list."""
        for email in self.emails:
            row = EmailRow(
                self.scroll_frame,
                email,
                on_toggle=self._on_row_toggle
            )
            row.pack(fill="x", pady=2)

            # Add separator
            sep = ctk.CTkFrame(self.scroll_frame, height=1, fg_color="gray30")
            sep.pack(fill="x", pady=2)

            self.email_rows.append(row)

    def _on_row_toggle(self, row: EmailRow, selected: bool):
        """Handle row selection change."""
        self._update_summary()

    def _update_summary(self):
        """Update summary labels."""
        selected = self.get_selected_emails()
        total_emails = len(self.emails)
        selected_count = len(selected)

        total_attachments = sum(e.attachment_count for e in selected)

        self.summary_label.configure(
            text=f"Selected: {selected_count}/{total_emails} emails, {total_attachments} attachments"
        )

        # Enable/disable download button
        self.download_btn.configure(
            state="normal" if selected_count > 0 else "disabled"
        )

    def _select_all(self):
        """Select all emails."""
        for row in self.email_rows:
            row.set_selected(True)
        self._update_summary()

    def _select_none(self):
        """Deselect all emails."""
        for row in self.email_rows:
            row.set_selected(False)
        self._update_summary()

    def get_selected_emails(self) -> list[EmailMessage]:
        """Get list of selected emails."""
        return [row.email for row in self.email_rows if row.is_selected()]

    def _on_download_click(self):
        """Handle download button click."""
        selected = self.get_selected_emails()
        if selected and self.on_download:
            self.destroy()
            self.on_download(selected)
