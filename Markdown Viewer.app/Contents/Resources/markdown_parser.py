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
        # Italic patterns use negative lookbehind/lookahead for * to avoid
        # matching inside ** bold ** delimiters.
        self.inline_patterns = [
            # Bold + Italic
            (re.compile(r'\*\*\*(.+?)\*\*\*'), ['bold', 'italic']),
            (re.compile(r'___(.+?)___'), ['bold', 'italic']),
            # Bold
            (re.compile(r'\*\*(.+?)\*\*'), ['bold']),
            (re.compile(r'__(.+?)__'), ['bold']),
            # Italic — closing * must not be followed by * (avoid stealing from **)
            (re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)'), ['italic']),
            (re.compile(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)'), ['italic']),
            # Inline code
            (re.compile(r'`(.+?)`'), ['code_inline']),
            # Strikethrough
            (re.compile(r'~~(.+?)~~'), ['strikethrough']),
        ]

        # Link pattern: [text](url)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        # Image pattern: ![alt](path)
        self.image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

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
        """Parse inline formatting within text, with recursion for nesting."""
        while text:
            earliest_match = None
            earliest_start = len(text)
            earliest_pattern_tags = None
            earliest_type = 'format'  # 'format', 'link', or 'image'

            # Check images first (before links, since ![...] starts with !)
            img_m = self.image_pattern.search(text)
            if img_m and img_m.start() < earliest_start:
                earliest_match = img_m
                earliest_start = img_m.start()
                earliest_type = 'image'

            # Check links
            link_m = self.link_pattern.search(text)
            if link_m and link_m.start() < earliest_start:
                # Make sure this isn't part of an image (preceded by !)
                if link_m.start() == 0 or text[link_m.start() - 1] != '!':
                    earliest_match = link_m
                    earliest_start = link_m.start()
                    earliest_type = 'link'

            # Check inline formatting patterns
            for pattern, tags in self.inline_patterns:
                m = pattern.search(text)
                if m and m.start() < earliest_start:
                    earliest_match = m
                    earliest_start = m.start()
                    earliest_pattern_tags = tags
                    earliest_type = 'format'

            if earliest_match is None:
                if text:
                    segments.append((text, list(base_tags)))
                break

            # Text before the match
            if earliest_start > 0:
                segments.append((text[:earliest_start], list(base_tags)))

            if earliest_type == 'image':
                alt_text = earliest_match.group(1) or 'image'
                img_path = earliest_match.group(2)
                segments.append(('[', list(base_tags)))
                segments.append(('img', list(base_tags) + ['image_icon']))
                segments.append((': ', list(base_tags)))
                if alt_text:
                    segments.append((alt_text, list(base_tags) + ['bold']))
                segments.append((' \u2192 ', list(base_tags)))
                segments.append((img_path, list(base_tags) + ['link_url']))
                segments.append((']', list(base_tags)))
            elif earliest_type == 'link':
                link_text = earliest_match.group(1)
                link_url = earliest_match.group(2)
                segments.append((link_text, list(base_tags) + ['link_text']))
                segments.append((' (', list(base_tags)))
                segments.append((link_url, list(base_tags) + ['link_url']))
                segments.append((')', list(base_tags)))
            else:
                # Inline formatting - recurse for nested formatting
                inner_text = earliest_match.group(1)
                combined_tags = list(base_tags) + list(earliest_pattern_tags)
                # Recurse to handle nested inline formatting (e.g. bold inside italic)
                # But don't recurse for code_inline - it should be literal
                if 'code_inline' in earliest_pattern_tags:
                    segments.append((inner_text, combined_tags))
                else:
                    self._parse_inline(inner_text, segments, combined_tags)

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