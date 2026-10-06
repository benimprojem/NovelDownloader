############################################
# NovelDovnload.py için NovelReader.py
# ver. 0.9.6
# 30.10.2025
# Halen hataları ve eksikleri olabilir. Gğrdüğüm tüm hatalrı gidermeye çalıştım.
# Optimize edilmemiştir. İçerisinde halen gereksiz veya fazladan kod bulunabilir..
# Edit: D'ssconnecTed.  Kodlayan: Gemini. :)
# 
#############################################
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import re
import threading
import time
import importlib.util
from urllib.parse import urlparse

# --- Sabitler ve Ayarlar ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
NOVELS_DIR = os.path.join(APP_DIR, "novels")
STATE_FILE = os.path.join(APP_DIR, "readnovel_state.json")
DOWNLOADER_FILE = os.path.join(APP_DIR, "NovelDovnload_3.py")
LINE_HEIGHT = 20 

# Tema color
THEMES = {
    "light": {
        "bg": "white",
        "fg": "black",
        "text_bg": "white",
        "text_fg": "black",
        "button_bg": "#f0f0f0",
        "button_fg": "black",
        "highlight_bg": "lightblue",
        "list_bg": "white",
        "list_fg": "black"
    },
    "dark": {
        "bg": "#020d18",
        "fg": "#ECEEDF",
        "text_bg": "#06121e",
        "text_fg": "#ECEEDF",
        "button_bg": "#06121e",
        "button_fg": "#ECEEDF",
        "highlight_bg": "#84994F",
        "list_bg": "#020d18",
        "list_fg": "#ECEEDF"
    }
}



