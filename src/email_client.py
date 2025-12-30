"""Email client module for IMAP connection and email filtering."""

import imaplib
import email
from email.header import decode_header
from email.message import Message
from datetime import datetime
from typing import Callable, Any
from dataclasses import dataclass
from enum import Enum


class EmailProvider(Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"


# Provider IMAP configurations
PROVIDER_CONFIG = {
    EmailProvider.GMAIL: {
        "name": "Gmail",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "help_text": (
            "Use an App Password (not your regular password):\n"
            "1. Enable 2-Step Verification in Google Account\n"
            "2. Go to myaccount.google.com/apppasswords\n"
            "3. Generate a password for 'Mail'\n"
            "4. Use the 16-character password here"
        )
    },
    EmailProvider.OUTLOOK: {
        "name": "Outlook / Hotmail",
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "help_text": (
            "For Outlook.com / Hotmail / Live:\n"
            "1. Use your regular password, OR\n"
            "2. If 2FA enabled, create an App Password at:\n"
            "   account.microsoft.com/security\n"
            "Note: IMAP must be enabled in Outlook settings"
        )
    }
}


class EmailClientError(Exception):
    """Base exception for email client errors."""
    pass


class AuthenticationError(EmailClientError):
    """Raised when authentication fails."""
    pass


class ConnectionError(EmailClientError):
    """Raised when connection fails."""
    pass


@dataclass
class EmailMessage:
    """Represents an email message with metadata."""
    uid: str
    subject: str
    sender: str
    date: datetime
    attachment_count: int
    attachment_names: list[str]
    raw_message: Any


class EmailClient:
    """Multi-provider IMAP client for fetching and filtering emails.

    Supports context manager for automatic connection cleanup.

    Example:
        with EmailClient(EmailProvider.GMAIL) as client:
            client.connect('user@gmail.com', 'app_password')
            emails = client.search_emails(
                sender='invoices@company.com',
                date_from=datetime(2024, 1, 1)
            )
    """

    def __init__(self, provider: EmailProvider = EmailProvider.GMAIL):
        """
        Initialize email client for a specific provider.

        Args:
            provider: Email provider (GMAIL, OUTLOOK)
        """
        self.provider = provider
        self.config = PROVIDER_CONFIG[provider]
        self.email_address: str | None = None
        self.connection: imaplib.IMAP4_SSL | None = None
        self.logged_in = False

    def __enter__(self) -> "EmailClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - disconnects from IMAP."""
        self.disconnect()

    @property
    def server(self) -> str:
        """Get IMAP server address."""
        return self.config["imap_server"]

    @property
    def port(self) -> int:
        """Get IMAP port."""
        return self.config["imap_port"]

    @property
    def provider_name(self) -> str:
        """Get provider display name."""
        return self.config["name"]

    @property
    def help_text(self) -> str:
        """Get provider-specific help text."""
        return self.config["help_text"]

    def connect(self, email_address: str, password: str) -> None:
        """
        Connect to email server via IMAP.

        Args:
            email_address: Email address
            password: Password or App Password

        Raises:
            ConnectionError: If unable to connect to server
            AuthenticationError: If login fails
        """
        self.email_address = email_address

        # Connect to IMAP server
        try:
            self.connection = imaplib.IMAP4_SSL(self.server, self.port)
        except OSError as e:
            raise ConnectionError(
                f"Cannot connect to {self.provider_name}.\n"
                f"Check your internet connection.\n\n"
                f"Server: {self.server}:{self.port}\n"
                f"Error: {str(e)}"
            )
        except Exception as e:
            raise ConnectionError(f"Connection failed: {str(e)}")

        # Authenticate
        try:
            self.connection.login(email_address, password)
            self.logged_in = True
        except imaplib.IMAP4.error as e:
            error_msg = str(e)

            # Provider-specific error handling
            if self.provider == EmailProvider.GMAIL:
                if "AUTHENTICATIONFAILED" in error_msg or "Invalid credentials" in error_msg:
                    raise AuthenticationError(
                        "Gmail authentication failed.\n\n"
                        f"{self.help_text}"
                    )
                elif "Application-specific password required" in error_msg:
                    raise AuthenticationError(
                        "Gmail requires an App Password.\n\n"
                        f"{self.help_text}"
                    )
            elif self.provider == EmailProvider.OUTLOOK:
                if "AUTHENTICATE" in error_msg or "LOGIN" in error_msg:
                    raise AuthenticationError(
                        "Outlook authentication failed.\n\n"
                        f"{self.help_text}"
                    )

            raise AuthenticationError(
                f"Login failed for {self.provider_name}.\n\n"
                f"Error: {error_msg}\n\n"
                f"{self.help_text}"
            )

    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self.connection and self.logged_in:
            try:
                self.connection.logout()
            except Exception:
                pass
            self.logged_in = False
            self.connection = None

    def _build_search_criteria(
        self,
        sender: str | None = None,
        subject: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None
    ) -> str:
        """Build IMAP search criteria string."""
        criteria = []

        if sender:
            criteria.append(f'FROM "{sender}"')

        if subject:
            criteria.append(f'SUBJECT "{subject}"')

        if date_from:
            date_str = date_from.strftime("%d-%b-%Y")
            criteria.append(f'SINCE {date_str}')

        if date_to:
            date_str = date_to.strftime("%d-%b-%Y")
            criteria.append(f'BEFORE {date_str}')

        return " ".join(criteria) if criteria else "ALL"

    def _decode_header_value(self, value: str | None) -> str:
        """Decode email header value."""
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def _parse_date(self, date_str: str | None) -> datetime:
        """Parse email date string to datetime."""
        if not date_str:
            return datetime.now()

        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()

    def _count_attachments(self, msg: Message) -> tuple[int, list[str]]:
        """Count attachments and return their names."""
        count = 0
        names = []

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition")
            if content_disposition and "attachment" in content_disposition.lower():
                filename = part.get_filename()
                if filename:
                    if isinstance(filename, bytes):
                        filename = filename.decode("utf-8", errors="replace")
                    names.append(filename)
                    count += 1

        return count, names

    def search_emails(
        self,
        sender: str | None = None,
        subject: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        folder: str = "INBOX",
        progress_callback: Callable[[int, int], None] | None = None
    ) -> list[EmailMessage]:
        """
        Search emails matching the given criteria.

        Args:
            sender: Filter by sender email address
            subject: Filter by subject (partial match)
            date_from: Filter emails from this date
            date_to: Filter emails until this date
            folder: IMAP folder to search (default: INBOX)
            progress_callback: Callback function(current, total) for progress updates

        Returns:
            List of EmailMessage objects matching criteria

        Raises:
            ConnectionError: If not connected to server
        """
        if not self.connection or not self.logged_in:
            raise ConnectionError("Not connected to IMAP server. Call connect() first.")

        try:
            self.connection.select(folder)
        except imaplib.IMAP4.error as e:
            raise EmailClientError(f"Cannot access folder '{folder}': {str(e)}")

        criteria = self._build_search_criteria(sender, subject, date_from, date_to)

        try:
            _, message_numbers = self.connection.search(None, criteria)
        except imaplib.IMAP4.error as e:
            raise EmailClientError(f"Search failed: {str(e)}")

        if not message_numbers[0]:
            return []

        uids = message_numbers[0].split()
        total = len(uids)
        emails = []

        for i, uid in enumerate(uids):
            try:
                _, msg_data = self.connection.fetch(uid, "(RFC822)")

                if msg_data[0] is None:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                attachment_count, attachment_names = self._count_attachments(msg)

                email_obj = EmailMessage(
                    uid=uid.decode(),
                    subject=self._decode_header_value(msg.get("Subject")),
                    sender=self._decode_header_value(msg.get("From")),
                    date=self._parse_date(msg.get("Date")),
                    attachment_count=attachment_count,
                    attachment_names=attachment_names,
                    raw_message=msg
                )
                emails.append(email_obj)

            except Exception:
                # Skip problematic emails but continue
                continue

            if progress_callback:
                progress_callback(i + 1, total)

        return emails

    def get_folders(self) -> list[str]:
        """Get list of available IMAP folders."""
        if not self.connection or not self.logged_in:
            raise ConnectionError("Not connected to IMAP server")

        _, folders = self.connection.list()
        folder_names = []

        for folder in folders:
            if folder:
                # Parse folder name from response
                decoded = folder.decode()
                # Handle different delimiter formats
                if ' "/" ' in decoded:
                    parts = decoded.split(' "/" ')
                elif ' "." ' in decoded:
                    parts = decoded.split(' "." ')
                else:
                    parts = [decoded]

                if len(parts) >= 2:
                    folder_names.append(parts[-1].strip('"'))

        return folder_names


# Backwards compatibility alias
GmailClient = EmailClient


def get_provider_names() -> list[tuple[str, str]]:
    """Get list of provider names for dropdown.

    Returns:
        List of (key, display_name) tuples
    """
    return [(p.value, PROVIDER_CONFIG[p]["name"]) for p in EmailProvider]


def get_provider_by_name(name: str) -> EmailProvider:
    """Get provider enum by display name."""
    for provider, config in PROVIDER_CONFIG.items():
        if config["name"] == name:
            return provider
    return EmailProvider.GMAIL
