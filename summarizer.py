"""Condense long Claude responses for speech output."""

import re
from config import MAX_SPEECH_CHARS


def strip_markdown(text: str) -> str:
    """Remove markdown formatting for cleaner speech."""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "[code block omitted]", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove headers (keep the text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", text)
    # Remove links, keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Remove bullet points
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Remove numbered lists prefix
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def condense(text: str, max_chars: int = MAX_SPEECH_CHARS) -> str:
    """Condense text for speech. Strips markdown and truncates if needed."""
    text = strip_markdown(text)

    if len(text) <= max_chars:
        return text

    # Try to break at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")
    last_newline = truncated.rfind("\n")
    break_point = max(last_period, last_newline)

    if break_point > max_chars * 0.5:
        return truncated[:break_point + 1].strip()

    return truncated.strip() + "... That's the summary. Ask me to elaborate if needed."


def summarize_for_speech(text: str) -> str:
    """Main entry point: prepare Claude's response for speech output."""
    if not text:
        return "Claude returned an empty response."

    # Check for common short responses that don't need processing
    if len(text) < 100 and not any(c in text for c in "`#*["):
        return text

    return condense(text)
