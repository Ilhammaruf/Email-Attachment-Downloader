"""Attachment downloader module for extracting and saving email attachments."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable
from dataclasses import dataclass

from .email_client import EmailMessage
from .renamer import FileRenamer


# Common file type extensions
FILE_TYPE_EXTENSIONS = {
    "pdf": [".pdf"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"],
    "documents": [".doc", ".docx", ".odt", ".rtf", ".txt"],
    "spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
    "presentations": [".ppt", ".pptx", ".odp"],
    "archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "all": []  # Empty means all types
}


@dataclass
class Attachment:
    """Represents an email attachment."""
    filename: str
    content_type: str
    size: int
    data: bytes
    email_subject: str
    email_sender: str
    email_date: str
    email_uid: str


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    original_filename: str
    saved_filename: str
    filepath: str
    size: int = 0
    error: str | None = None


class AttachmentExtractor:
    """Extracts attachments from email messages."""

    def __init__(self, allowed_extensions: list[str] | None = None):
        """
        Initialize extractor with optional file type filter.

        Args:
            allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.png'])
                              None means allow all types
        """
        self.allowed_extensions = allowed_extensions

    def _is_allowed_type(self, filename: str) -> bool:
        """Check if file type is allowed."""
        if not self.allowed_extensions:
            return True

        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_extensions

    def extract(self, email_msg: EmailMessage) -> list[Attachment]:
        """
        Extract all attachments from an email message.

        Args:
            email_msg: EmailMessage object to extract from

        Returns:
            List of Attachment objects
        """
        attachments = []
        msg = email_msg.raw_message

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition")

            if content_disposition is None:
                continue

            if "attachment" not in content_disposition.lower():
                continue

            filename = part.get_filename()
            if not filename:
                continue

            # Decode filename if needed
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="replace")

            # Check file type filter
            if not self._is_allowed_type(filename):
                continue

            data = part.get_payload(decode=True)
            if data is None:
                continue

            attachment = Attachment(
                filename=filename,
                content_type=part.get_content_type(),
                size=len(data),
                data=data,
                email_subject=email_msg.subject,
                email_sender=email_msg.sender,
                email_date=email_msg.date.strftime("%Y-%m-%d"),
                email_uid=email_msg.uid
            )
            attachments.append(attachment)

        return attachments


class DownloadManager:
    """Manages downloading and saving of attachments."""

    def __init__(
        self,
        download_dir: str,
        renamer: FileRenamer | None = None,
        max_workers: int = 4
    ):
        """
        Initialize download manager.

        Args:
            download_dir: Directory to save attachments
            renamer: Optional FileRenamer for auto-renaming files
            max_workers: Max threads for parallel downloads
        """
        self.download_dir = download_dir
        self.renamer = renamer
        self.max_workers = max_workers
        os.makedirs(download_dir, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Remove or replace invalid characters from filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename.strip()

    def _get_unique_filepath(self, filepath: str) -> str:
        """Get a unique filepath by adding a number suffix if file exists."""
        if not os.path.exists(filepath):
            return filepath

        base, ext = os.path.splitext(filepath)
        counter = 1

        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1

        return f"{base}_{counter}{ext}"

    def save_attachment(self, attachment: Attachment) -> DownloadResult:
        """
        Save a single attachment to disk.

        Args:
            attachment: The attachment to save

        Returns:
            DownloadResult with save status
        """
        try:
            filename = attachment.filename

            # Apply rename rules if renamer is configured
            if self.renamer:
                filename = self.renamer.apply_rules(
                    filename=filename,
                    sender=attachment.email_sender,
                    subject=attachment.email_subject,
                    date=attachment.email_date
                )

            # Sanitize filename
            filename = self._sanitize_filename(filename)

            filepath = os.path.join(self.download_dir, filename)
            filepath = self._get_unique_filepath(filepath)

            with open(filepath, "wb") as f:
                f.write(attachment.data)

            return DownloadResult(
                success=True,
                original_filename=attachment.filename,
                saved_filename=os.path.basename(filepath),
                filepath=filepath,
                size=attachment.size
            )

        except Exception as e:
            return DownloadResult(
                success=False,
                original_filename=attachment.filename,
                saved_filename="",
                filepath="",
                error=str(e)
            )

    def download_batch(
        self,
        attachments: list[Attachment],
        progress_callback: Callable[[int, int, str], None] | None = None,
        use_threading: bool = True
    ) -> list[DownloadResult]:
        """
        Download multiple attachments.

        Args:
            attachments: List of attachments to download
            progress_callback: Callback(current, total, filename) for progress
            use_threading: Use multi-threading for faster downloads

        Returns:
            List of DownloadResult objects
        """
        total = len(attachments)
        results = []

        if not use_threading or total <= 1:
            # Sequential download
            for i, attachment in enumerate(attachments):
                if progress_callback:
                    progress_callback(i + 1, total, attachment.filename)
                result = self.save_attachment(attachment)
                results.append(result)
        else:
            # Parallel download with threading
            completed = 0
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_attachment = {
                    executor.submit(self.save_attachment, att): att
                    for att in attachments
                }

                for future in as_completed(future_to_attachment):
                    attachment = future_to_attachment[future]
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, total, attachment.filename)

                    result = future.result()
                    results.append(result)

        return results


class AttachmentDownloader:
    """High-level interface combining extraction and downloading."""

    def __init__(
        self,
        download_dir: str,
        renamer: FileRenamer | None = None,
        allowed_extensions: list[str] | None = None
    ):
        """
        Initialize the downloader.

        Args:
            download_dir: Directory to save attachments
            renamer: Optional FileRenamer for auto-renaming
            allowed_extensions: Filter by file extensions
        """
        self.extractor = AttachmentExtractor(allowed_extensions)
        self.manager = DownloadManager(download_dir, renamer)

    def extract_attachments(self, email_msg: EmailMessage) -> list[Attachment]:
        """Extract attachments from a single email."""
        return self.extractor.extract(email_msg)

    def download_from_emails(
        self,
        emails: list[EmailMessage],
        progress_callback: Callable[[int, int, str], None] | None = None,
        use_threading: bool = True
    ) -> list[DownloadResult]:
        """
        Download all attachments from a list of emails.

        Args:
            emails: List of EmailMessage objects
            progress_callback: Callback function(current, total, filename)
            use_threading: Use multi-threading for downloads

        Returns:
            List of DownloadResult objects
        """
        # Extract all attachments first
        all_attachments: list[Attachment] = []
        for email_msg in emails:
            attachments = self.extractor.extract(email_msg)
            all_attachments.extend(attachments)

        if not all_attachments:
            return []

        # Download all attachments
        return self.manager.download_batch(
            all_attachments,
            progress_callback,
            use_threading
        )

    def get_attachment_summary(
        self,
        emails: list[EmailMessage]
    ) -> tuple[int, int, int]:
        """
        Get summary of attachments without downloading.

        Returns:
            Tuple of (email_count, attachment_count, total_size_bytes)
        """
        email_count = len(emails)
        attachment_count = 0
        total_size = 0

        for email_msg in emails:
            attachments = self.extractor.extract(email_msg)
            for att in attachments:
                attachment_count += 1
                total_size += att.size

        return email_count, attachment_count, total_size


def get_extensions_for_types(type_names: list[str]) -> list[str] | None:
    """
    Get list of extensions for given file type names.

    Args:
        type_names: List of type names (e.g., ['pdf', 'images'])

    Returns:
        List of extensions or None for all types
    """
    if not type_names or "all" in type_names:
        return None

    extensions = []
    for name in type_names:
        if name in FILE_TYPE_EXTENSIONS:
            extensions.extend(FILE_TYPE_EXTENSIONS[name])

    return extensions if extensions else None
