#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lightweight Markdown parser for Python 2.5 / PowerPC Mac.
Converts Markdown text into a list of tagged segments for Tkinter Text widget.

Each segment is a tuple: (text, [tag1, tag2, ...])
"""

import re


class MarkdownParser(object):
    """Parses a subset of Markdown into tagged segments for display."""

    def __init__(self):
        # Inline patterns (order matters - bold before italic)
        self.inline_patterns = [
            # Bold + Italic
            (re.compile(r'\*\*\*(.+?)\*\*\*'), ['bold', 'italic']),
            (re.compile(r'___(.+?)___'), ['bold', 'italic']),
            # Bold
            (re.compile(r'\*\*(.+?)\*\*'), ['bold']),
            (re.compile(r'__(.+?)__'), ['bold']),
            # Italic
            (re.compile(r'\*(.+?)\*'), ['italic']),
            (re.compile(r'_(.+?)_'), ['italic']),
            # Inline code
            (re.compile(r'`(.+?)`'), ['code_inline']),
            # Strikethrough
            (re.compile(r'~~(.+?)~~'), ['strikethrough']),
        ]

    def parse(self, text):
        """Parse markdown text and return list of (text, tags) segments."""
        lines = text.split('\n')
        segments = []
        in_code_block = False
        code_block_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Fenced code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    code_text = '\n'.join(code_block_lines)
                    if code_text:
                        segments.append((code_text + '\n', ['code_block']))
                    code_block_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                i += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue

            # Blank line
            if line.strip() == '':
                segments.append(('\n', ['normal']))
                i += 1
                continue

            # Headings (ATX style)
            heading_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s*#*\s*)?$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text_content = heading_match.group(2)
                tag = 'h%d' % level
                segments.append((text_content + '\n', [tag]))
                i += 1
                continue

            # Setext-style headings
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == '=' for c in next_line) and len(next_line) >= 2:
                    segments.append((line + '\n', ['h1']))
                    i += 2
                    continue
                if next_line and all(c == '-' for c in next_line) and len(next_line) >= 2:
                    segments.append((line + '\n', ['h2']))
                    i += 2
                    continue

            # Horizontal rule
            if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', line.strip()):
                segments.append(('-' * 40 + '\n', ['hr']))
                i += 1
                continue

            # Unordered list items
            list_match = re.match(r'^(\s*)[*\-+]\s+(.+)$', line)
            if list_match:
                indent = len(list_match.group(1))
                bullet_level = indent // 2
                prefix = '  ' * bullet_level + '* '
                content = list_match.group(2)
                segments.append((prefix, ['list_bullet']))
                self._parse_inline(content + '\n', segments, ['list_item'])
                i += 1
                continue

            # Ordered list items
            olist_match = re.match(r'^(\s*)(\d+)[.)]\s+(.+)$', line)
            if olist_match:
                indent = len(olist_match.group(1))
                number = olist_match.group(2)
                bullet_level = indent // 2
                prefix = '  ' * bullet_level + number + '. '
                content = olist_match.group(3)
                segments.append((prefix, ['list_bullet']))
                self._parse_inline(content + '\n', segments, ['list_item'])
                i += 1
                continue

            # Blockquote
            bq_match = re.match(r'^>\s?(.*)', line)
            if bq_match:
                content = bq_match.group(1)
                segments.append(('  | ', ['blockquote_bar']))
                self._parse_inline(content + '\n', segments, ['blockquote'])
                i += 1
                continue

            # Normal paragraph
            self._parse_inline(line + '\n', segments, ['normal'])
            i += 1

        # Handle unclosed code block
        if in_code_block and code_block_lines:
            code_text = '\n'.join(code_block_lines)
            segments.append((code_text + '\n', ['code_block']))

        return segments

    def _parse_inline(self, text, segments, base_tags):
        """Parse inline formatting within text."""
        while text:
            earliest_match = None
            earliest_start = len(text)
            earliest_pattern_tags = None

            for pattern, tags in self.inline_patterns:
                m = pattern.search(text)
                if m and m.start() < earliest_start:
                    earliest_match = m
                    earliest_start = m.start()
                    earliest_pattern_tags = tags

            if earliest_match is None:
                if text:
                    segments.append((text, list(base_tags)))
                break

            if earliest_start > 0:
                segments.append((text[:earliest_start], list(base_tags)))

            inner_text = earliest_match.group(1)
            combined_tags = list(base_tags) + list(earliest_pattern_tags)
            segments.append((inner_text, combined_tags))

            text = text[earliest_match.end():]


if __name__ == '__main__':
    test = """# Hello World

This is **bold** and *italic* and `code`.

## Lists

- Item one
- Item **two**
- Item three

> This is a blockquote

```
def hello():
    print "world"
```

Normal paragraph with ***bold italic*** text.
"""
    parser = MarkdownParser()
    result = parser.parse(test)
    for seg in result:
        print repr(seg)