class GridChapterList:
    """Büyük bölüm listeleri için sanal (virtualized) ızgara.

    Yalnızca görünür alan + bir ekranlık tampon oluşturulur. Böylece binlerce
    bölümün tamamı aynı anda Tkinter widget'ına dönüştürülmez.
    """
    def __init__(self, parent, callback=None, item_width=210, item_height=42):
        self.parent = parent
        self.callback = callback
        self.item_width = item_width
        self.item_height = item_height
        self.items = []
        self.selected = None
        self._config = {}
        self._widgets = {}
        self._cols = 1
        self._rows = 1
        self._render_after = None
        self._last_view = None

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(parent, highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vscroll = ttk.Scrollbar(parent, orient="vertical", command=self._scroll_y)
        self.vscroll.grid(row=0, column=1, sticky="ns")
        self.hscroll = ttk.Scrollbar(parent, orient="horizontal", command=self._scroll_x)
        self.hscroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=self._set_y_scroll,
                             xscrollcommand=self._set_x_scroll)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._shiftwheel)
        self.canvas.bind("<Button-4>", lambda e: self._wheel_units(-3))
        self.canvas.bind("<Button-5>", lambda e: self._wheel_units(3))

    def _set_y_scroll(self, first, last):
        self.vscroll.set(first, last)

    def _set_x_scroll(self, first, last):
        self.hscroll.set(first, last)

    def _scroll_y(self, *args):
        self.canvas.yview(*args)
        self._schedule_render()

    def _scroll_x(self, *args):
        self.canvas.xview(*args)
        self._schedule_render()

    def _wheel_units(self, units):
        self.canvas.yview_scroll(units, "units")
        self._schedule_render()

    def _mousewheel(self, event):
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta * 3, "units")
            self._schedule_render()
        return "break"

    def _shiftwheel(self, event):
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.canvas.xview_scroll(delta * 3, "units")
            self._schedule_render()
        return "break"

    def _on_canvas_configure(self, event=None):
        self._schedule_render()

    def _schedule_render(self):
        if self._render_after is not None:
            try:
                self.canvas.after_cancel(self._render_after)
            except Exception:
                pass
        self._render_after = self.canvas.after_idle(self._render_visible)

    def _visible_geometry(self):
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        cols = max(1, width // self.item_width)
        rows = max(1, height // self.item_height)
        return cols, rows

    def _render_visible(self):
        self._render_after = None
        if not self.items:
            for w in self._widgets.values():
                w.destroy()
            self._widgets.clear()
            self.canvas.configure(scrollregion=(0, 0, 1, 1))
            return

        # Sütun-dolgu düzeni: önce yukarıdan aşağı, sonra sağdaki sütuna geç.
        rows = max(1, self.canvas.winfo_height() // self.item_height)
        cols = max(1, self.canvas.winfo_width() // self.item_width)
        self._rows = rows
        self._cols = cols
        total_cols = (len(self.items) + rows - 1) // rows
        total_w = total_cols * self.item_width
        total_h = rows * self.item_height
        self.canvas.configure(scrollregion=(0, 0, total_w, total_h))

        x0 = self.canvas.canvasx(0)
        y0 = self.canvas.canvasy(0)
        x1 = x0 + max(1, self.canvas.winfo_width())
        y1 = y0 + max(1, self.canvas.winfo_height())

        first_col = max(0, int(x0 // self.item_width))
        last_col = min(total_cols - 1, int(max(x0, x1 - 1) // self.item_width))
        first_row = max(0, int(y0 // self.item_height))
        last_row = min(rows - 1, int(max(y0, y1 - 1) // self.item_height))

        # Bir ekranlık tampon. Sadece yakın bölümler widget olarak tutulur.
        buffer_cols = max(1, last_col - first_col + 1)
        buffer_rows = max(1, last_row - first_row + 1)
        first_col = max(0, first_col - buffer_cols)
        last_col = min(total_cols - 1, last_col + buffer_cols)
        first_row = max(0, first_row - buffer_rows)
        last_row = min(rows - 1, last_row + buffer_rows)

        needed = set()
        for col in range(first_col, last_col + 1):
            for row in range(first_row, last_row + 1):
                index = col * rows + row
                if index >= len(self.items):
                    continue
                needed.add(index)
                if index not in self._widgets:
                    self._widgets[index] = self._make_button(index)
                widget = self._widgets[index]
                widget.place(x=col * self.item_width + 4,
                             y=row * self.item_height + 4,
                             width=self.item_width - 8,
                             height=self.item_height - 8)

        for index in list(self._widgets):
            if index not in needed:
                self._widgets[index].destroy()
                del self._widgets[index]

        self._refresh_selection()

    def _make_button(self, index):
        button = tk.Button(
            self.canvas,
            text=self.items[index],
            anchor="w", justify="left",
            wraplength=self.item_width - 25,
            font=("Arial", 10),
            relief="flat", bd=1, padx=8, pady=3
        )
        button.configure(command=lambda n=index: self._select(n))
        button.bind("<Double-Button-1>", lambda e, n=index: self._double_click(e, n))
        return button

    def _select(self, index):
        if not (0 <= index < len(self.items)):
            return
        self.selected = index
        self._refresh_selection()

    def _double_click(self, event, index):
        self._select(index)
        if self.callback:
            self.callback(event)

    def _refresh_selection(self):
        theme = self._config
        for i, button in self._widgets.items():
            if i == self.selected:
                button.configure(
                    bg=theme.get("selectbackground", "lightblue"),
                    fg=theme.get("selectforeground", theme.get("fg", "black"))
                )
            else:
                button.configure(
                    bg=theme.get("bg", "white"),
                    fg=theme.get("fg", "black")
                )

    def set_items(self, items):
        for w in self._widgets.values():
            w.destroy()
        self._widgets.clear()
        self.items = [str(x) for x in items]
        self.selected = None
        self._last_view = None
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self._schedule_render()

    def insert(self, index, text):
        # Eski Listbox API uyumluluğu; gerçek ekleme sonrası yalnızca görünür alan çizilir.
        if index in (tk.END, len(self.items)):
            self.items.append(str(text))
        else:
            self.items.insert(index, str(text))
        for w in self._widgets.values():
            w.destroy()
        self._widgets.clear()
        self._schedule_render()

    def delete(self, first=0, last=None):
        if not self.items:
            return
        if last is None:
            last = first
        if last == tk.END:
            last = len(self.items) - 1
        del self.items[first:last + 1]
        self.selected = None
        for w in self._widgets.values():
            w.destroy()
        self._widgets.clear()
        self._schedule_render()

    def get(self, first, last=None):
        if last is None:
            return self.items[first]
        if last == tk.END:
            last = len(self.items) - 1
        return tuple(self.items[first:last + 1])

    def curselection(self):
        return () if self.selected is None else (self.selected,)

    def selection_clear(self, first=0, last=tk.END):
        self.selected = None
        self._refresh_selection()

    def selection_set(self, index):
        self._select(index)

    def activate(self, index):
        self._select(index)

    def see(self, index):
        if not (0 <= index < len(self.items)):
            return
        self.update_idletasks()
        rows = max(1, self.canvas.winfo_height() // self.item_height)
        total_cols = max(1, (len(self.items) + rows - 1) // rows)
        row = index % rows
        col = index // rows
        x = col * self.item_width
        y = row * self.item_height

        # Aktif bölüm mümkün olduğunca ekranın ortasına gelsin.
        view_w = max(1, self.canvas.winfo_width())
        view_h = max(1, self.canvas.winfo_height())
        max_x = max(0, total_cols * self.item_width - view_w)
        max_y = max(0, rows * self.item_height - view_h)
        target_x = min(max_x, max(0, x + self.item_width / 2 - view_w / 2))
        target_y = min(max_y, max(0, y + self.item_height / 2 - view_h / 2))
        total_w = max(1, total_cols * self.item_width)
        total_h = max(1, rows * self.item_height)
        self.canvas.xview_moveto(target_x / max(1, total_w))
        self.canvas.yview_moveto(target_y / max(1, total_h))
        self._schedule_render()

    def _total_width(self):
        rows = max(1, self.canvas.winfo_height() // self.item_height)
        total_cols = max(1, (len(self.items) + rows - 1) // rows)
        return max(1, total_cols * self.item_width)

    def _total_height(self):
        rows = max(1, self.canvas.winfo_height() // self.item_height)
        return max(1, rows * self.item_height)

    def bind(self, sequence, func, add=None):
        self._bound_callback = func

    def config(self, **kwargs):
        self._config.update(kwargs)
        if "bg" in kwargs:
            self.canvas.configure(bg=kwargs["bg"])
        self._refresh_selection()

    configure = config

    def update_idletasks(self):
        self.canvas.update_idletasks()

class NovelReaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Read Novel v1.4")
        master.geometry("1040x630")

        self.novels_path = NOVELS_DIR
        self.novel_data = {}  
        self.current_novel = None
        self.current_chapter_file = None
        self.current_language = None 
        
        self.current_content = []  
        self.chapter_lists = {} 
        self.current_chapters_list = []

        # Downloader arka planda çalışır; reader sekmeleri çalışmaya devam eder.
        self.downloader = None
        self.download_control = None
        self.download_thread = None
        self.download_mode = None
        self.download_current_novel = None
        self.download_status_var = tk.StringVar(value="Hazır")
        self.download_progress_var = tk.StringVar(value="")
        self.download_pause_var = tk.StringVar(value="Duraklat")
        
        self.state = self.load_state()
        self.current_theme = self.state.get('theme', 'dark')
        
        self.setup_ui()
        self.apply_theme(self.current_theme)
        
        # Klavye olaylarını bağlama
        self.master.bind('<Key>', self.on_key_press)
        
        # load_novels_from_dir, novel listesini doldurur ve load_last_read'i tetikler
        self.load_novels_from_dir(initial_load=True)
        self.refresh_download_list()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        self.top_controls_frame = ttk.Frame(self.master)
        self.top_controls_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.novel_title_label = ttk.Label(
            self.top_controls_frame, text="Novel Seçilmedi",
            font=("Arial", 14, "bold")
        )
        self.novel_title_label.pack(side=tk.LEFT, padx=10, pady=2)

        self.button_align_frame = ttk.Frame(self.top_controls_frame)
        self.button_align_frame.pack(side=tk.RIGHT)
        ttk.Button(self.button_align_frame, text="Novel",
                   command=self.select_novels_dir).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_align_frame, text="Yenile",
                   command=self.refresh_novels).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_align_frame, text="⭐",
                   command=self.toggle_theme).pack(side=tk.LEFT, padx=2)

        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.main_notebook = ttk.Notebook(self.content_frame)
        self.main_notebook.grid(row=0, column=0, sticky="nsew")

        # 1) DOWNLOADS
        self.download_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.download_tab, text="Downloads")
        self.setup_download_tab()

        # 2) NOVEL LISTESİ
        self.novel_list_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.novel_list_tab, text="Novel Listesi")
        self.novel_list_tab.grid_rowconfigure(1, weight=1)
        self.novel_list_tab.grid_columnconfigure(0, weight=1)

        list_info = ttk.Frame(self.novel_list_tab)
        list_info.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        self.novel_count_label = ttk.Label(list_info, text="0 novel")
        self.novel_count_label.pack(side=tk.LEFT)
        ttk.Button(list_info, text="Yenile", command=self.refresh_novels).pack(side=tk.RIGHT)

        self.novel_canvas_frame = ttk.Frame(self.novel_list_tab)
        self.novel_canvas_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.novel_canvas_frame.grid_rowconfigure(0, weight=1)
        self.novel_canvas_frame.grid_columnconfigure(0, weight=1)

        self.novel_canvas = tk.Canvas(self.novel_canvas_frame, highlightthickness=0)
        self.novel_canvas.grid(row=0, column=0, sticky="nsew")
        self.novel_vscroll = ttk.Scrollbar(
            self.novel_canvas_frame, orient="vertical", command=self.novel_canvas.yview
        )
        self.novel_vscroll.grid(row=0, column=1, sticky="ns")
        self.novel_hscroll = ttk.Scrollbar(
            self.novel_canvas_frame, orient="horizontal", command=self.novel_canvas.xview
        )
        self.novel_hscroll.grid(row=1, column=0, sticky="ew")
        self.novel_canvas.configure(yscrollcommand=self.novel_vscroll.set, xscrollcommand=self.novel_hscroll.set)
        self.novel_tiles_frame = ttk.Frame(self.novel_canvas)
        self.novel_canvas_window = self.novel_canvas.create_window(
            (0, 0), window=self.novel_tiles_frame, anchor="nw"
        )
        self.novel_tiles_frame.bind("<Configure>", self._update_novel_canvas)
        self.novel_canvas.bind("<Configure>", self._relayout_novel_tiles)
        self.novel_canvas.bind("<MouseWheel>", self._novel_mousewheel)
        self.novel_canvas.bind("<Shift-MouseWheel>", self._novel_shift_scroll)

        # 3) BÖLÜMLER
        self.chapter_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.chapter_tab, text="Bölümler")
        self.chapter_tab.grid_rowconfigure(0, weight=1)
        self.chapter_tab.grid_columnconfigure(0, weight=1)
        self.chapter_notebook = ttk.Notebook(self.chapter_tab)
        self.chapter_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chapter_notebook.bind('<<NotebookTabChanged>>', self.on_chapter_tab_change)
        self.original_tab = self.create_chapter_list_tab("Orijinal (en)", 'en')
        self.chapter_notebook.add(self.original_tab, text="Orijinal (en)")
        self.translation_tab = self.create_chapter_list_tab("Çeviri (tr)", 'tr')
        self.chapter_notebook.add(self.translation_tab, text="Çeviri (tr)")

        # 4) OKUMA
        self.reader_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.reader_tab, text="Okuma")
        self.reader_tab.grid_rowconfigure(0, weight=1)
        self.reader_tab.grid_columnconfigure(0, weight=1)
        self.text_area_scrollbar = ttk.Scrollbar(self.reader_tab)
        self.text_area_scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_area = tk.Text(
            self.reader_tab, wrap=tk.WORD, font=("Arial", 13), state=tk.DISABLED,
            yscrollcommand=self.text_area_scrollbar.set, padx=20, pady=20
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")
        self.text_area_scrollbar.config(command=self.text_area.yview)

        self.bottom_controls_left = ttk.Frame(self.reader_tab)
        self.bottom_controls_left.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.bottom_controls_left.grid_columnconfigure(0, weight=1)
        self.bottom_controls_left.grid_columnconfigure(1, weight=1)
        self.bottom_controls_left.grid_columnconfigure(2, weight=1)
        self.read_page_info_label = ttk.Label(self.bottom_controls_left, text="Bölüm Açılmadı")
        self.read_page_info_label.grid(row=0, column=1, padx=10)
        self.prev_page_button = ttk.Button(
            self.bottom_controls_left, text="<< Geri", command=lambda: self.change_chapter(-1)
        )
        self.prev_page_button.grid(row=0, column=0, sticky="w", padx=(5, 0))
        self.next_page_button = ttk.Button(
            self.bottom_controls_left, text="İleri >>", command=lambda: self.change_chapter(1)
        )
        self.next_page_button.grid(row=0, column=2, sticky="e", padx=(0, 5))
        self.toggle_read_controls(False)

    def setup_download_tab(self):
        tab = self.download_tab
        tab.grid_rowconfigure(5, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        top = ttk.LabelFrame(tab, text="Yeni İndirme")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top.grid_columnconfigure(1, weight=1)
        ttk.Label(top, text="İlk bölüm URL:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.download_url_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.download_url_var).grid(row=0, column=1, columnspan=3, padx=6, pady=6, sticky="ew")
        ttk.Label(top, text="Bölüm sayısı:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.download_limit_var = tk.StringVar(value="0")
        ttk.Entry(top, textvariable=self.download_limit_var, width=12).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ttk.Button(top, text="Yeni İndirme", command=self.start_new_download).grid(row=1, column=2, padx=6, pady=6)
        ttk.Button(top, text="Seçileni Devam Ettir", command=self.resume_selected_download).grid(row=1, column=3, padx=6, pady=6)

        controls = ttk.Frame(tab)
        controls.grid(row=1, column=0, sticky="ew", padx=10)
        ttk.Button(controls, text="Duraklat / Devam", command=self.toggle_download_pause).pack(side=tk.LEFT, padx=3)
        ttk.Button(controls, text="Durdur", command=self.stop_download).pack(side=tk.LEFT, padx=3)
        ttk.Button(controls, text="Çevir", command=self.start_translation).pack(side=tk.LEFT, padx=3)
        ttk.Button(controls, text="Listeyi Yenile", command=self.refresh_download_list).pack(side=tk.LEFT, padx=3)

        status = ttk.Frame(tab)
        status.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        self.download_status_label = ttk.Label(status, textvariable=self.download_status_var, font=("Arial", 10, "bold"))
        self.download_status_label.pack(side=tk.LEFT)
        self.download_progress_label = ttk.Label(status, textvariable=self.download_progress_var)
        self.download_progress_label.pack(side=tk.RIGHT)

        self.download_progressbar = ttk.Progressbar(tab, mode="determinate", maximum=100)
        self.download_progressbar.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))

        self.download_activity = tk.Text(tab, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.download_activity.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 6))

        self.download_tree = ttk.Treeview(
            tab, columns=("novel", "downloaded", "total", "untranslated"),
            show="headings", selectmode="browse"
        )
        self.download_tree.grid(row=5, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.download_tree.heading("novel", text="Novel")
        self.download_tree.heading("downloaded", text="İndirilen")
        self.download_tree.heading("total", text="Toplam")
        self.download_tree.heading("untranslated", text="Çevrilmemiş")
        self.download_tree.column("novel", width=420, anchor="w")
        self.download_tree.column("downloaded", width=100, anchor="center")
        self.download_tree.column("total", width=100, anchor="center")
        self.download_tree.column("untranslated", width=120, anchor="center")
        self.download_tree.bind("<Double-1>", self.open_selected_novel)

    def _update_novel_canvas(self, event=None):
        self.novel_canvas.configure(scrollregion=self.novel_canvas.bbox("all"))

    def _relayout_novel_tiles(self, event=None):
        if not hasattr(self, "novel_tiles_frame"):
            return
        names = sorted(self.novel_data.keys(), key=str.lower)
        if not names:
            self._update_novel_canvas()
            return
        card_w, card_h = 250, 130
        rows = max(1, self.novel_canvas.winfo_height() // (card_h + 10))
        cards = self.novel_tiles_frame.winfo_children()
        columns = max(1, (len(cards) + rows - 1) // rows)
        for r in range(rows):
            self.novel_tiles_frame.grid_rowconfigure(r, minsize=card_h + 10, weight=0)
        for c in range(columns):
            self.novel_tiles_frame.grid_columnconfigure(c, minsize=card_w + 10, weight=0)
        for i, card in enumerate(cards):
            card.configure(width=card_w, height=card_h)
            card.grid(row=i % rows, column=i // rows, sticky="nsew", padx=5, pady=5)
        self.novel_tiles_frame.update_idletasks()
        self._update_novel_canvas()

    def _novel_mousewheel(self, event):
        self.novel_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _novel_shift_scroll(self, event):
        self.novel_canvas.xview_scroll(int(-event.delta / 120), "units")

    def _keep_novel_tiles_height(self, event=None):
        self._relayout_novel_tiles(event)

    def create_chapter_list_tab(self, tab_text, lang_key):
        frame = ttk.Frame(self.chapter_notebook)
        grid = GridChapterList(frame, callback=self.load_chapter_from_list, item_width=210, item_height=42)
        self.chapter_lists[lang_key] = grid
        return frame

    # --- Tema ve Kontrol İşlemleri ---

    # ---------------- DOWNLOAD / TRANSLATION ----------------
    def _load_downloader(self):
        if self.downloader is not None:
            return self.downloader
        if not os.path.exists(DOWNLOADER_FILE):
            raise FileNotFoundError(f"Downloader bulunamadı: {DOWNLOADER_FILE}")
        spec = importlib.util.spec_from_file_location("novel_downloader_embedded", DOWNLOADER_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.downloader = module
        return module

    def _app_novel_dir(self, novel_name):
        return os.path.join(self.novels_path, novel_name)

    def refresh_download_list(self):
        try:
            self.download_tree.delete(*self.download_tree.get_children())
            if not os.path.isdir(self.novels_path):
                return
            for name in sorted(os.listdir(self.novels_path), key=str.lower):
                path = os.path.join(self.novels_path, name)
                if not os.path.isdir(path):
                    continue
                en_dir = os.path.join(path, 'en')
                tr_dir = os.path.join(path, 'tr')
                if not os.path.isdir(en_dir):
                    continue
                downloaded = len([f for f in os.listdir(en_dir) if f.startswith('chapter_') and f.endswith('.txt')])
                translated = len([f for f in os.listdir(tr_dir) if f.startswith('chapter_') and f.endswith('.txt')]) if os.path.isdir(tr_dir) else 0
                untranslated = max(0, downloaded - translated)
                total = 0
                progress_file = os.path.join(path, 'progress.json')
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        total = int(json.load(f).get('total_chapters', 0) or 0)
                except Exception:
                    pass
                self.download_tree.insert('', 'end', iid=name, values=(name, downloaded, total or '?', untranslated))
        except Exception as e:
            self.download_status_var.set(f'Downloads listesi okunamadı: {e}')

    def _selected_download_novel(self):
        selected = self.download_tree.selection()
        if not selected:
            messagebox.showinfo("Bilgi", "Önce bir novel seçin.")
            return None
        return selected[0]

    def start_new_download(self):
        url = self.download_url_var.get().strip()
        if not url:
            messagebox.showwarning("Eksik bilgi", "İlk bölüm URL'sini girin.")
            return
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            messagebox.showwarning("Hatalı URL", "Geçerli bir http/https URL girin.")
            return
        try:
            limit = max(0, int(self.download_limit_var.get().strip() or "0"))
        except ValueError:
            limit = 0
            self.download_limit_var.set("0")
        self._start_download_worker(url=url, limit=limit, resume=False)

    def resume_selected_download(self):
        novel = self._selected_download_novel()
        if not novel:
            return
        path = self._app_novel_dir(novel)
        try:
            dl = self._load_downloader()
            progress = dl.load_progress(path)
            url = progress.get("current_url")
            if not url or url == "N/A" or str(url).lower() == "final":
                messagebox.showinfo("Bilgi", "Bu novel için devam edilecek bir indirme konumu bulunamadı.")
                return
            try:
                limit = max(0, int(self.download_limit_var.get().strip() or "0"))
            except ValueError:
                limit = 0
            self._start_download_worker(url=url, limit=limit, resume=True, novel_name=novel)
        except Exception as e:
            messagebox.showerror("Hata", f"İndirme devam ettirilemedi:\n{e}")

    def _start_download_worker(self, url, limit=0, resume=False, novel_name=None):
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showinfo("Bilgi", "Zaten arka planda çalışan bir indirme var.")
            return
        try:
            dl = self._load_downloader()
        except Exception as e:
            messagebox.showerror("Downloader", str(e))
            return
        self.download_control = dl.Control()
        self.download_mode = "download"
        self.download_current_novel = novel_name
        self.download_status_var.set("İndirme başlatılıyor...")
        self.download_progress_var.set("")
        self.download_progressbar.stop()
        self.download_progressbar.config(mode="determinate", value=0)
        self._append_download_activity(f"{novel_name or 'Yeni novel'} — işlem başlatıldı")
        self.download_thread = threading.Thread(
            target=self._download_worker, args=(dl, url, limit, resume, novel_name), daemon=True
        )
        self.download_thread.start()

    def _download_worker(self, dl, start_url, page_limit, resume, known_novel):
        try:
            if resume:
                novel_name = known_novel
                novel_dir = self._app_novel_dir(novel_name)
                progress = dl.load_progress(novel_dir)
                current_url = progress.get("current_url")
                chapter_number = int(progress.get("chapter_number", 1))
                total_chapters = int(progress.get("total_chapters", 0) or 0)
            else:
                soup = dl.fetch_page(start_url)
                if not soup:
                    raise RuntimeError("Başlangıç sayfası çekilemedi.")
                novel_name = dl.extract_novel_name(soup)
                safe_name = dl._clear_name(novel_name)
                novel_dir = os.path.join(self.novels_path, safe_name)
                os.makedirs(os.path.join(novel_dir, "en"), exist_ok=True)
                os.makedirs(os.path.join(novel_dir, "tr"), exist_ok=True)
                current_url = start_url
                chapter_number = 1
                total_chapters = dl.get_total_chapters(dl.find_novel_base_url(start_url))

            pages = 0
            while current_url and str(current_url).lower() != "final":
                if page_limit > 0 and pages >= page_limit:
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    break
                if self.download_control.stop_event.is_set():
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    break
                self.download_control.pause_event.wait()
                if self.download_control.stop_event.is_set():
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    break

                self._download_ui("durum", f"{novel_name} — Bölüm {chapter_number} indiriliyor")
                if total_chapters:
                    self._download_ui("percent", (chapter_number - 1) * 100.0 / total_chapters)
                    self._download_ui("progress", f"{chapter_number}/{total_chapters}")
                else:
                    self._download_ui("progress", f"{pages + 1}/{page_limit if page_limit else '∞'}")
                soup = dl.fetch_page(current_url)
                if not soup:
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    raise RuntimeError("Sayfa çekilemedi; mevcut konum kaydedildi.")
                content = dl.extract_novel_content(soup)
                if not content:
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    raise RuntimeError("Bölüm içeriği çıkarılamadı; mevcut konum kaydedildi.")
                if total_chapters:
                    self._download_ui("percent", chapter_number * 100.0 / total_chapters)
                if not dl.save_chapter(content, chapter_number, novel_dir):
                    dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    raise RuntimeError("Bölüm kaydedilemedi.")

                next_url = dl.find_next_page_url(soup, current_url)
                if not next_url:
                    dl.save_progress(novel_dir, chapter_number + 1, "Final", total_chapters)
                    break
                if next_url.lower() == current_url.lower():
                    dl.save_progress(novel_dir, chapter_number + 1, next_url, total_chapters)
                    break
                dl.save_progress(novel_dir, chapter_number, current_url, total_chapters)
                chapter_number += 1
                pages += 1
                current_url = next_url
                time.sleep(1)

            self._download_ui("done", f"İndirme tamamlandı: {novel_name}")
        except Exception as e:
            self._download_ui("done", f"İndirme durdu: {e}")
        finally:
            self._download_ui("refresh")
            self.download_control = None

    def _append_download_activity(self, message):
        if not hasattr(self, "download_activity"):
            return
        self.download_activity.config(state=tk.NORMAL)
        self.download_activity.insert(tk.END, message + "\n")
        self.download_activity.see(tk.END)
        self.download_activity.config(state=tk.DISABLED)

    def _download_ui(self, kind, value=""):
        def apply():
            if kind == "durum":
                self.download_status_var.set(value)
                self._append_download_activity(value)
            elif kind == "progress":
                self.download_progress_var.set(value)
            elif kind == "percent":
                try:
                    self.download_progressbar["value"] = max(0, min(100, float(value)))
                except Exception:
                    pass
            elif kind == "indeterminate":
                if value:
                    self.download_progressbar.config(mode="indeterminate")
                    self.download_progressbar.start(12)
                else:
                    self.download_progressbar.stop()
                    self.download_progressbar.config(mode="determinate")
            elif kind == "done":
                self.download_status_var.set(value)
                self.download_progress_var.set("")
                self.download_progressbar.stop()
                self.download_progressbar.config(mode="determinate")
                self._append_download_activity(value)
            elif kind == "refresh":
                self.refresh_download_list()
                self.load_novels_from_dir(initial_load=False)
        self.master.after(0, apply)

    def toggle_download_pause(self):
        if not self.download_control:
            return
        if self.download_control.pause_event.is_set():
            self.download_control.pause_event.clear()
            self.download_pause_var.set("Devam Et")
            self.download_status_var.set("İndirme duraklatıldı")
        else:
            self.download_control.pause_event.set()
            self.download_pause_var.set("Duraklat")
            self.download_status_var.set("İndirme devam ediyor")

    def stop_download(self):
        if self.download_control:
            self.download_control.request_stop()
            self.download_status_var.set("Durdurma talebi gönderildi...")

    def start_translation(self):
        novel = self._selected_download_novel()
        if not novel:
            messagebox.showinfo("Bilgi", "Önce çeviri yapılacak novel satırını seçin.")
            return
        if self.download_thread and self.download_thread.is_alive():
            messagebox.showinfo("Bilgi", "Önce çalışan indirme/çeviri işlemini tamamlayın veya durdurun.")
            return
        try:
            dl = self._load_downloader()
            items = dl.list_untranslated_chapters(self._app_novel_dir(novel))
            if not items:
                messagebox.showinfo("Bilgi", "Çevrilecek bölüm bulunamadı.")
                return

            # Eski downloader'ın kullandığı çeviri motorunu gerçekten kontrol et.
            if getattr(dl, "TRANSLATOR_BACKEND", None) is None:
                messagebox.showerror(
                    "Çeviri motoru yok",
                    "Google Translate kütüphanesi yüklenemedi.\n\n"
                    "Komut satırında şu komutu çalıştırın:\n"
                    "python -m pip install -U googletrans"
                )
                self.download_status_var.set("Çeviri motoru bulunamadı")
                return

            self.download_control = dl.Control()
            self.download_mode = "translation"
            self.download_progressbar.stop()
            self.download_progressbar.config(mode="determinate", maximum=100, value=0)
            self.download_progress_var.set(f"0/{len(items)}")
            self.download_status_var.set(f"{novel} — çeviri başlıyor...")
            self._append_download_activity(f"{novel} — {len(items)} çevrilmemiş bölüm bulundu")
            self.download_thread = threading.Thread(
                target=self._translation_worker, args=(dl, novel, items), daemon=True
            )
            self.download_thread.start()
        except Exception as e:
            messagebox.showerror("Hata", f"Çeviri başlatılamadı:\n{e}")

    def _translation_worker(self, dl, novel, items):
        # Her bölümü ayrı çağırıyoruz. Böylece arayüz, Google Translate bir bölüm
        # üzerinde uzun süre beklese bile hangi bölümde olduğunu gösterebilir.
        total = len(items)
        translated_total = 0
        novel_dir = self._app_novel_dir(novel)
        try:
            self._download_ui("durum", f"{novel} — çeviri başladı ({total} bölüm)")

            for i, item in enumerate(items, 1):
                if self.download_control.stop_event.is_set():
                    self._download_ui("done", f"Çeviri durduruldu: {translated_total}/{total}")
                    return

                self.download_control.pause_event.wait()
                if self.download_control.stop_event.is_set():
                    self._download_ui("done", f"Çeviri durduruldu: {translated_total}/{total}")
                    return

                chapter_num, filename = item
                percent = ((i - 1) / total) * 100.0
                self._download_ui("percent", percent)
                self._download_ui("progress", f"{i}/{total}")
                self._download_ui("durum", f"{novel} — Bölüm {chapter_num} çevriliyor")

                # Downloader'ın kendi çeviri fonksiyonunu koruyoruz; sadece bir
                # bölüm vererek GUI'ye bölüm bazında ilerleme aktarabiliyoruz.
                result = dl.translate_chapters(
                    novel_dir, [item], self.download_control, 0, 1
                )
                if result == -1:
                    self._download_ui("done", f"Çeviri durduruldu: {translated_total}/{total}")
                    return
                if result and result > 0:
                    translated_total += result
                    self._download_ui("percent", (i / total) * 100.0)
                    self._download_ui("progress", f"{i}/{total}")
                    self._download_ui("durum", f"Bölüm {chapter_num} tamamlandı ({translated_total}/{total})")
                else:
                    self._download_ui("durum", f"Bölüm {chapter_num} çevrilemedi, sonraki bölüme geçiliyor")

            self._download_ui("percent", 100)
            self._download_ui("done", f"Çeviri tamamlandı: {novel} ({translated_total}/{total} bölüm)")
        except Exception as e:
            self._download_ui("done", f"Çeviri durdu: {e}")
        finally:
            self._download_ui("refresh")
            self.download_control = None

    def open_selected_novel(self, event=None):
        novel = self._selected_download_novel()
        if not novel:
            return
        self.select_novel_by_name(novel)

    def apply_theme(self, theme_name):
        theme = THEMES[theme_name]
        self.master.config(bg=theme['bg'])
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Download.Treeview", background=theme["list_bg"], foreground=theme["list_fg"], fieldbackground=theme["list_bg"])
        style.configure("TFrame", background=theme['bg'])
        style.configure("TLabel", background=theme['bg'], foreground=theme['fg'])
        style.configure("TButton", background=theme['button_bg'], foreground=theme['button_fg'])
        style.map('TButton', background=[('active', theme['highlight_bg'])])
        
        # Novel başlık etiketi için tema uygulama
        self.novel_title_label.config(background=theme['bg'], foreground=theme['fg'])
        
        self.text_area.config(bg=theme['text_bg'], fg=theme['text_fg'], insertbackground=theme['text_fg'])
        self.read_page_info_label.config(background=theme['bg'], foreground=theme['fg'])

        list_options = {'bg': theme['list_bg'], 'fg': theme['list_fg'], 'selectbackground': theme['highlight_bg'], 'selectforeground': theme['fg']}
        self.novel_canvas.config(bg=theme['list_bg'])
        for lb in self.chapter_lists.values():
            lb.config(**list_options)
        if hasattr(self, 'download_tree'):
            style.configure('Download.Treeview', background=theme['list_bg'], foreground=theme['list_fg'], fieldbackground=theme['list_bg'])
        
        style.configure("TNotebook", background=theme['bg'])
        style.configure("TNotebook.Tab", background=theme['button_bg'], foreground=theme['button_fg'])
        style.map("TNotebook.Tab", background=[('selected', theme['highlight_bg'])], foreground=[('selected', theme['fg'])])

        self.current_theme = theme_name
        self.state['theme'] = theme_name
        
        if hasattr(self, "download_tree"):
            self.download_tree.configure(style="Download.Treeview")

    def toggle_theme(self):
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme(new_theme)
        self.state['theme'] = new_theme
        self.save_state(silent=True)
        
    # --- Klavye Kısayolları İşlemi ---
    def on_key_press(self, event):
        # Sadece "Okuyucu" sekmesi seçiliyken ve bir bölüm açıkken çalışsın.
        if self.main_notebook.index(self.main_notebook.select()) != 3 or not self.current_chapter_file:
            return

        key = event.keysym

        # Bölümler arasında geçiş
        if key == 'Right':
            # Sağ ok tuşu: İleri
            self.change_chapter(1)
            return

        if key == 'Left':
            # Sol ok tuşu: Geri
            self.change_chapter(-1)
            return

        # Dikey kaydırma çubuğunu hareket ettirme
        # Ok tuşlarına hassas kaydırma ataması
        scroll_amount = 5 # Kaç satır kaydırılacağı

        if key == 'Down':
            # Aşağı ok tuşu
            self.text_area.yview_scroll(scroll_amount, "units")
            return

        if key == 'Up':
            # Yukarı ok tuşu
            self.text_area.yview_scroll(-scroll_amount, "units")
            return

        if key == 'Prior': # Page Up
            # Sayfa Yukarı tuşu
            self.text_area.yview_scroll(-1, "pages")
            return

        if key == 'Next': # Page Down
            # Sayfa Aşağı tuşu
            self.text_area.yview_scroll(1, "pages")
            return
            
    
    def toggle_read_controls(self, is_reading):
        """Okuma modunda sayfalama butonlarını açar/kapatır."""
        state = tk.NORMAL if is_reading else tk.DISABLED
        self.prev_page_button.config(state=state)
        self.next_page_button.config(state=state)
        if not is_reading:
            self.read_page_info_label.config(text="Bölüm Açılmadı")
            self.novel_title_label.config(text="Novel Seçilmedi") # Novel Seçilmedi
            self.current_novel = None


    # --- Novel Listeleme ve Yükleme İşlemleri (Aynı Kaldı) ---
    def select_novels_dir(self):
        new_dir = filedialog.askdirectory(title="Romanların bulunduğu 'novels' klasörünü seçin")
        if new_dir:
            self.novels_path = new_dir
            self.load_novels_from_dir(initial_load=True)

    def refresh_novels(self):
        current = self.current_novel
        self.load_novels_from_dir(initial_load=False)
        self.refresh_download_list()
        if current in self.novel_data:
            self.select_novel_by_name(current, open_reader=False)

    @staticmethod
    def natural_sort_key(value):
        return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", value)]

    def load_novels_from_dir(self, initial_load=False):
        self.novel_data = {}
        if not os.path.isdir(self.novels_path):
            os.makedirs(self.novels_path, exist_ok=True)

        try:
            names = os.listdir(self.novels_path)
        except OSError as e:
            messagebox.showerror("Hata", f"Novel klasörü okunamadı:\n{e}")
            return

        for name in names:
            path = os.path.join(self.novels_path, name)
            if not os.path.isdir(path):
                continue
            data = {"en": [], "tr": [], "path": path}
            for lang in ("en", "tr"):
                lang_dir = os.path.join(path, lang)
                if os.path.isdir(lang_dir):
                    data[lang] = sorted(
                        [f for f in os.listdir(lang_dir) if f.lower().endswith(".txt")],
                        key=self.natural_sort_key
                    )
            if data["en"] or data["tr"]:
                self.novel_data[name] = data

        self.display_novel_list()
        if initial_load:
            self.load_last_read()

    def display_novel_list(self):
        for child in self.novel_tiles_frame.winfo_children():
            child.destroy()
        names = sorted(self.novel_data.keys(), key=str.lower)
        self.novel_count_label.config(text=f"{len(names)} novel")
        for i, name in enumerate(names):
            data = self.novel_data[name]
            card = ttk.Frame(self.novel_tiles_frame, relief="ridge", padding=8)
            card.configure(width=240, height=120)
            card.grid_propagate(False)
            title = ttk.Label(card, text=name, font=("Arial", 11, "bold"), wraplength=220)
            title.pack(fill="x", anchor="w")
            ttk.Label(card, text=f"EN: {len(data['en'])}    TR: {len(data['tr'])}").pack(anchor="w", pady=(8, 3))
            ttk.Button(card, text="Aç", command=lambda n=name: self.select_novel_by_name(n)).pack(side=tk.BOTTOM, anchor="e")
            card.bind("<Double-Button-1>", lambda e, n=name: self.select_novel_by_name(n))
            title.bind("<Double-Button-1>", lambda e, n=name: self.select_novel_by_name(n))
        self.master.after_idle(self._relayout_novel_tiles)

    def select_novel_by_name(self, novel_name, open_reader=True):
        if novel_name not in self.novel_data:
            return
        self.current_novel = novel_name
        self.novel_title_label.config(text=novel_name)
        self.update_chapter_list_boxes()

        progress = self.state.get("novel_progress", {}).get(novel_name, {})
        if progress:
            parts = progress.get("key", "").split("/", 2)
            if len(parts) == 3:
                _, lang, chapter = parts
                lb = self.chapter_lists.get(lang)
                if lb and chapter in lb.get(0, tk.END):
                    idx = list(lb.get(0, tk.END)).index(chapter)
                    self.chapter_notebook.select(0 if lang == "en" else 1)
                    lb.selection_clear(0, tk.END); lb.selection_set(idx); lb.activate(idx); lb.see(idx)
                    self.current_language = lang
                    if open_reader:
                        self.load_chapter_from_list(None)
                    return

        for lang in ("tr", "en"):
            chapters = self.novel_data[novel_name].get(lang, [])
            if chapters:
                lb = self.chapter_lists[lang]
                self.chapter_notebook.select(0 if lang == "en" else 1)
                lb.selection_clear(0, tk.END); lb.selection_set(0); lb.activate(0); lb.see(0)
                self.current_language = lang
                if open_reader:
                    self.load_chapter_from_list(None)
                return
        self.clear_reader_and_controls()

    def on_chapter_tab_change(self, event=None):
        """Bölüm dili sekmesi değiştiğinde mevcut novelin bölüm listesini yeniler."""
        if self.current_novel:
            self.update_chapter_list_boxes()

    def on_novel_select(self, event):
        # Eski Listbox uyumluluğu; yeni arayüzde kartlar kullanılıyor.
        return

    def update_chapter_list_boxes(self):
        if not self.current_novel:
            return
        for lang, lb in self.chapter_lists.items():
            chapters = self.novel_data.get(self.current_novel, {}).get(lang, [])
            if chapters:
                lb.set_items(chapters)
            else:
                lb.set_items([f"'{self.current_novel}' için {lang.upper()} bölümü yok."])

    def get_current_list_and_language(self):
        """Aktif Listbox ve dil anahtarını döndürür."""
        try:
            selected_tab_text = self.chapter_notebook.tab(self.chapter_notebook.select(), "text")
        except tk.TclError:
             return None, None, None
             
        if 'Orijinal' in selected_tab_text:
            lang_key = 'en'
        elif 'Çeviri' in selected_tab_text:
            lang_key = 'tr'
        else:
            return None, None, None

        listbox = self.chapter_lists.get(lang_key)
        return listbox, lang_key, self.novel_data.get(self.current_novel, {}).get(lang_key, [])


    def load_chapter_from_list(self, event):
        """Sağdaki listeden çift tıklama (veya on_novel_select) ile bölümü yükler."""
        listbox, lang_key, chapter_list = self.get_current_list_and_language()
        
        if not listbox or not self.current_novel:
            return

        try:
            selected_index_tuple = listbox.curselection()
            if not selected_index_tuple:
                return
            selected_index = selected_index_tuple[0]
            chapter_file = listbox.get(selected_index)
            if "bölümü yok" in chapter_file:
                return
        except IndexError:
            return

        # Yüklemeden önce, eğer farklı bir bölüm açıksa, o bölümün pozisyonunu kaydet (sadece bölüm bilgisi).
        if self.current_novel and self.current_chapter_file and self.current_chapter_file != chapter_file:
            self.save_state(silent=True) 

        # Yeni bölümü state'e set et
        self.current_chapter_file = chapter_file
        self.current_language = lang_key
        self.novel_title_label.config(text=self.current_novel) # Üstteki etiketi güncelle
        
        base_path = self.novel_data[self.current_novel]['path']
        dir_name = self.current_language 
        file_path = os.path.join(base_path, dir_name, chapter_file)

        # Pozisyonu state'den al (Artık her zaman 0.0)
        scroll_pos = 0.0 
        
        # Kayıtlı ilerleme kontrolü (sadece doğru bölüm olup olmadığını anlamak için gerekli)
        novel_progress = self.state.get('novel_progress', {})
        progress_to_load = novel_progress.get(self.current_novel)
        
        if progress_to_load:
            key_to_load = progress_to_load.get("key")
            full_key = f"{self.current_novel}/{self.current_language}/{self.current_chapter_file}"
            
            # Eğer yüklemeye çalıştığımız bölüm, kayıtlı "son bölüm" ise, pozisyon yine 0.0 olarak kalır.
            if key_to_load == full_key:
                scroll_pos = 0.0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_content = f.read()
            
            self.main_notebook.select(self.reader_tab)
            # Pozisyonu gönder (her zaman 0.0)
            self.display_full_chapter(self.current_content, scroll_pos)
            self.toggle_read_controls(True)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Bölüm yüklenirken hata oluştu: {e}")
            self.current_chapter_file = None
            self.current_language = None
            self.toggle_read_controls(False)

    def change_chapter(self, direction):
        """Okuma alanındaki butonlarla bir sonraki/önceki bölüme geçer."""
        if not self.current_novel or not self.current_chapter_file or not self.current_language:
            return

        current_chapter_list = self.novel_data.get(self.current_novel, {}).get(self.current_language, [])
        if not current_chapter_list:
            return

        try:
            current_index = current_chapter_list.index(self.current_chapter_file)
        except ValueError:
            return

        new_index = current_index + direction
        
        if 0 <= new_index < len(current_chapter_list):
            self.save_state(silent=True) # Önceki bölümün pozisyonunu kaydet
            
            # Sadece listedeki seçimi değiştir ve yüklemeyi tetikle
            listbox = self.chapter_lists.get(self.current_language)
            if listbox:
                listbox.selection_clear(0, tk.END)
                listbox.selection_set(new_index)
                listbox.activate(new_index)
                listbox.see(new_index) 
                
                # Seçimi yükle (load_chapter_from_list'in event'i None)
                self.load_chapter_from_list(None) 
            
        else:
            messagebox.showinfo("Bilgi", "Başka bölüm bulunamadı.")
            
    # --- Tam Bölüm Gösterimi ---
    def display_full_chapter(self, content, scroll_pos=0.0):
        """Okuma alanına tam bölüm içeriğini yükler ve belirtilen pozisyona kaydırır."""
        self.text_area.config(state=tk.NORMAL) 
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, content)
        self.text_area.config(state=tk.DISABLED)
        
        # Kayıtlı pozisyona git (Artık her zaman 0.0 olacak)
        self.text_area.yview_moveto(scroll_pos)
        
        self.read_page_info_label.config(text=f"Bölüm: {self.current_chapter_file} | Dil: {self.current_language.upper()} (Tam)")
        
        self.prev_page_button.config(text="<< Geri", state=tk.NORMAL) 
        self.next_page_button.config(text="İleri >>", state=tk.NORMAL) 

    # --- YENİ YARDIMCI FONKSİYON ---
    def clear_reader_and_controls(self):
        """Okuma alanını temizler ve butonları devre dışı bırakır."""
        self.text_area.config(state=tk.NORMAL) 
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)
        self.toggle_read_controls(False)
        self.current_chapter_file = None
        self.current_language = None


    # --- Durum Kaydetme/Yükleme İşlemleri (Aynı Kaldı) ---
    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_state(self, silent=False):
        
        # Sadece tema değişimi veya uygulama kapanışı gibi durumlarda (bölüm açık değilken) kaydet
        if not (self.current_novel and self.current_chapter_file and self.current_language):
            # Sadece temayı kaydet (eğer değiştiyse)
            try:
                self.state['theme'] = self.current_theme
                if self.current_novel:
                    self.state['last_viewed_novel'] = self.current_novel
                with open(STATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.state, f, indent=4)
            except Exception:
                pass
            return

        # Scroll pozisyonu kaydı devre dışı bırakıldı.
        scroll_pos = 0.0 
        
        # O novel için yeni ilerleme verisi
        progress_data = {
            "key": f"{self.current_novel}/{self.current_language}/{self.current_chapter_file}",
            "scroll_pos": scroll_pos # Her zaman 0.0 olarak kaydedilecek
        }
        
        # Ana ilerleme listesini al veya oluştur
        novel_progress = self.state.get('novel_progress', {})
        
        # O novele ait kaydı GÜNCELLE
        novel_progress[self.current_novel] = progress_data
        
        # State'e geri yaz
        self.state['novel_progress'] = novel_progress
        self.state['last_viewed_novel'] = self.current_novel # Uygulama açılışı için
        self.state['theme'] = self.current_theme
        
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                # Pozisyonun float olarak doğru yazıldığından emin ol
                json.dump(self.state, f, indent=4)
            if not silent:
                messagebox.showinfo("Bilgi", "Okuma durumu başarıyla kaydedildi.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Hata", f"Okuma durumu kaydedilemedi: {e}")

    def load_last_read(self):
        novel_name = self.state.get("last_viewed_novel")
        if novel_name and novel_name in self.novel_data:
            self.select_novel_by_name(novel_name)


    def on_closing(self):
        self.save_state(silent=True)
        if self.download_control:
            self.download_control.request_stop()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NovelReaderApp(root)
    root.mainloop()
