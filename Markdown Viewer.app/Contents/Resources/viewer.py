#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown Viewer for PowerPC Mac
A lightweight Markdown viewer built with Tkinter for Mac OS X 10.5 / Python 2.5.

Usage:
    python viewer.py [file.md]
"""

import sys
import os
import Tkinter as tk
import tkFont
import tkFileDialog
import tkMessageBox
from markdown_parser import MarkdownParser


class MarkdownViewer(object):
    """Main application window for the Markdown Viewer."""

    APP_NAME = "Markdown Viewer"
    WINDOW_WIDTH = 720
    WINDOW_HEIGHT = 580
    BG_COLOR = "#FEFEFE"
    TEXT_COLOR = "#1A1A1A"
    ACCENT_COLOR = "#2860A0"
    CODE_BG = "#F0F0F0"
    BLOCKQUOTE_COLOR = "#555555"
    HR_COLOR = "#CCCCCC"

    def __init__(self, root, filepath=None):
        self.root = root
        self.parser = MarkdownParser()
        self.current_file = None

        self._setup_window()
        self._setup_fonts()
        self._setup_menu()
        self._setup_ui()
        self._setup_tags()
        self._bind_keys()

        if filepath and os.path.isfile(filepath):
            self.open_file(filepath)
        else:
            self._show_welcome()

    def _setup_window(self):
        self.root.title(self.APP_NAME)
        self.root.geometry("%dx%d" % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        self.root.minsize(400, 300)
        self.root.configure(bg=self.BG_COLOR)

    def _setup_fonts(self):
        available = list(tkFont.families())

        if "Lucida Grande" in available:
            family = "Lucida Grande"
        elif "Helvetica" in available:
            family = "Helvetica"
        else:
            family = "TkDefaultFont"

        if "Monaco" in available:
            mono_family = "Monaco"
        elif "Courier" in available:
            mono_family = "Courier"
        else:
            mono_family = "TkFixedFont"

        base_size = 13

        self.fonts = {
            'normal': tkFont.Font(family=family, size=base_size),
            'bold': tkFont.Font(family=family, size=base_size, weight="bold"),
            'italic': tkFont.Font(family=family, size=base_size, slant="italic"),
            'bold_italic': tkFont.Font(family=family, size=base_size,
                                       weight="bold", slant="italic"),
            'h1': tkFont.Font(family=family, size=base_size + 13, weight="bold"),
            'h2': tkFont.Font(family=family, size=base_size + 9, weight="bold"),
            'h3': tkFont.Font(family=family, size=base_size + 5, weight="bold"),
            'h4': tkFont.Font(family=family, size=base_size + 3, weight="bold"),
            'h5': tkFont.Font(family=family, size=base_size + 1, weight="bold"),
            'h6': tkFont.Font(family=family, size=base_size, weight="bold"),
            'code': tkFont.Font(family=mono_family, size=base_size - 1),
            'code_block': tkFont.Font(family=mono_family, size=base_size - 1),
        }

        self.base_size = base_size

    def _setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open...", command=self.cmd_open,
                              accelerator="Command-O")
        file_menu.add_command(label="Reload", command=self.cmd_reload,
                              accelerator="Command-R")
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.cmd_close,
                              accelerator="Command-W")
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy", command=self.cmd_copy,
                              accelerator="Command-C")
        edit_menu.add_command(label="Select All", command=self.cmd_select_all,
                              accelerator="Command-A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", command=self.cmd_find,
                              accelerator="Command-F")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.cmd_zoom_in,
                              accelerator="Command-+")
        view_menu.add_command(label="Zoom Out", command=self.cmd_zoom_out,
                              accelerator="Command--")
        view_menu.add_command(label="Reset Zoom", command=self.cmd_zoom_reset,
                              accelerator="Command-0")
        menubar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=menubar)

    def _setup_ui(self):
        # Top toolbar with file info
        self.toolbar = tk.Frame(self.root, bg="#E8E8E8", height=28)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        self.file_label = tk.Label(
            self.toolbar, text="No file loaded",
            bg="#E8E8E8", fg="#666666",
            font=tkFont.Font(size=11), anchor=tk.W, padx=10
        )
        self.file_label.pack(fill=tk.X, expand=True)

        # Main text area with scrollbar
        text_frame = tk.Frame(self.root)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(
            text_frame, wrap=tk.WORD,
            bg=self.BG_COLOR, fg=self.TEXT_COLOR,
            font=self.fonts['normal'],
            padx=30, pady=20,
            spacing1=2, spacing3=2,
            cursor="arrow",
            state=tk.DISABLED,
            relief=tk.FLAT,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text.yview)

        # Find bar (hidden by default)
        self.find_frame = tk.Frame(self.root, bg="#E8E8D8", height=30)
        self.find_frame.pack_propagate(False)
        self.find_visible = False

        find_label = tk.Label(self.find_frame, text="Find:",
                              bg="#E8E8D8", fg="#333333",
                              font=tkFont.Font(size=11))
        find_label.pack(side=tk.LEFT, padx=(10, 4))

        self.find_entry = tk.Entry(self.find_frame, width=30,
                                    font=tkFont.Font(size=11),
                                    highlightthickness=1,
                                    relief=tk.SOLID)
        self.find_entry.pack(side=tk.LEFT, padx=2, pady=4)
        self.find_entry.bind('<Return>', lambda e: self._do_find())
        self.find_entry.bind('<Escape>', lambda e: self._hide_find_bar())

        find_btn = tk.Button(self.find_frame, text="Next",
                             command=self._do_find,
                             font=tkFont.Font(size=10))
        find_btn.pack(side=tk.LEFT, padx=4)

        find_prev_btn = tk.Button(self.find_frame, text="Prev",
                                   command=self._do_find_prev,
                                   font=tkFont.Font(size=10))
        find_prev_btn.pack(side=tk.LEFT, padx=2)

        self.find_count_label = tk.Label(self.find_frame, text="",
                                          bg="#E8E8D8", fg="#666666",
                                          font=tkFont.Font(size=10))
        self.find_count_label.pack(side=tk.LEFT, padx=8)

        find_close_btn = tk.Button(self.find_frame, text="\xC3\x97",
                                    command=self._hide_find_bar,
                                    font=tkFont.Font(size=11),
                                    relief=tk.FLAT, bg="#E8E8D8")
        find_close_btn.pack(side=tk.RIGHT, padx=6)

        self.find_pos = '1.0'

        # Status bar
        self.statusbar = tk.Frame(self.root, bg="#E0E0E0", height=22)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)

        self.status_label = tk.Label(
            self.statusbar, text="Ready",
            bg="#E0E0E0", fg="#888888",
            font=tkFont.Font(size=10), anchor=tk.W, padx=10
        )
        self.status_label.pack(fill=tk.X, expand=True)

    def _setup_tags(self):
        """Configure text widget tags for markdown styling."""
        t = self.text

        t.tag_configure('h1', font=self.fonts['h1'], foreground=self.TEXT_COLOR,
                         spacing1=16, spacing3=8)
        t.tag_configure('h2', font=self.fonts['h2'], foreground=self.TEXT_COLOR,
                         spacing1=14, spacing3=6)
        t.tag_configure('h3', font=self.fonts['h3'], foreground=self.TEXT_COLOR,
                         spacing1=10, spacing3=4)
        t.tag_configure('h4', font=self.fonts['h4'], foreground=self.TEXT_COLOR,
                         spacing1=8, spacing3=4)
        t.tag_configure('h5', font=self.fonts['h5'], foreground=self.TEXT_COLOR,
                         spacing1=6, spacing3=2)
        t.tag_configure('h6', font=self.fonts['h6'], foreground="#444444",
                         spacing1=6, spacing3=2)

        t.tag_configure('normal', font=self.fonts['normal'])
        t.tag_configure('bold', font=self.fonts['bold'])
        t.tag_configure('italic', font=self.fonts['italic'])
        t.tag_configure('bold_italic', font=self.fonts['bold_italic'])
        t.tag_configure('code_inline', font=self.fonts['code'],
                         background=self.CODE_BG, foreground="#C7254E")
        t.tag_configure('strikethrough', overstrike=True)

        t.tag_configure('code_block', font=self.fonts['code_block'],
                         background=self.CODE_BG, foreground=self.TEXT_COLOR,
                         lmargin1=30, lmargin2=30, rmargin=30,
                         spacing1=6, spacing3=6)

        t.tag_configure('list_bullet', font=self.fonts['normal'],
                         foreground=self.ACCENT_COLOR)
        t.tag_configure('list_item', font=self.fonts['normal'])

        t.tag_configure('blockquote', font=self.fonts['italic'],
                         foreground=self.BLOCKQUOTE_COLOR,
                         lmargin1=40, lmargin2=40)
        t.tag_configure('blockquote_bar', foreground=self.ACCENT_COLOR,
                         font=self.fonts['normal'])

        t.tag_configure('hr', foreground=self.HR_COLOR, justify=tk.CENTER,
                         spacing1=8, spacing3=8)

        t.tag_configure('link_text', font=self.fonts['normal'],
                         foreground=self.ACCENT_COLOR, underline=True)
        t.tag_configure('link_url', font=self.fonts['code'],
                         foreground="#888888")
        t.tag_configure('image_icon', font=self.fonts['bold'],
                         foreground="#D4882A")

        t.tag_configure('find_highlight', background="#FFFF00",
                         foreground="#000000")
        t.tag_configure('find_current', background="#FF9632",
                         foreground="#000000")

    def _bind_keys(self):
        self.root.bind('<Command-o>', lambda e: self.cmd_open())
        self.root.bind('<Command-O>', lambda e: self.cmd_open())
        self.root.bind('<Command-r>', lambda e: self.cmd_reload())
        self.root.bind('<Command-R>', lambda e: self.cmd_reload())
        self.root.bind('<Command-w>', lambda e: self.cmd_close())
        self.root.bind('<Command-W>', lambda e: self.cmd_close())
        self.root.bind('<Command-equal>', lambda e: self.cmd_zoom_in())
        self.root.bind('<Command-plus>', lambda e: self.cmd_zoom_in())
        self.root.bind('<Command-minus>', lambda e: self.cmd_zoom_out())
        self.root.bind('<Command-0>', lambda e: self.cmd_zoom_reset())
        self.root.bind('<Command-a>', lambda e: self.cmd_select_all())
        self.root.bind('<Command-A>', lambda e: self.cmd_select_all())
        self.root.bind('<Command-f>', lambda e: self.cmd_find())
        self.root.bind('<Command-F>', lambda e: self.cmd_find())
        self.root.bind('<Escape>', lambda e: self._hide_find_bar())
        self.text.bind('<MouseWheel>', self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.text.yview_scroll(-1 * (event.delta), "units")

    def _show_welcome(self):
        welcome = (
            "# Welcome to Markdown Viewer\n\n"
            "This is a lightweight Markdown viewer for **PowerPC Macs**.\n\n"
            "## Getting Started\n\n"
            "- Use **File > Open** (or **Cmd+O**) to open a `.md` file\n"
            "- Use **Cmd+R** to reload the current file\n"
            "- Use **Cmd+** / **Cmd-** to zoom in and out\n"
            "- Use **Cmd+F** to search within the document\n\n"
            "## Supported Markdown\n\n"
            "- **Bold**, *italic*, and ***bold italic***\n"
            "- Nested formatting like ***bold and italic*** inside *an italic phrase*\n"
            "- `Inline code` and fenced code blocks\n"
            "- Headings (H1 through H6)\n"
            "- Ordered and unordered lists\n"
            "- Blockquotes\n"
            "- Horizontal rules\n"
            "- ~~Strikethrough~~\n"
            "- [Links](https://example.com) with visible URLs\n"
            "- ![Image references](path/to/image.png) displayed as paths\n\n"
            "---\n\n"
            "*Built for Mac OS X Leopard on PowerPC*\n"
        )
        self._render(welcome)

    def _render(self, markdown_text):
        """Parse and render markdown into the text widget."""
        segments = self.parser.parse(markdown_text)

        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)

        for text_content, tags in segments:
            resolved_tags = self._resolve_tags(tags)
            self.text.insert(tk.END, text_content, tuple(resolved_tags))

        self.text.config(state=tk.DISABLED)

    def _resolve_tags(self, tags):
        """Resolve tag combinations."""
        resolved = []
        has_bold = 'bold' in tags
        has_italic = 'italic' in tags

        if has_bold and has_italic:
            resolved.append('bold_italic')
            tags = [t for t in tags if t not in ('bold', 'italic')]

        resolved.extend(tags)
        return resolved

    def open_file(self, filepath):
        """Open and render a markdown file."""
        try:
            f = open(filepath, 'r')
            try:
                content = f.read()
            finally:
                f.close()

            self.current_file = filepath
            filename = os.path.basename(filepath)
            self.root.title("%s - %s" % (filename, self.APP_NAME))
            self.file_label.config(text=filepath, fg="#333333")
            self._render(content)

            num_lines = content.count('\n') + 1
            file_size = os.path.getsize(filepath)
            if file_size < 1024:
                size_str = "%d bytes" % file_size
            else:
                size_str = "%.1f KB" % (file_size / 1024.0)
            self.status_label.config(
                text="%s  |  %d lines  |  %s" % (filename, num_lines, size_str)
            )

        except IOError, e:
            tkMessageBox.showerror("Error",
                                   "Could not open file:\n%s" % str(e))
        except Exception, e:
            tkMessageBox.showerror("Error",
                                   "Error reading file:\n%s" % str(e))

    def cmd_open(self):
        filepath = tkFileDialog.askopenfilename(
            title="Open Markdown File",
            filetypes=[
                ("Markdown files", "*.md"),
                ("Markdown files", "*.markdown"),
                ("Markdown files", "*.mdown"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ]
        )
        if filepath:
            self.open_file(filepath)

    def cmd_reload(self):
        if self.current_file:
            self.open_file(self.current_file)

    def cmd_close(self):
        self.root.destroy()

    def cmd_copy(self):
        try:
            self.root.clipboard_clear()
            text = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_append(text)
        except tk.TclError:
            pass

    def cmd_select_all(self):
        self.text.config(state=tk.NORMAL)
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def cmd_zoom_in(self):
        self._adjust_zoom(2)

    def cmd_zoom_out(self):
        self._adjust_zoom(-2)

    def cmd_zoom_reset(self):
        base = self.base_size
        defaults = {
            'normal': base, 'bold': base, 'italic': base,
            'bold_italic': base,
            'h1': base + 13, 'h2': base + 9, 'h3': base + 5,
            'h4': base + 3, 'h5': base + 1, 'h6': base,
            'code': base - 1, 'code_block': base - 1,
        }
        for name, size in defaults.items():
            if name in self.fonts:
                self.fonts[name].configure(size=size)

    def _adjust_zoom(self, delta):
        for font in self.fonts.values():
            current = font.cget("size")
            new_size = max(8, current + delta)
            font.configure(size=new_size)

    def cmd_find(self):
        """Show the find bar and focus the entry."""
        if not self.find_visible:
            self.find_frame.pack(fill=tk.X, side=tk.BOTTOM,
                                 before=self.statusbar)
            self.find_visible = True
        self.find_entry.focus_set()
        self.find_entry.selection_range(0, tk.END)

    def _hide_find_bar(self):
        """Hide the find bar and clear highlights."""
        if self.find_visible:
            self.find_frame.pack_forget()
            self.find_visible = False
            self.text.tag_remove('find_highlight', '1.0', tk.END)
            self.text.tag_remove('find_current', '1.0', tk.END)
            self.find_count_label.config(text="")
            self.find_pos = '1.0'

    def _do_find(self):
        """Find next occurrence of the search term."""
        query = self.find_entry.get()
        if not query:
            return

        # Clear previous highlights
        self.text.tag_remove('find_highlight', '1.0', tk.END)
        self.text.tag_remove('find_current', '1.0', tk.END)

        # Highlight all matches
        count_var = tk.StringVar()
        total = 0
        start = '1.0'
        while True:
            pos = self.text.search(query, start, stopindex=tk.END,
                                    nocase=True, count=count_var)
            if not pos:
                break
            total += 1
            end = '%s+%sc' % (pos, count_var.get())
            self.text.tag_add('find_highlight', pos, end)
            start = end

        if total == 0:
            self.find_count_label.config(text="Not found")
            self.find_pos = '1.0'
            return

        # Find next from current position
        pos = self.text.search(query, self.find_pos, stopindex=tk.END,
                                nocase=True, count=count_var)
        if not pos:
            # Wrap around
            pos = self.text.search(query, '1.0', stopindex=tk.END,
                                    nocase=True, count=count_var)

        if pos:
            end = '%s+%sc' % (pos, count_var.get())
            self.text.tag_add('find_current', pos, end)
            self.text.see(pos)
            self.find_pos = end
            self.find_count_label.config(text="%d found" % total)

    def _do_find_prev(self):
        """Find previous occurrence of the search term."""
        query = self.find_entry.get()
        if not query:
            return

        # Clear previous highlights
        self.text.tag_remove('find_highlight', '1.0', tk.END)
        self.text.tag_remove('find_current', '1.0', tk.END)

        # Highlight all matches
        count_var = tk.StringVar()
        total = 0
        start = '1.0'
        while True:
            pos = self.text.search(query, start, stopindex=tk.END,
                                    nocase=True, count=count_var)
            if not pos:
                break
            total += 1
            end = '%s+%sc' % (pos, count_var.get())
            self.text.tag_add('find_highlight', pos, end)
            start = end

        if total == 0:
            self.find_count_label.config(text="Not found")
            self.find_pos = '1.0'
            return

        # Search backwards from current position
        pos = self.text.search(query, self.find_pos, stopindex='1.0',
                                nocase=True, count=count_var,
                                backwards=True)
        if not pos:
            # Wrap to end
            pos = self.text.search(query, tk.END, stopindex='1.0',
                                    nocase=True, count=count_var,
                                    backwards=True)

        if pos:
            end = '%s+%sc' % (pos, count_var.get())
            self.text.tag_add('find_current', pos, end)
            self.text.see(pos)
            self.find_pos = pos
            self.find_count_label.config(text="%d found" % total)


def main():
    root = tk.Tk()

    filepath = None
    if len(sys.argv) > 1:
        filepath = sys.argv[1]

    app = MarkdownViewer(root, filepath)
    root.mainloop()


if __name__ == '__main__':
    main()