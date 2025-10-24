import os
import time
import re
import json
import threading
import sys # İlerleme çubuğu için sys modülünü ekle
# Kütüphanelerin kurulu olup olmadığını kontrol et
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:   
    print("Gerekli kütüphaneler bulunamadı!")  
    print("Lütfen şu komutları çalıştırın:")  
    print(" pip install requests")  
    print(" pip install beautifulsoup4")    
    print(" pip install googletrans-py")   
    input("Devam etmek için Enter tuşuna basın...") 
    exit(1)
# Desteklenen diller ve kodları
source_lang = "en"
target_lang = "tr"
# Translator nesnesini global olarak tanımla
#translator = Translator()
def fetch_page(url):
    """Web sayfasını çeker ve BeautifulSoup nesnesi olarak döndürür."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTP hatalarını kontrol et
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Hata: Sayfa çekilemedi - {url}")
        print(f"Hata detayı: {e}")
        return None
def find_next_page_url(soup, current_url):
    ## Sonraki sayfa linkini bulur.
    try:
        # NovelBuddy.io sitesinin yeni yapısına göre sonraki sayfa linki 'btn-next' id'si ile
        next_link = soup.find('a', id='btn-next')
        
        if next_link and next_link.get('href'):
            # Göreceli URL'yi mutlak URL'ye dönüştür
            next_url = next_link['href']
            if next_url.startswith('/'):
                # Baz URL'yi çıkar
                base_url = '/'.join(current_url.split('/')[:3])
                next_url = base_url + next_url
            return next_url
        else:
            print("Sonraki sayfa linki bulunamadı. 'btn-next' id'si bulunamadı.")
        
        return None
    except Exception as e:
        print(f"Sonraki sayfa linki bulunurken hata oluştu: {e}")
        return None
def _clear_name(yazi):
    # Temizlenecek kelimeler (büyük/küçük harfe duyarsız)
    no_words = ['read', 'mtl', '-', 're:']
    
    # Tüm istenmeyen kelimeleri kaldır
    for word in no_words:
        yazi = yazi.lower().replace(word, '')
    
    # Özel karakterleri temizle ve baştaki/sondaki boşlukları al
    safe_name = re.sub(r'[\\/*?:"<>|]', "", yazi).strip()
    
    return safe_name
    
def create_novel_directory(novel_name):
    ##Novel için klasör oluşturur."""
    # Geçersiz dosya adı karakterlerini temizle
    safe_name = _clear_name(novel_name)
    
    # Mevcut çalışma dizinini göster
    current_dir = os.getcwd()
    print(f"Mevcut çalışma dizini: {current_dir}")
    
    # Çalışma klasörü içinde novels adıyla klasör oluştur
    novel_dir = os.path.join(current_dir, "novels", safe_name)
    # Klasör yolunu kısalt
    short_dir = os.path.join("novels", safe_name)
    print(f"Hedef klasör: .../{short_dir}")
    
    if not os.path.exists(novel_dir):
        os.makedirs(novel_dir)
        print(f"Klasör oluşturuldu: .../{short_dir}")
    else:
        print(f"Klasör zaten mevcut: .../{short_dir}")
    # en ve tr alt klasörlerini oluştur
    en_dir = os.path.join(novel_dir, "en")
    tr_dir = os.path.join(novel_dir, "tr")
    short_en = os.path.join("novels", safe_name, "en")
    short_tr = os.path.join("novels", safe_name, "tr")
    if not os.path.exists(en_dir):
        os.makedirs(en_dir)
        print(f"Klasör oluşturuldu: .../{short_en}")
    else:
        print(f"Klasör zaten mevcut: .../{short_en}")
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir)
        print(f"Klasör oluşturuldu: .../{short_tr}")
    else:
        print(f"Klasör zaten mevcut: .../{short_tr}")
    
    return novel_dir
def save_chapter(content, chapter_number, novel_dir):
    ##Bölüm içeriğini dosyaya kaydeder.
    if not content:
        return False
    
    # EN klasörüne kaydet
    en_dir = os.path.join(novel_dir, "en")
    file_path = os.path.join(en_dir, f"chapter_{chapter_number:04d}.txt")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        # Dosya yolunu kısalt
        short_path = os.path.join("en", os.path.basename(file_path))
        print(f"Bölüm {chapter_number} kaydedildi: .../{short_path}")
        return True
    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")
        return False
