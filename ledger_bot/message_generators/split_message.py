"""Splits the message content into 2000 character chunks."""

import logging
import re
from typing import List

log = logging.getLogger(__name__)


def _split_text_on_newline(text: str, chunk_length: int) -> List[str]:
    chunks = []
    current_chunk = ""

    for line in text.splitlines(True):
        if len(current_chunk) + len(line) <= chunk_length:
            current_chunk += line
        else:
            chunks.append(current_chunk)
            current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def split_message(content: List) -> List[str]:
    """
    Splits the message content into 2000 character chunks.

    Discord can't accept messages more than 2000 characters, so we have to return long lists as multiple messages.

    Parameters
    ----------
    content : List
        A list containing the content to be sent. Initial split will be based on list items.

    Returns
    -------
    List[str]
        A list of messages to send
    """
    total_length = (
        sum(len(s) + 1 for s in content) - 1
    )  # We add a line break between each section hence the +1 / -1
    log.debug(f"Total length: {total_length}")

    if total_length > 1995:
        log.info(f"Splitting large message ({total_length} characters)")

        output = []

        for section in content:
            if len(section) < 1995:
                if len(section) != 0:
                    output.append(section)
            else:
                # Further split section

                # Remove first line
                parts = section.split("\n", 1)
                if len(parts) == 2:
                    section_title = parts[0]
                    section_content = parts[1]
                else:
                    section_title = parts[0]
                    section_content = ""

                log.debug(f"section_title:\n{section_title}")
                log.debug(f"section_content:\n{section_content}")

                # Split on section titles, where titles are either:
                # `Text:``
                # `**Text**`
                sub_sections = re.split(
                    r"(?<![^\n])\n(?=[A-Za-z ]+:|\*\*[A-Za-z ]+\*\*)", section_content
                )

                for i, sub_section in enumerate(sub_sections):

                    log.debug(f"i: {i}")
                    log.debug(f"new line count: {sub_section.count("\n")}")

                    log.debug(f"{i}:\n{sub_section}")
                    if i == 0:
                        sub_section = section_title + "\n" + sub_section

                    if len(sub_section) < 1995:
                        output.append(sub_section)
                    else:
                        # Further split section
                        split_sub_section = _split_text_on_newline(sub_section, 1995)
                        output = output + split_sub_section

    else:
        output = ["\n".join(content)]

    return output
