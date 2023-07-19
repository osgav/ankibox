#!/usr/bin/env python
#
# ankibox script 2.0
#
# ankinote chunks
#
# osgav 2023
#


# CHUNK
#
ankinote_chunk_header = """
TARGET DECK: {ankibox_name}

---
"""


# CHUNK
#
ankinote_chunk_first_line = """
filepath: {filepath}

{anki_card_front} {anki_card_tag}
{anki_card_back}


---
"""


# CHUNK
#
ankinote_chunk_first_line_with_id = """
filepath: {filepath}

{anki_card_front} {anki_card_tag}
{anki_card_back}
{obsidian_to_anki_id}


---
"""


# CHUNK
#
ankinote_chunk_first_line_delete = """
filepath: {filepath}

{anki_card_front} {anki_card_tag}
{anki_card_back}
DELETE
{obsidian_to_anki_id}


---
"""