def extract_novel_content(soup):
    try:
        # Tüm HTML'yi metin olarak al
        html = soup.decode()
        # Çekilecek aralık işaretleri
        # INFOLINKS_ON ile INFOLINKS_OFF arasındaki içeriği eksiksiz alır.
        match = re.search(r'<!--\s*INFOLINKS_ON\s*-->(.*?)<!--\s*INFOLINKS_OFF\s*-->', html, re.DOTALL | re.IGNORECASE)
        if not match:
            print("INFOLINKS yorum aralığı bulunamadı.")
            return None
        
        inner_html = match.group(1)
        
        # İçeriği metne çevirirken satır sonlarını koru
        inner_soup = BeautifulSoup(inner_html, 'html.parser')
        for tag in inner_soup(['script', 'style']):
            tag.decompose()
        text = inner_soup.get_text(separator='\n')
        
        # Satır sonlarını ve boşlukları normalize et
        text = re.sub(r'\r\n?', '\n', text)
        # Fazla satır sonlarını temizle (3 veya daha fazla ardışık \n'i 2'ye düşür)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Fazla boşlukları temizle
        text = re.sub(r'[ \t]{2,}', ' ', text)
        # Satır başı ve sonundaki boşlukları temizle
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        # Birden fazla boş satırı tek boş satıra düşür
        text = re.sub(r'\n{2,}', '\n\n', text)
        
        cleaned = text.strip()
        print(f"İçerik uzunluğu: {len(cleaned)} karakter")
        return cleaned
    except Exception as e:
        print(f"İçerik çıkarılırken hata oluştu: {e}")
        return None
def extract_novel_name(soup):
    ##Sayfa başlığından novel adını çıkarır.
    try:
        # Başlık genellikle title etiketinde veya h1 içinde olur
        title = soup.title.string if soup.title else None
        
        if not title:
            title_elem = soup.find('h1')
            title = title_elem.get_text() if title_elem else "Bilinmeyen Novel"
        
        # Başlıktan gereksiz kısımları temizle
        title = re.sub(r' - Chapter \d+.*', '', title)
        title = re.sub(r' - Bölüm \d+.*', '', title)
        
        return title.strip()
    except Exception:
        return "Bilinmeyen Novel"
def save_progress(novel_dir, chapter_number, current_url):
    ##İlerlemeyi novel klasörüne progress.json olarak yazar.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        data = {
            "chapter_number": chapter_number,
            "current_url": current_url
        }
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # URL'yi kısaltarak göster
        short_url = current_url.split('/')[-1] if '/' in current_url else current_url
        if len(short_url) > 50:
            short_url = short_url[:47] + "..."
        print(f"İlerleme kaydedildi: bölüm={chapter_number}, url=.../{short_url}")
    except Exception as e:
        print(f"İlerleme kaydedilemedi: {e}")
