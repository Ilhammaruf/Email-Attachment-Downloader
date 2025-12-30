"""File renaming utility module with customizable rules and templates."""

import re
import os
from dataclasses import dataclass


# Predefined rename templates
RENAME_TEMPLATES = {
    "original": {
        "name": "Keep Original",
        "description": "Keep the original filename",
        "pattern": "{filename}"
    },
    "date_filename": {
        "name": "Date + Filename",
        "description": "2024-01-15_invoice.pdf",
        "pattern": "{date}_{filename}"
    },
    "sender_date_filename": {
        "name": "Sender + Date + Filename",
        "description": "john_2024-01-15_invoice.pdf",
        "pattern": "{sender}_{date}_{filename}"
    },
    "sender_filename": {
        "name": "Sender + Filename",
        "description": "john_invoice.pdf",
        "pattern": "{sender}_{filename}"
    },
    "subject_filename": {
        "name": "Subject + Filename",
        "description": "Monthly_Report_data.xlsx",
        "pattern": "{subject}_{filename}"
    },
    "date_sender_subject": {
        "name": "Date + Sender + Subject",
        "description": "2024-01-15_john_Monthly_Report.pdf",
        "pattern": "{date}_{sender}_{subject}_{filename}"
    }
}


@dataclass
class RenameRule:
    """A rename rule using a template pattern."""
    template: str
    replace_spaces: bool = True
    lowercase: bool = False
    space_replacement: str = "_"


class FileRenamer:
    """Applies rename rules to filenames using templates."""

    def __init__(self, template: str = "{filename}"):
        """
        Initialize renamer with a template.

        Args:
            template: Pattern like "{date}_{sender}_{filename}"
                     Available placeholders: {date}, {sender}, {subject}, {filename}
        """
        self.template = template
        self.replace_spaces = True
        self.lowercase = False
        self.space_replacement = "_"
        self._counter = 0

    def set_options(
        self,
        replace_spaces: bool = True,
        lowercase: bool = False,
        space_replacement: str = "_"
    ):
        """Set additional renaming options."""
        self.replace_spaces = replace_spaces
        self.lowercase = lowercase
        self.space_replacement = space_replacement

    def _extract_sender_name(self, sender: str) -> str:
        """Extract name or email from sender string."""
        if not sender:
            return "unknown"

        # Format: "Name <email@example.com>" or just "email@example.com"
        match = re.match(r'^"?([^"<]+)"?\s*<', sender)
        if match:
            return match.group(1).strip()

        # Just email address - get part before @
        match = re.match(r'^([^@]+)@', sender)
        if match:
            return match.group(1).strip()

        return sender[:20] if sender else "unknown"

    def _sanitize_component(self, text: str, max_length: int = 30) -> str:
        """Sanitize text for use in filename."""
        if not text:
            return ""

        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)

        # Handle spaces
        if self.replace_spaces:
            text = re.sub(r'\s+', self.space_replacement, text)

        # Remove multiple underscores/dashes
        text = re.sub(r'[_-]+', '_', text)

        # Lowercase if requested
        if self.lowercase:
            text = text.lower()

        # Truncate and clean edges
        return text[:max_length].strip('_.- ')

    def apply_rules(
        self,
        filename: str,
        sender: str = "",
        subject: str = "",
        date: str = ""
    ) -> str:
        """
        Apply template to generate new filename.

        Args:
            filename: Original filename
            sender: Email sender
            subject: Email subject
            date: Email date (YYYY-MM-DD format)

        Returns:
            New filename
        """
        name, ext = os.path.splitext(filename)

        # Prepare components
        sender_clean = self._sanitize_component(self._extract_sender_name(sender), 20)
        subject_clean = self._sanitize_component(subject, 30)
        name_clean = self._sanitize_component(name, 50)

        # Increment counter for {counter} placeholder
        self._counter += 1

        # Apply template
        result = self.template.format(
            date=date or "nodate",
            sender=sender_clean or "unknown",
            subject=subject_clean or "nosubject",
            filename=name_clean,
            counter=self._counter
        )

        # Final cleanup
        result = re.sub(r'[_-]+', '_', result)
        result = result.strip('_.- ')

        # Handle lowercase for final result
        if self.lowercase:
            result = result.lower()
            ext = ext.lower()

        return result + ext

    def reset_counter(self):
        """Reset the counter for {counter} placeholder."""
        self._counter = 0


def create_renamer_from_template(template_key: str) -> FileRenamer:
    """
    Create a renamer from a predefined template.

    Args:
        template_key: Key from RENAME_TEMPLATES dict

    Returns:
        Configured FileRenamer
    """
    if template_key in RENAME_TEMPLATES:
        pattern = RENAME_TEMPLATES[template_key]["pattern"]
    else:
        pattern = "{filename}"

    return FileRenamer(template=pattern)


def get_template_names() -> list[tuple[str, str]]:
    """
    Get list of template names for dropdown.

    Returns:
        List of (key, display_name) tuples
    """
    return [(key, info["name"]) for key, info in RENAME_TEMPLATES.items()]
