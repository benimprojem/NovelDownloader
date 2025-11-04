############################################
# NovelDovnloader.py için NovelReader.py
# ver. 0.9.5
# 30.10.2025
# Pdf çevirici gelecekte eklenecek. 
#   pdf çevirici her 100 sayfayı gruplandırıp tek kitap olarak kaydetmek için kullanılacak.
# Halen hataları ve eksikleri olabilir. Gğrdüğüm tüm hatalrı gidermeye çalıştım.
# Optimize edilmemiştir. İçerisinde halen gereksiz veya fazladan kod bulunabilir..
# Fikir: Dissconnectted.  Kodlayan: Gemini. :)
# 
#############################################
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from math import ceil

# --- Sabitler ve Ayarlar ---
NOVELS_DIR = "novels"
STATE_FILE = "readnovel_state.json"
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

class NovelReaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Read Novel")
        master.geometry("1144x600")

        self.novels_path = NOVELS_DIR
        self.novel_data = {}  
        self.current_novel = None
        self.current_chapter_file = None
        self.current_language = None 
        
        self.current_content = []  
        self.chapter_lists = {} 
        self.current_chapters_list = [] 
        
        self.state = self.load_state()
        self.current_theme = self.state.get('theme', 'light')
        
        self.setup_ui()
        self.apply_theme(self.current_theme)
        # load_novels_from_dir, novel listesini doldurur ve load_last_read'i tetikler
        self.load_novels_from_dir(initial_load=True) 
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # --- ANA YAPININ KURULUMU ---
        self.top_controls_frame = ttk.Frame(self.master)
        self.top_controls_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # 1. Okunan novelin adını gösteren etiket
        self.novel_title_label = ttk.Label(self.top_controls_frame, text="Novel Seçilmedi", font=("Arial", 14, "bold"))
        self.novel_title_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        # Sağ tarafa yaslı butonlar için çerçeve
        self.button_align_frame = ttk.Frame(self.top_controls_frame)
        self.button_align_frame.pack(side=tk.RIGHT)
        
        ttk.Button(self.button_align_frame, text="Novel", command=self.select_novels_dir).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_align_frame, text="Kaydet", command=lambda: self.save_state(silent=False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_align_frame, text="⭐", command=self.toggle_theme).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.button_align_frame, text="PDF", command=lambda: messagebox.showinfo("Bilgi", "PDF özelliği şimdilik işlevsel değil.")).pack(side=tk.LEFT, padx=2)
        
        self.content_frame = ttk.Frame(self.master)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        self.content_frame.grid_columnconfigure(0, weight=5) 
        self.content_frame.grid_columnconfigure(1, weight=2) 
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.left_frame = ttk.Frame(self.content_frame, relief=tk.SUNKEN)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 5)) 
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.left_notebook = ttk.Notebook(self.left_frame)
        self.left_notebook.grid(row=0, column=0, sticky="nsew")

        # 1. Sekme: Novel Listesi
        self.novel_list_tab = ttk.Frame(self.left_notebook)
        self.left_notebook.add(self.novel_list_tab, text="Novel Listesi")
        self.novel_list_tab.grid_rowconfigure(0, weight=1)
        self.novel_list_tab.grid_columnconfigure(0, weight=1)
        
        self.novel_list_scrollbar = ttk.Scrollbar(self.novel_list_tab)
        self.novel_list_scrollbar.grid(row=0, column=1, sticky="ns")

        self.novel_list_box = tk.Listbox(self.novel_list_tab, exportselection=False, font=("Arial", 11), yscrollcommand=self.novel_list_scrollbar.set, highlightthickness=0)
        self.novel_list_box.grid(row=0, column=0, sticky="nsew")
        self.novel_list_box.bind('<<ListboxSelect>>', self.on_novel_select)
        
        self.novel_list_scrollbar.config(command=self.novel_list_box.yview)
        
        # 2. Sekme: Okuyucu
        self.reader_tab = ttk.Frame(self.left_notebook)
        self.left_notebook.add(self.reader_tab, text="Okuyucu")
        self.reader_tab.grid_rowconfigure(0, weight=1)
        self.reader_tab.grid_columnconfigure(0, weight=1)
        
        self.text_area_scrollbar = ttk.Scrollbar(self.reader_tab)
        self.text_area_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.text_area = tk.Text(self.reader_tab, wrap=tk.WORD, font=("Arial", 13), state=tk.DISABLED, yscrollcommand=self.text_area_scrollbar.set, padx=20,pady=20)
        self.text_area.grid(row=0, column=0, sticky="nsew")
        
        self.text_area_scrollbar.config(command=self.text_area.yview)
        
        # Sol Alt Kontrol Çubuğu
        self.bottom_controls_left = ttk.Frame(self.left_frame)
        self.bottom_controls_left.grid(row=1, column=0, sticky="ew", pady=5)
        self.bottom_controls_left.grid_columnconfigure(0, weight=1)
        self.bottom_controls_left.grid_columnconfigure(1, weight=1)
        self.bottom_controls_left.grid_columnconfigure(2, weight=1)

        self.read_page_info_label = ttk.Label(self.bottom_controls_left, text="Bölüm Açılmadı")
        self.read_page_info_label.grid(row=0, column=1, padx=10)

        self.prev_page_button = ttk.Button(self.bottom_controls_left, text="<< Geri", command=lambda: self.change_chapter(-1))
        self.prev_page_button.grid(row=0, column=0, sticky="w", padx=(5, 0))

        self.next_page_button = ttk.Button(self.bottom_controls_left, text="İleri >>", command=lambda: self.change_chapter(1))
        self.next_page_button.grid(row=0, column=2, sticky="e", padx=(0, 5))
        
        self.toggle_read_controls(False)

        # --- Sağ Bölüm (Sekmeli Bölüm Listesi) ---
        self.right_frame = ttk.Frame(self.content_frame, relief=tk.RAISED)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.right_frame.grid_rowconfigure(0, weight=1) 
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Bölüm Listesi Sekmeleri
        self.chapter_notebook = ttk.Notebook(self.right_frame)
        self.chapter_notebook.grid(row=0, column=0, sticky="nsew")
        self.chapter_notebook.bind('<<NotebookTabChanged>>', self.on_chapter_tab_change) 
        
        self.original_tab = self.create_chapter_list_tab("Orijinal (en)", 'en')
        self.chapter_notebook.add(self.original_tab, text="Orijinal (en)")

        self.translation_tab = self.create_chapter_list_tab("Çeviri (tr)", 'tr')
        self.chapter_notebook.add(self.translation_tab, text="Çeviri (tr)")

        self.pdf_tab = ttk.Frame(self.chapter_notebook)
        ttk.Label(self.pdf_tab, text="PDF özelliği henüz aktif değil.").pack(pady=20)
        self.chapter_notebook.add(self.pdf_tab, text="PDF")


    def create_chapter_list_tab(self, tab_text, lang_key):
        """Sağdaki her bir dil sekmesi için Listbox ve Scrollbar oluşturur."""
        frame = ttk.Frame(self.chapter_notebook)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.grid(row=0, column=1, sticky="ns")

        listbox = tk.Listbox(frame, exportselection=False, yscrollcommand=scrollbar.set, highlightthickness=0)
        listbox.grid(row=0, column=0, sticky="nsew")
        listbox.bind('<Double-1>', self.load_chapter_from_list)
        
        scrollbar.config(command=listbox.yview)
        
        self.chapter_lists[lang_key] = listbox # Listbox referansını kaydet
        return frame


    # --- Tema ve Kontrol İşlemleri ---
    def apply_theme(self, theme_name):
        theme = THEMES[theme_name]
        self.master.config(bg=theme['bg'])
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TFrame", background=theme['bg'])
        style.configure("TLabel", background=theme['bg'], foreground=theme['fg'])
        style.configure("TButton", background=theme['button_bg'], foreground=theme['button_fg'])
        style.map('TButton', background=[('active', theme['highlight_bg'])])
        
        # Novel başlık etiketi için tema uygulama
        self.novel_title_label.config(background=theme['bg'], foreground=theme['fg'])
        
        self.text_area.config(bg=theme['text_bg'], fg=theme['text_fg'], insertbackground=theme['text_fg'])
        self.read_page_info_label.config(background=theme['bg'], foreground=theme['fg'])

        list_options = {'bg': theme['list_bg'], 'fg': theme['list_fg'], 'selectbackground': theme['highlight_bg'], 'selectforeground': theme['fg']}
        self.novel_list_box.config(**list_options)
        
        for lb in self.chapter_lists.values():
            lb.config(**list_options)
        
        style.configure("TNotebook", background=theme['bg'])
        style.configure("TNotebook.Tab", background=theme['button_bg'], foreground=theme['button_fg'])
        style.map("TNotebook.Tab", background=[('selected', theme['highlight_bg'])], foreground=[('selected', theme['fg'])])

        self.current_theme = theme_name
        self.state['theme'] = theme_name
        
    def toggle_theme(self):
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme(new_theme)
        self.state['theme'] = new_theme
        self.save_state(silent=True)
        
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

    def load_novels_from_dir(self, initial_load=False):
        self.novel_data = {}
        if not os.path.exists(self.novels_path):
            if initial_load:
                self.novel_list_box.delete(0, tk.END)
                self.novel_list_box.insert(tk.END, f"'{self.novels_path}' klasörü bulunamadı.")
                self.novel_list_box.insert(tk.END, "Lütfen 'Novel' butonu ile seçin.")
                for lb in self.chapter_lists.values():
                    lb.delete(0, tk.END)
            return

        for novel_name in os.listdir(self.novels_path):
            novel_path = os.path.join(self.novels_path, novel_name)
            if os.path.isdir(novel_path):
                en_chapters = []
                tr_chapters = []
                en_dir = os.path.join(novel_path, 'en')
                if os.path.isdir(en_dir):
                    en_chapters = sorted([f for f in os.listdir(en_dir) if f.endswith('.txt')])
                tr_dir = os.path.join(novel_path, 'tr')
                if os.path.isdir(tr_dir):
                    tr_chapters = sorted([f for f in os.listdir(tr_dir) if f.endswith('.txt')])
                    
                if en_chapters or tr_chapters: 
                     self.novel_data[novel_name] = {
                        'en': en_chapters,
                        'tr': tr_chapters,
                        'path': novel_path
                    }

        self.display_novel_list()
        
        if initial_load:
            self.left_notebook.select(self.novel_list_tab) 
            self.load_last_read()


    def display_novel_list(self):
        """Novel Listesi sekmesini günceller."""
        self.novel_list_box.delete(0, tk.END)

        sorted_novel_names = sorted(self.novel_data.keys())

        for novel_name in sorted_novel_names:
            data = self.novel_data[novel_name]
            en_count = len(data['en'])
            tr_count = len(data['tr'])
            display_text = f"{novel_name} ({en_count} / {tr_count})"
            self.novel_list_box.insert(tk.END, display_text)

    def on_chapter_tab_change(self, event):
        """Sağdaki bölüm listesi sekmeleri değiştiğinde listeyi günceller."""
        if self.current_novel:
            self.update_chapter_list_boxes()

    def on_novel_select(self, event):
        """Novel listesinde bir seçim yapıldığında sağdaki bölüm listelerini günceller VE O NOVELE AİT SON OKUNAN BÖLÜMÜ YÜKLER."""
        try:
            selected_index_tuple = self.novel_list_box.curselection()
            if not selected_index_tuple:
                return
            selected_index = selected_index_tuple[0]
            selected_item = self.novel_list_box.get(selected_index)
            novel_name = selected_item.split(' (')[0]
        except IndexError:
            return
        
        # Eğer zaten seçili olan novel (ve bir bölüm açıksa) tekrar seçilirse (örn. liste tazelendi)
        if novel_name == self.current_novel and self.current_chapter_file:
             self.update_chapter_list_boxes()
             return

        self.current_novel = novel_name
        self.novel_title_label.config(text=novel_name) # Üstteki etiketi güncelle
        self.update_chapter_list_boxes() # Bu, sağdaki listeleri doldurur
        
        # --- Novel için kayıtlı ilerlemeyi yükleme (Restart sırasında veya manuel seçildiğinde) ---
        novel_progress = self.state.get('novel_progress', {})
        progress_to_load = novel_progress.get(novel_name)

        if progress_to_load:
            try:
                key_to_load = progress_to_load.get("key")
                if not key_to_load:
                    self.clear_reader_and_controls()
                    return

                # Anahtardan bilgileri ayır: "NovelAdı/dil/bölüm.txt"
                _novel_name, language, chapter_file = key_to_load.split('/')
                
                # Doğru dil sekmesini seç (en=0, tr=1)
                tab_id = 0 if language == 'en' else 1
                self.chapter_notebook.select(tab_id)
                
                listbox = self.chapter_lists.get(language)
                
                # Bölüm, listede mevcut mu kontrol et
                if listbox and chapter_file in list(listbox.get(0, tk.END)):
                    chap_idx = list(listbox.get(0, tk.END)).index(chapter_file)
                    
                    # O bölümü listede seçili hale getir
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(chap_idx)
                    listbox.activate(chap_idx)
                    listbox.see(chap_idx)
                    
                    # current_language'i load_chapter_from_list'ten önce ayarlayın.
                    self.current_language = language 
                    
                    # Seçili bölümü yüklemek için ana fonksiyonu çağır
                    self.load_chapter_from_list(None)
                else:
                    self.clear_reader_and_controls()
                    
            except Exception as e:
                print(f"on_novel_select içinde son bölüm yüklenirken hata: {e}")
                self.clear_reader_and_controls()
        else:
            # Bu novel için kayıtlı bir "son okunan" bölüm yoksa, okuyucuyu temizle
            # self.clear_reader_and_controls() # TEMİZLEME YERİNE İLK BÖLÜMÜ YÜKLE
            
            # YENİ EKLENTİ: Eğer kayıtlı ilerleme yoksa, TR sekmesindeki ilk bölümü otomatik yükle
            tr_chapters = self.novel_data.get(novel_name, {}).get('tr', [])
            
            if tr_chapters:
                # 1. Çeviri (tr) sekmesini seç
                self.chapter_notebook.select(1) # 'tr' tabı 1. indexte (0=en, 1=tr)

                # 2. Listbox'ta ilk bölümü seç ve yükle
                listbox = self.chapter_lists.get('tr')
                if listbox:
                    first_chapter_index = 0
                    listbox.selection_clear(0, tk.END)
                    listbox.selection_set(first_chapter_index)
                    listbox.activate(first_chapter_index)
                    listbox.see(first_chapter_index)
                    
                    self.current_language = 'tr' 
                    self.load_chapter_from_list(None) # Bölümü yükle
            else:
                self.clear_reader_and_controls() # TR bölümü yoksa temizle
        
    def update_chapter_list_boxes(self):
        """Sağdaki tüm Bölüm Listesi sekme içeriklerini günceller."""
        if not self.current_novel:
            return

        for lang_key, listbox in self.chapter_lists.items():
            listbox.delete(0, tk.END)
            
            chapters = self.novel_data.get(self.current_novel, {}).get(lang_key, [])
            total_chapters = len(chapters)
            
            if total_chapters == 0:
                listbox.insert(tk.END, f"'{self.current_novel}' için {lang_key.upper()} bölümü yok.")
                continue

            for chapter in chapters:
                listbox.insert(tk.END, chapter)

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

        # YENİ KONTROL: Yüklemeden önce, eğer farklı bir bölüm açıksa, o bölümün pozisyonunu kaydet (sadece bölüm bilgisi).
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
            
            self.left_notebook.select(self.reader_tab)
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
                with open(STATE_FILE, 'r') as f:
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
                with open(STATE_FILE, 'w') as f:
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
            with open(STATE_FILE, 'w') as f:
                # Pozisyonun float olarak doğru yazıldığından emin ol
                json.dump(self.state, f, indent=4)
            if not silent:
                messagebox.showinfo("Bilgi", "Okuma durumu başarıyla kaydedildi.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Hata", f"Okuma durumu kaydedilemedi: {e}")

    def load_last_read(self):
        novel_name = self.state.get('last_viewed_novel')

        if not novel_name:
            return

        # Novel'in listede olduğundan emin ol
        if novel_name not in self.novel_data:
            return

        for i, item in enumerate(self.novel_list_box.get(0, tk.END)):
            # Tam eşleşen novel'i bul
            if item.startswith(novel_name):
                # Novel listesinde seçimi ayarla
                self.novel_list_box.selection_clear(0, tk.END)
                self.novel_list_box.selection_set(i)
                self.novel_list_box.activate(i)
                
                # Bu, otomatik olarak self.on_novel_select'i tetikleyecektir (event=None)
                # ve o da doğru bölümü ve pozisyonu yükleyecektir.
                self.on_novel_select(None) 
                break


    def on_closing(self):
        # Uygulama kapanırken son pozisyonu kaydet
        self.save_state(silent=True)
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NovelReaderApp(root)
    root.mainloop()