def load_progress(novel_dir):
    ##Novel klasöründeki progress.json'ı okur.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        if os.path.exists(progress_path):
            with open(progress_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # URL'yi kısaltarak göster
            short_url = (data.get('current_url') or '')
            short_url = short_url.split('/')[-1] if '/' in short_url else short_url
            if len(short_url) > 50:
                short_url = short_url[:47] + "..."
            print(f"Mevcut ilerleme bulundu: bölüm={data.get('chapter_number')}, url=.../{short_url}")
            return data
    except Exception as e:
        print(f"İlerleme yüklenemedi: {e}")
        
        choice = input("Dil kodu veya numara girin: ").strip().lower()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(LANGUAGES):
                return list(LANGUAGES.keys())[idx]
        elif choice in LANGUAGES:
            return choice
        else:
            print("Geçersiz seçim. Lütfen geçerli bir dil kodu veya numara girin.")
try:
    from deep_translator import GoogleTranslator as DTTranslator
    TRANSLATOR_BACKEND = 'deep'
except Exception:
    DTTranslator = None
    try:
        from googletrans import Translator as GTTranslator
        TRANSLATOR_BACKEND = 'google'
    except Exception as e:
        GTTranslator = None
        TRANSLATOR_BACKEND = None
        print("Çeviri kütüphanesi bulunamadı.")
        print("Yüklemek için: py pip install deep-translator  veya  py -m pip install googletrans==4.0.0-rc1")
def translate_text_en_to_tr(text, control=None, source_lang='en', target_lang='tr', chapter_num=None):
    if TRANSLATOR_BACKEND is None:
        print("Çeviri yapılamıyor: kütüphane yüklü değil.")
        return None
    try:
        if TRANSLATOR_BACKEND == 'deep':
            translator = DTTranslator(source=source_lang, target=target_lang)
            if len(text) > 4500:
                chunks = _split_chunks(text)
                result = []
                for i, chunk in enumerate(chunks):
                    if control and control.stop_event.is_set():
                        print("Çeviri durduruldu.")
                        return None
                    if control and not control.pause_event.is_set():
                        print("Çeviri duraklatıldı. Devam etmek için 'R' tuşuna basın.")
                        control.pause_event.wait()
                    
                    sys.stdout.write(f"\rBölüm {chapter_num} - Parça {i + 1}/{len(chunks)} çevriliyor... ")
                    sys.stdout.flush()
                    try:
                        translated = translator.translate(chunk)
                    except Exception as e:
                        msg = str(e)
                        short = msg[-200:] if len(msg) > 200 else msg
                        print(f"Çeviri hatası (son 200): {short}")
                        translated = chunk  # Hata veren parçayı orijinal hâliyle ekle
                    
                    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
                    sys.stdout.flush()
                    result.append(translated)
                    time.sleep(1)
                return '\n'.join(result)
            else:
                try:
                    return translator.translate(text)
                except Exception as e:
                    msg = str(e)
                    short = msg[-200:] if len(msg) > 200 else msg
                    print(f"Çeviri hatası (son 200): {short}")
                    return text  # Tek parça hatasında orijinal metni döndür
        elif TRANSLATOR_BACKEND == 'google':
            # translator = GTTranslator() # Global translator nesnesini kullan
            if len(text) > 4500:
                chunks = _split_chunks(text)
                result = []
                for i, chunk in enumerate(chunks):
                    if control and control.stop_event.is_set():
                        print("Çeviri durduruldu.")
                        return None
                    if control and not control.pause_event.is_set():
                        print("Çeviri duraklatıldı. Devam etmek için 'R' tuşuna basın.")
                        control.pause_event.wait()
                    
                    sys.stdout.write(f"\rBölüm {chapter_num} - Parça {i + 1}/{len(chunks)} çevriliyor... ")
                    sys.stdout.flush()
                    try:
                        translated = translator.translate(chunk, src=source_lang, dest=target_lang).text
                    except Exception as e:
                        msg = str(e)
                        short = msg[-200:] if len(msg) > 200 else msg
                        print(f"Çeviri hatası (son 200): {short}")
                        translated = chunk  # Hata veren parçayı orijinal hâliyle ekle
                    
                    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
                    sys.stdout.flush()
                    result.append(translated)
                    time.sleep(1)
                return '\n'.join(result)
            else:
                try:
                    return translator.translate(text, src=source_lang, dest=target_lang).text
                except Exception as e:
                    msg = str(e)
                    short = msg[-200:] if len(msg) > 200 else msg
                    print(f"Çeviri hatası (son 200): {short}")
                    return text  # Tek parça hatasında orijinal metni döndür
    except Exception as e:
        msg = str(e)
        short = msg[-200:] if len(msg) > 200 else msg
        print(f"Çeviri hatası (son 200): {short}")
        return text  # Genel hatada da orijinal metinle akışı sürdür
def list_untranslated_chapters(novel_dir):
    ##Çevrilmemiş bölümleri listeler.
    en_dir = os.path.join(novel_dir, "en")
    tr_dir = os.path.join(novel_dir, "tr")
    
    if not os.path.exists(en_dir):
        print(f"Hata: İngilizce klasör bulunamadı: {en_dir}")
        return []
    
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir)
    
    en_files = sorted([f for f in os.listdir(en_dir) if f.startswith("chapter_") and f.endswith(".txt")])
    tr_files = set([f for f in os.listdir(tr_dir) if f.startswith("chapter_") and f.endswith(".txt")])
    
    untranslated = []
    for f in en_files:
        if f not in tr_files:
            try:
                chapter_num = int(f.replace("chapter_", "").replace(".txt", ""))
                untranslated.append((chapter_num, f))
            except ValueError:
                continue
    
    return sorted(untranslated)
