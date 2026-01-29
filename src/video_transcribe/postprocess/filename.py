"""Filename utilities for AI-suggested filenames."""

import re
import time
from pathlib import Path
from typing import Final

# Characters invalid in filenames (Windows + Linux + macOS)
INVALID_CHARS: Final = set('<>:"/\\|?*')
# Control characters (0-31)
CONTROL_CHARS: Final = set(chr(i) for i in range(32))
# Reserved Windows filenames
RESERVED_NAMES: Final = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}
MAX_FILENAME_LENGTH: Final = 255  # Common filesystem limit


def extract_filename_from_response(response: str) -> str | None:
    """Extract filename from HTML comment in LLM response.

    Expected format: <!-- FILENAME: Инструкция по удалению тикета.md -->

    Args:
        response: Raw LLM response text.

    Returns:
        Extracted filename without path, or None if not found.

    Examples:
        >>> extract_filename_from_response("...\\n<!-- FILENAME: Meeting notes.md -->\\n...")
        'Meeting notes.md'
        >>> extract_filename_from_response("No filename here")
        None
    """
    pattern = r'<!--\s*FILENAME:\s*([^\n]+?)\s*-->'
    match = re.search(pattern, response, re.IGNORECASE)
    if match:
        filename = match.group(1).strip()
        # Remove any path components (keep only basename)
        return Path(filename).name
    return None


def strip_filename_marker(response: str) -> str:
    """Remove the FILENAME HTML comment from LLM response.

    Args:
        response: Raw LLM response text.

    Returns:
        Response with FILENAME comment removed.

    Examples:
        >>> strip_filename_marker("Content...\\n\\n<!-- FILENAME: test.md -->")
        'Content...'
    """
    pattern = r'\n?<!--\s*FILENAME:.+?-->\s*$'
    return re.sub(pattern, '', response, flags=re.IGNORECASE).strip()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters.

    Preserves Cyrillic and other Unicode characters.

    Args:
        filename: Raw filename string.

    Returns:
        Sanitized filename safe for all platforms.

    Examples:
        >>> sanitize_filename("Инструкция: Что делать?.md")
        'Инструкция_Что делать.md'
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
    """
    # Remove control characters
    filename = ''.join(c for c in filename if c not in CONTROL_CHARS)

    # Replace invalid chars with underscore
    filename = ''.join(c if c not in INVALID_CHARS else '_' for c in filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Prevent path traversal - keep only basename
    filename = str(Path(filename).name)

    # Check for reserved names (case-insensitive)
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in RESERVED_NAMES:
        filename = f"_{filename}"

    # Limit length (reserve space for extension and collision suffix)
    max_len = MAX_FILENAME_LENGTH - 20  # Reserve for .md and _999 suffix
    if len(filename) > max_len:
        # Truncate from start, preserve extension
        stem = Path(filename).stem
        ext = Path(filename).suffix
        stem = stem[:max_len - len(ext)]
        filename = stem + ext

    # Ensure .md extension
    if not Path(filename).suffix:
        filename = f"{filename}.md"

    return filename


def validate_filename(filename: str) -> bool:
    """Validate that filename is safe to use.

    Args:
        filename: Filename to validate.

    Returns:
        True if filename is safe, False otherwise.
    """
    if not filename:
        return False

    # Check for empty after sanitization
    sanitized = sanitize_filename(filename)
    if not sanitized or sanitized == '.' or sanitized == '..':
        return False

    # Must have reasonable extension
    if not Path(sanitized).suffix:
        return False

    return True


def resolve_collision(output_dir: Path, filename: str) -> Path:
    """Resolve filename collision by adding numeric suffix.

    Args:
        output_dir: Directory where file will be saved.
        filename: Desired filename.

    Returns:
        Path with collision resolved (may add _1, _2, etc.).

    Examples:
        >>> resolve_collision(Path("/tmp"), "test.md")
        Path('/tmp/test.md')
        >>> # If test.md exists:
        >>> resolve_collision(Path("/tmp"), "test.md")
        Path('/tmp/test_1.md')
    """
    output_path = output_dir / filename

    if not output_path.exists():
        return output_path

    stem = Path(filename).stem
    ext = Path(filename).suffix

    counter = 1
    while counter < 1000:  # Prevent infinite loop
        new_filename = f"{stem}_{counter}{ext}"
        new_path = output_dir / new_filename
        if not new_path.exists():
            return new_path
        counter += 1

    # Fallback: use timestamp
    timestamp = int(time.time())
    new_filename = f"{stem}_{timestamp}{ext}"
    return output_dir / new_filename


def generate_safe_filename(
    suggested: str | None,
    output_dir: Path,
    default_prefix: str = "transcript",
) -> Path:
    """Generate a safe filename from AI suggestion or default.

    Args:
        suggested: AI-suggested filename (may be None or invalid).
        output_dir: Directory where file will be saved.
        default_prefix: Prefix for default filename.

    Returns:
        Safe, collision-resolved Path object.

    Examples:
        >>> generate_safe_filename("Meeting.md", Path("/tmp"))
        Path('/tmp/Meeting.md')
        >>> generate_safe_filename(None, Path("/tmp"))
        Path('/tmp/transcript.md')
        >>> generate_safe_filename("../../etc/passwd", Path("/tmp"))
        Path('/tmp/passwd.md')
    """
    filename = None

    if suggested and validate_filename(suggested):
        filename = sanitize_filename(suggested)

    # Fallback to default
    if not filename:
        filename = f"{default_prefix}.md"

    return resolve_collision(output_dir, filename)