def load_translation_progress(novel_dir):
    ##Çeviri ilerleme durumunu yükler.
    progress_file = os.path.join(novel_dir, "translate_progress.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Çeviri ilerleme dosyası yüklenemedi: {e}")
    return {"last_chapter": 0, "total_translated": 0}
def save_translation_progress(novel_dir, chapter_num, total_translated):
    ##Çeviri ilerleme durumunu kaydeder.
    progress_file = os.path.join(novel_dir, "translate_progress.json")
    progress = {
        "last_chapter": chapter_num,
        "total_translated": total_translated
    }
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f)
        return True
    except Exception as e:
        print(f"Çeviri ilerleme kaydedilemedi: {e}")
        return False
def _split_chunks(text, max_length=4500):
    ##Metni çeviri için uygun parçalara böler.
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 1 <= max_length:
            if current_chunk:
                current_chunk += '\n' + p
            else:
                current_chunk = p
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = p
    if current_chunk:
        chunks.append(current_chunk)
    return chunks
def _print_progress_bar(chapter_num, current_chapter_index, total_chapters, control):
    while not control.stop_progress_bar:
        progress_percentage = (current_chapter_index / total_chapters)
        filled_length = int(20 * progress_percentage)
        bar = '█' * filled_length + '-' * (20 - filled_length)
        sys.stdout.write(f"\rBölüm {chapter_num} çevriliyor... ({current_chapter_index}/{total_chapters}) [{bar}]")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
    sys.stdout.flush()

def translate_chapters(novel_dir, chapters, control=None, start_from=0, limit=None, source_lang='en', target_lang='tr'):
    ##Belirtilen bölümleri çevirir.
    if TRANSLATOR_BACKEND is None:
        print("Çeviri yapılamıyor: Çeviri kütüphanesi yüklü değil.")
        return 0
    en_dir = os.path.join(novel_dir, "en")
    tr_dir = os.path.join(novel_dir, "tr")
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir)

    total_translated = 0
    chapters_to_translate = chapters[start_from:limit] if limit else chapters[start_from:]
    
    for i, (chapter_num, filename) in enumerate(chapters_to_translate):
        # Durdurma kontrolü
        if control and control.stop_event.is_set():
            last_chapter = chapters_to_translate[i-1][0] if i > 0 else 0
            save_translation_progress(novel_dir, last_chapter, total_translated)
            print("Çeviri durduruldu. İlerleme kaydedildi. Ana menüye dönülüyor.")
            return -1
        
        # Duraklatma kontrolü
        if control and not control.pause_event.is_set():
            print("Çeviri duraklatıldı. Devam etmek için 'R' tuşuna basın.")
            control.pause_event.wait()
   
        # İlerleme çubuğunu gösteren bir döngü başlat
        control.stop_progress_bar = False # Her yeni bölüm için sıfırla
        progress_thread = threading.Thread(target=_print_progress_bar, args=(chapter_num, i+1, len(chapters_to_translate), control))
        progress_thread.daemon = True
        progress_thread.start()
        
        en_file = os.path.join(en_dir, filename)
        tr_file = os.path.join(tr_dir, filename)
        
        try:
            with open(en_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Bölüm ilerleme çubuğunu durdur ve satırı temizle
            if control:
                control.stop_progress_bar = True
            progress_thread.join()
            sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
            sys.stdout.flush()

            translated = translate_text_en_to_tr(content, control, source_lang, target_lang, chapter_num)
            if translated:
                with open(tr_file, "w", encoding="utf-8") as f:
                    f.write(translated)
                
                total_translated += 1
                save_translation_progress(novel_dir, chapter_num, total_translated)
                print(f"Bölüm {chapter_num} çevrildi ve kaydedildi.")
            else:
                print(f"Bölüm {chapter_num} çevrilemedi.")
        
        except Exception as e:
            print(f"Bölüm {chapter_num} işlenirken hata: {e}")
        
        # API sınırlamalarını aşmamak için bekleme
        time.sleep(1)
    
    return total_translated

def show_translation_menu(novel_dir):
    ##Çeviri menüsünü gösterir ve işlemleri yönetir.
    items = list_untranslated_chapters(novel_dir)
    total = len(items)
    print(f"\n[Çeviri] Novel: {os.path.basename(novel_dir)} | Çevrilmemiş bölüm sayısı: {total}")
    
    if total:
        # Global dil ayarlarını kullan
        print(f"Çeviri dilleri: Kaynak: {source_lang}, Hedef: {target_lang}")

        show_all = input("Tam liste gösterilsin mi? (E/H): ").strip().lower()
        if show_all.startswith('e'):
            print("Çevrilmemiş bölümler:")
            all_names = ", ".join(f"chapter_{str(n).zfill(4)}" for n, _ in items)
            print(all_names)
        
        progress = load_translation_progress(novel_dir)
        last_chapter = progress.get("last_translated_chapter", 0)
        
        if last_chapter > 0:
            resume = input(f"Son çevrilen bölüm: {last_chapter}. Buradan devam edilsin mi? (E/H): ").strip().lower()
            if resume.startswith('e'):
                start_idx = 0
                for idx, (num, _) in enumerate(items):
                    if num > last_chapter:
                        start_idx = idx
                        break
                
                print(f"Bölüm {items[start_idx][0]}'den devam ediliyor...")
                control = Control()
                start_keyboard_listener(control)
                
                print("\nÇeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                translated = translate_chapters(novel_dir, items, control, start_idx, source_lang, target_lang)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
                return
        
        print("\nÇevrilecek bölümleri seçin:")
        print("1. Tek bölüm çevir")
        print("2. Bölüm aralığı çevir")
        print("3. Tüm çevrilmemiş bölümleri çevir")
        print("M. Ana menüye dön")
        
        choice = input("Seçiminiz (1/2/3/M): ").strip()
        
        if choice.lower() == 'm':
            print("Ana menüye dönülüyor...")
            return
        
        control = Control()
        start_keyboard_listener(control)
        
        if choice == "1":
            chapter_input = input("Çevrilecek bölüm numarası: ").strip()
            try:
                chapter_num = int(chapter_input)
                selected_items = [(n, f) for n, f in items if n == chapter_num]
                if not selected_items:
                    print(f"Bölüm {chapter_num} bulunamadı veya zaten çevrilmiş.")
                    return
                
                print(f"\nBölüm {chapter_num} çevriliyor...")
                print("Çeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                translated = translate_chapters(novel_dir, selected_items, control, 0, source_lang, target_lang)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            
            except ValueError:
                print("Geçersiz bölüm numarası.")
        
        elif choice == "2":
            try:
                start_num = int(input("Başlangıç bölüm numarası: ").strip())
                end_num = int(input("Bitiş bölüm numarası: ").strip())
                
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                
                selected_items = [(n, f) for n, f in items if start_num <= n <= end_num]
                if not selected_items:
                    print(f"Belirtilen aralıkta çevrilmemiş bölüm bulunamadı.")
                    return
                
                print(f"\n{len(selected_items)} bölüm çevrilecek ({start_num}-{end_num})...")
                print("Çeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                translated = translate_chapters(novel_dir, selected_items, control, 0, source_lang, target_lang)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            
            except ValueError:
                print("Geçersiz bölüm numarası.")
        
        elif choice == "3":
            limit_input = input("Kaç bölüm çevrilsin? (0=tümü): ").strip()
            try:
                limit = int(limit_input)
                if limit < 0:
                    limit = 0
                
                limit_text = f"ilk {limit} bölüm" if limit > 0 else "tüm bölümler"
                print(f"\n{limit_text} çevrilecek...")
                print("Çeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                
                translated = translate_chapters(novel_dir, items, control, 0, limit if limit > 0 else None)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            
            except ValueError:
                print("Geçersiz sayı, tüm bölümler çevriliyor...")
                translated = translate_chapters(novel_dir, items, control)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
        
        else:
            print("Geçersiz seçim.")
    else:
        print("Çevrilecek bölüm bulunamadı.")

def list_downloaded_novels():
    ##İndirilmiş romanları listeler.
    novels_dir = os.path.join(os.getcwd(), "novels")
    if not os.path.exists(novels_dir):
        print("Henüz indirilmiş roman bulunmuyor.")
        return []
    
    novels = []
    for item in os.listdir(novels_dir):
        novel_dir = os.path.join(novels_dir, item)
        if os.path.isdir(novel_dir) and os.path.exists(os.path.join(novel_dir, "en")):
            novels.append({"name": item, "path": novel_dir, "untranslated_count": len(list_untranslated_chapters(novel_dir))})
    
    return novels

def choose_novel_menu():
    ##Roman seçim menüsünü gösterir.
    novels = list_downloaded_novels()
    
    if not novels:
        print("Çevrilecek roman bulunamadı.")
        return None
    
    print("\nKayıtlı Romanlar:")
    for i, novel_data in enumerate(novels, 1):
        print(f"{i}. {novel_data['name']} (Çevrilmemiş Bölüm: {novel_data['untranslated_count']})")
    
    while True:
        try:
            choice = input("\nÇevrilecek romanı seçin (1-{}) veya çıkış için 'q': ".format(len(novels))).strip().lower()
            
            if choice == 'q':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(novels):
                return novels[idx]["path"]  # Novel dizini döndür
            else:
                print("Geçersiz seçim. 1-{} arası bir sayı girin.".format(len(novels)))
        
        except ValueError:
            print("Geçersiz giriş. Bir sayı girin veya çıkış için 'q' yazın.")

def show_global_translation_menu():
    ##Global çeviri menüsünü gösterir.
    if TRANSLATOR_BACKEND is None:
        print("\nÇeviri yapabilmek için çeviri kütüphanesi yüklemeniz gerekiyor.")
        print("Yüklemek için: py -m pip install deep-translator")
        return
    
    novel_dir = choose_novel_menu()
    if novel_dir:
        show_translation_menu(novel_dir)

def show_main_menu():
    print("\nAna Menü:")
    print("  D - Yeni İndirme Başlat")
    print("  C - Kayıtlı İndirmelere Devam Et")
    print("  T - Kayıtlı Novel Çevir")
    print("  Q - Çıkış")
    choice = input("Seçiminizi yapın: ").strip().lower()
    return choice

def list_saved_novels():
    novels_dir = os.path.join(os.getcwd(), "novels")
    saved_novels = []
    if os.path.exists(novels_dir):
        for novel_name in os.listdir(novels_dir):
            novel_path = os.path.join(novels_dir, novel_name)
            if os.path.isdir(novel_path):
                progress_file = os.path.join(novel_path, "progress.json")
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r', encoding='utf-8') as f:
                            progress_data = json.load(f)
                        current_url = progress_data.get("current_url", "N/A")
                        current_chapter = progress_data.get("chapter_number", 0)
                        saved_novels.append({"name": novel_name, "path": novel_path, "url": current_url, "current_chapter": current_chapter})
                    except Exception as e:
                        print(f"Hata: {novel_name} için progress.json okunamadı: {e}")
    return saved_novels     
    
class Control:
    ##İndirme ve çeviri işlemlerini kontrol etmek için kullanılır.
    def __init__(self):
        self.pause_event = threading.Event()
        self.pause_event.set()  # Başlangıçta duraklatılmamış
        self.stop_event = threading.Event()
        self.stop_event.clear() # Her yeni işlemde durdurma olayını temizle
        self.translate_event = threading.Event()
        self.stop_progress_bar = False # İlerleme çubuğunu durdurmak için yeni öznitelik
        self.part_progress_message = "" # Parça ilerleme mesajını tutmak için yeni öznitelik
        
def start_keyboard_listener(control):
    def keyboard_listener():
        try:
            import msvcrt
            print("Kontroller: P=Duraklat, R=Devam, S=Durdur, T=Ana Menü")
            while not control.stop_event.is_set():
                if msvcrt.kbhit():
                    ch = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                    if ch == 'p':
                        control.pause_event.clear()
                        print("\n[Duraklatıldı - devam için 'R']")
                    elif ch == 'r':
                        control.pause_event.set()
                        print("\n[Devam ediliyor]")
                    elif ch == 's':
                        control.stop_event.set()
                        print("\n[Durdurma talebi alındı]")
                    elif ch == 't':
                        control.stop_event.set() # Ana menüye dönmek için stop_event'i set et
                        print("\n[Ana menüye dönülüyor...]")
                time.sleep(0.1)
        except ImportError:
            print("Uyarı: Windows dışı sistemde klavye dinleyici çalışmayabilir.")
    threading.Thread(target=keyboard_listener, daemon=True).start()
    
def main():
    while True:
        sel = show_main_menu()
        if sel == 'q':
            print("Çıkılıyor...")
            break

        elif sel == 't':
            # Kayıtlı romanlardan çeviri menüsünü aç
            show_global_translation_menu()
            print("\nAna menüye dönülüyor...")
            continue

        elif sel == 'd':
            # İndirme akışı
            start_url = input("Novelin ilk sayfasının URL'sini girin: ").strip()
            if not start_url:
                print("Geçerli bir URL girmelisiniz.")
                continue

            try:
                page_limit = int(input("Kaç sayfa indirilsin? (0 = sınırsız): "))
                if page_limit < 0:
                    page_limit = 0
            except ValueError:
                print("Geçersiz sayı, sınırsız olarak devam ediliyor.")
                page_limit = 0

            soup = fetch_page(start_url)
            if not soup:
                print("Başlangıç sayfası çekilemedi. Ana menüye dönülüyor.")
                continue

            novel_name = extract_novel_name(soup)
            print(f"Novel adı: {novel_name}")
            novel_dir = create_novel_directory(novel_name)

            control = Control()
            start_keyboard_listener(control)

            progress = load_progress(novel_dir)
            if progress:
                ans = input("Kayıttan devam edilsin mi? (E/H): ").strip().lower()
                if ans.startswith('e'):
                    current_url = progress.get("current_url", start_url)
                    chapter_number = progress.get("chapter_number", 1)
                    print(f"{chapter_number}. bölümden devam ediliyor...")
                else:
                    current_url = start_url
                    chapter_number = 1
            else:
                current_url = start_url
                chapter_number = 1

            try:
                pages_downloaded = 0
                while current_url:
                    
                    # Sayfa sınırı
                    if page_limit > 0 and pages_downloaded >= page_limit:
                        print(f"Sayfa sınırına ulaşıldı ({page_limit} sayfa). İlerleme kaydediliyor...")
                        save_progress(novel_dir, chapter_number, current_url)
                        break

                    # Durdurma talebi
                    if control.stop_event.is_set():
                        print("Durdurma talebi alındı. İlerleme kaydediliyor...")
                        save_progress(novel_dir, chapter_number, current_url)
                        break

                    # Duraklatma
                    control.pause_event.wait()

                    print(f"\nBölüm {chapter_number} indiriliyor... ({pages_downloaded+1}/{page_limit if page_limit > 0 else '∞'})")
                    short_url = current_url.split('/')[-1] if '/' in current_url else current_url
                    if len(short_url) > 50:
                        short_url = short_url[:47] + "..."
                    #print(f"URL: .../{short_url}")

                    soup = fetch_page(current_url)
                    if not soup:
                        save_progress(novel_dir, chapter_number, current_url)
                        print("Sayfa çekilemedi. Kalınan yer kaydediliyor.")
                        break

                    content = extract_novel_content(soup)
                    if save_chapter(content, chapter_number, novel_dir):
                        chapter_number += 1
                        pages_downloaded += 1

                    next_url = find_next_page_url(soup, current_url)
                    if next_url == current_url:
                        print("Sonraki sayfa mevcut sayfayla aynı. İşlem sonlandırılıyor.")
                        save_progress(novel_dir, chapter_number, next_url)
                        break
                    if not next_url:
                        print("Sonraki sayfa bulunamadı. İşlem tamamlandı.")
                        save_progress(novel_dir, chapter_number, "Final")
                        break

                    #save_progress(novel_dir, chapter_number, next_url)
                    current_url = next_url

                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nCtrl+C yakalandı. İlerleme kaydediliyor...")
                save_progress(novel_dir, chapter_number, current_url)
                return

            print(f"\nİşlem tamamlandı. Toplam {pages_downloaded} sayfa indirildi.")
            short_en_dir = os.path.join("novels", os.path.basename(novel_dir), source_lang)
            print(f"Dosyalar şu klasöre kaydedildi: .../{short_en_dir}")

            print("\nAna menüye dönülüyor...")
            continue

        elif sel == 'c':
            # Mevcut indirmeye devam et akışı
            saved_novels = list_saved_novels()
            if not saved_novels:
                print("Kayıtlı roman bulunamadı. Lütfen önce yeni bir indirme başlatın.")
                continue

            print("\n=== Kayıtlı Romanlar ===")
            for i, novel in enumerate(saved_novels):
                print(f"{i+1}. {novel['name']} (Son Bölüm: {novel['current_chapter']})")
            print("========================")

            try:
                choice = int(input("Devam etmek istediğiniz romanın numarasını girin: ")) - 1
                if 0 <= choice < len(saved_novels):
                    selected_novel = saved_novels[choice]
                    novel_dir = selected_novel['path']
                    novel_name = selected_novel['name']

                    control = Control()
                    start_keyboard_listener(control)

                    progress = load_progress(novel_dir)
                    if progress:
                        current_url = progress.get("current_url")
                        chapter_number = progress.get("chapter_number", 1)
                        if not current_url:
                            print("Kayıtlı ilerleme dosyasında URL bulunamadı. Yeni indirme olarak başlatılıyor.")
                            continue
                        print(f"{novel_name} romanının {chapter_number}. bölümünden devam ediliyor...")
                    else:
                        print("Seçilen roman için ilerleme dosyası bulunamadı. Ana menüye dönülüyor.")
                        continue

                    try:
                        pages_downloaded = 0
                        try:
                            page_limit = int(input("Kaç sayfa indirilsin? (0 = sınırsız): "))
                            if page_limit < 0:
                                page_limit = 0
                        except ValueError:
                            print("Geçersiz sayı, sınırsız olarak devam ediliyor.")
                            page_limit = 0
                        # İndirme döngüsü (sel == 'd' bloğundaki ile aynı)
                        while current_url:
                            # Sayfa sınırı
                            if page_limit > 0 and pages_downloaded >= page_limit:
                                print(f"Sayfa sınırına ulaşıldı ({page_limit} sayfa). İlerleme kaydediliyor...")
                                save_progress(novel_dir, chapter_number, current_url)
                                break



                            # Durdurma talebi
                            if control.stop_event.is_set():
                                print("Durdurma talebi alındı. İlerleme kaydediliyor...")
                                save_progress(novel_dir, chapter_number, current_url)
                                break

                            # Duraklatma
                            control.pause_event.wait()

                            print(f"\nBölüm {chapter_number} indiriliyor... ({pages_downloaded+1}/{page_limit if page_limit > 0 else '∞'})")
                            short_url = current_url.split('/')[-1] if '/' in current_url else current_url
                            if len(short_url) > 50:
                                short_url = short_url[:47] + "..."
                            #print(f"URL: .../{short_url}")

                            soup = fetch_page(current_url)
                            if not soup:
                                print("Sayfa çekilemedi. Sonraki sayfaya geçiliyor.")
                                break

                            content = extract_novel_content(soup)
                            if save_chapter(content, chapter_number, novel_dir):
                                chapter_number += 1
                                pages_downloaded += 1

                            next_url = find_next_page_url(soup, current_url)
                            if next_url == current_url:
                                print("Sonraki sayfa mevcut sayfayla aynı. İşlem sonlandırılıyor.")
                                save_progress(novel_dir, chapter_number, next_url)
                                break
                            if not next_url:
                                print("Sonraki sayfa bulunamadı. İşlem tamamlandı.")
                                save_progress(novel_dir, chapter_number, "Final")
                                break

                            #save_progress(novel_dir, chapter_number, next_url)
                            current_url = next_url

                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\nCtrl+C yakalandı. İlerleme kaydediliyor...")
                        save_progress(novel_dir, chapter_number, current_url)
                        break
                else:
                    print("Geçersiz seçim. Ana menüye dönülüyor.")
            except ValueError:
                continue 

        else: 
            print("Geçersiz seçim. Lütfen D/C/T/Q tuşlarını kullanın.")
            continue 

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\nBeklenmeyen hata:", e)
        traceback.print_exc()
        input("\nHata ayrıntısını görmek için Enter'a basın...")
