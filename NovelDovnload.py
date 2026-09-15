############################################
# NovelDovnload.py
# ver. 0.9.6
# 30.10.2025
# indirme ve çeviri işlemlerini yapar. 
# Halen hataları ve eksikleri olabilir. Gördüğüm tüm hataları gidermeye çalıştım.
# Optimize edilmemiştir. İçerisinde halen gereksiz veya fazladan kod bulunabilir..
# Edit: D'ssconnecTed.  Kodlayan: Gemini. :)
# 
#############################################
import os
import time
import re
import json
import threading
import sys 
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
    

source_lang = "en"  # indirilen kaynak dili
target_lang = "tr"  # çeviri hedef dili

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
        msg = str(e)
        short = msg[-100:] if len(msg) > 100 else msg
        print(f"Hata::Sayfa çekilemedi - {url}")
        print(f"Hata detayı::{msg}")
        return None
        
# Bölüm URL'sinden ana roman sayfasının URL'sini bulur
def find_novel_base_url(chapter_url):
    # Bölüm URL'sinden ana roman sayfasının URL'sini bulur.
    # URL'nin sonundaki /chapter-X-ad-gibi kısımları kaldır
    parts = chapter_url.strip('/').split('/')
    
    # Ana URL'yi bulana kadar son parçayı sil
    reverse_parts = list(reversed(parts))
    
    # Eğer son parça 'chapter' veya 'bölüm' içeriyorsa:
    if len(reverse_parts) > 1 and ('chapter' in reverse_parts[0].lower() or 'bölüm' in reverse_parts[0].lower()):
        # Son kısmı at
        base_url_parts = parts[:-1]
        base_url = '/'.join(base_url_parts) + '/'
        
        # Sonucu kontrol et - hala bir bölüm linki olabilir, bir parça daha at
        if 'chapter' in base_url.lower() or 'bölüm' in base_url.lower():
            base_url_parts = base_url_parts[:-1]
            base_url = '/'.join(base_url_parts) + '/'
        
        return base_url
        
    return chapter_url # Zaten ana sayfa olabilir

# Novelin ana sayfasından Novelin bilglerini çeker
def get_total_chapters(novel_base_url):
    # Novelin ana sayfasından toplam bölüm sayısını rozetten veya metinden çeker.
    print(f"Toplam bölüm sayısı kontrol ediliyor: {novel_base_url}")
    soup = fetch_page(novel_base_url)
    if not soup:
        print("Hata: Toplam bölüm sayısı belirlenemedi.")
        return 0
    
    try:
        # Önce '999+' gibi rozet içeren span etiketini ara
        badge_tag = soup.find('span', string=lambda t: t and '+' in t)
        if badge_tag:
            badge_text = badge_tag.get_text(strip=True)
            if '999+' in badge_text or '1000+' in badge_text:
                print(f"Toplam bölüm rozeti yakalandı: {badge_text} (1000+ olarak kabul ediliyor)")
                return 1000 # 999+ olduğu için varsayılan üst sınır veya yüksek bir değer veriyoruz
        
        # Eğer rozet bulunamazsa Chapters etiketini veya liste başlıklarını kontrol et
        strong_tag = soup.find('strong', string=lambda t: t and 'Chapters:' in t)
        if strong_tag and strong_tag.parent:
            span_tag = strong_tag.parent.find('span')
            if span_tag:
                count_text = span_tag.get_text(strip=True)
                if count_text.isdigit():
                    print(f"Toplam bölüm: {count_text}")
                    return int(count_text)

        # En kötü ihtimalle listedeki ilk bölümün numarasını baz al
        chapter_link = soup.find('a', href=re.compile(r'chapter-\d+', re.IGNORECASE))
        if chapter_link:
            match = re.search(r'chapter-(\d+)', chapter_link.get('href', ''), re.IGNORECASE)
            if match:
                total_count = int(match.group(1))
                print(f"Listeden tespit edilen en yüksek bölüm: {total_count}")
                return total_count
        
        print("Uyarı: Toplam bölüm sayısı belirlenemedi. 0 olarak ayarlandı.")
        return 0
    except Exception as e:
        print(f"Toplam bölüm sayısı çekilirken hata oluştu: {e}")
        return 0
        
def find_next_page_url(soup, current_url):
    ## Sonraki sayfa linkini bulur.
    try:
        # Sağlanan yeni HTML yapısına göre sonraki sayfa 'Next' yazılı veya 'aria-hidden' içeren 'a' etiketinden bulunur.
        # title="Next" veya içindeki Next metni/ikonuna göre arama yapalım:
        next_link = soup.find('a', title=re.compile('Next', re.IGNORECASE))
        
        if not next_link:
            # Alternatif olarak içerisindeki span yardımıyla bulmayı dene
            span_next = soup.find('span', string=re.compile('Next', re.IGNORECASE))
            if span_next and span_next.parent and span_next.parent.name == 'a':
                next_link = span_next.parent
                
        if next_link and next_link.get('href'):
            next_url = next_link['href']
            
            # Eğer href='#' ise, bu son sayfa demektir.
            if next_url == '#':
                print("Sonraki sayfa linki '#' olarak bulundu. Bu son bölümdür. İşlem sonlandırılıyor.")
                return None
            
            # Göreceli URL'yi mutlak URL'ye dönüştür
            if next_url.startswith('/'):
                base_url = '/'.join(current_url.split('/')[:3])
                next_url = base_url + next_url
            return next_url
        else:
            print("Sonraki sayfa linki bulunamadı.")
        
        return None
    except Exception as e:
        print(f"Sonraki sayfa linki bulunurken hata oluştu: {e}")
        return None

def _clear_name(yazi):
    # Temizlenecek kelimeler (büyük/küçük harfe duyarsız)
    no_words = ['read', 'mtl', '-', 're:', ',' ,'.' ,'_']
    
    # Tüm istenmeyen kelimeleri kaldır
    for word in no_words:
        yazi = yazi.lower().replace(word, '')
    
    # Özel karakterleri temizle ve baştaki/sondaki boşlukları al
    safe_name = re.sub(r'[\\/*?:"<>|]', "", yazi).strip()
    # Kelimelerin ilk harflerini büyük yap.
    final_name = safe_name.title()
    return final_name
    
def create_novel_directory(novel_name):
    ##Novel için klasör oluşturur."""
    safe_name = _clear_name(novel_name)
    current_dir = os.getcwd()
    print(f"Mevcut çalışma dizini: {current_dir}")
    
    novel_dir = os.path.join(current_dir, "novels", safe_name)
    short_dir = os.path.join("novels", safe_name)
    print(f"Hedef klasör: .../{short_dir}")
    
    if not os.path.exists(novel_dir):
        os.makedirs(novel_dir)
        print(f"Klasör oluşturuldu: .../{short_dir}")
    else:
        print(f"Klasör zaten mevcut: .../{short_dir}")

    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    short_en = os.path.join("novels", safe_name, source_lang)
    short_tr = os.path.join("novels", safe_name, target_lang)
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
    
    en_dir = os.path.join(novel_dir, source_lang)
    file_path = os.path.join(en_dir, f"chapter_{chapter_number:04d}.txt")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        file_name = os.path.basename(file_path)
        print(f"Bölüm:{chapter_number} :: -> İçerik:{len(content)} karakter:: {file_name} kaydedildi::.")
        return True
    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")
        return False
        
def extract_novel_content(soup):
    try:
        inner_html = None
        
        # Yeni sağlanan yapıya özel güncellenmiş seçici:
        # <div class="novel-tts-content px-7" ...> alanı ana metin taşıyıcısıdır.
        content_div = soup.find('div', class_=lambda c: c and 'novel-tts-content' in c)
        
        if not content_div:
            # Yedek olarak eski veya alternatif etiketleri kontrol et
            match = re.search(r'<!--INFOLINKS_ON-->(.*?)<!--INFOLINKS_OFF-->', soup.decode(), re.DOTALL | re.IGNORECASE)
            if match:
                inner_html = match.group(1)
            else:
                content_div = soup.find('div', id='max-w-') or soup.find('div', class_='novel-reader-content')
                if content_div:
                    inner_html = str(content_div)
        else:
            inner_html = str(content_div)
                
        if not inner_html:
             print("Uyarı: İçerik HTML'i boş.")
             return None
             
        inner_soup = BeautifulSoup(inner_html, 'html.parser')
        
        for tag in inner_soup(['script', 'style']):
            tag.decompose()
        text = inner_soup.get_text(separator='\n')
        
        text = re.sub(r'\r\n?', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n\n', text)
        text = re.sub(r'[ \t]{2,}', '\n\n', text)
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        text = re.sub(r'\n{2,}', '\n\n', text)
        
        cleaned = text.strip()
        
        if len(cleaned) < 50: 
            print(f"Uyarı: Çıkarılan içerik çok kısa ({len(cleaned)} karakter). Başarısız sayılıyor.")
            return None
        
        return cleaned
    except Exception as e:
        print(f"İçerik çıkarılırken hata oluştu: {e}")
        return None
        
def extract_novel_name(soup):
    ##Sayfa başlığından novel adını çıkarır.
    try:
        title = soup.title.string if soup.title else None
        
        if not title:
            title_elem = soup.find('h1')
            title = title_elem.get_text() if title_elem else "Bilinmeyen Novel"
        
        title = re.sub(r' - Chapter \d+.*', '', title)
        title = re.sub(r' - Bölüm \d+.*', '', title)
        
        return title.strip()
    except Exception:
        return "Bilinmeyen Novel"

def save_progress(novel_dir, chapter_number, current_url, total_chapters=0):
    ##İlerlemeyi novel klasörüne progress.json olarak yazar.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        data = {
            "chapter_number": chapter_number,
            "current_url": current_url,
            "total_chapters": total_chapters
        }
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"İlerleme kaydedilemedi: {e}")
        
def load_progress(novel_dir, print_message=False):
    ##Novel klasöründeki progress.json'ı okur.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        if os.path.exists(progress_path):
            with open(progress_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chapter_num = data.get("chapter_number", 1)
            current_url = data.get("current_url", "N/A")
            total_chapters = data.get("total_chapters", 5000) 

            if print_message:
                short_url = current_url.split('/')[-1] if '/' in current_url else current_url
                if len(short_url) > 50:
                    short_url = short_url[:47] + "..."
                print(f"Mevcut ilerleme: bölüm={chapter_num}, toplam={total_chapters}, url=/{short_url}")
            
            data["chapter_number"] = chapter_num
            data["current_url"] = current_url
            data["total_chapters"] = total_chapters
            return data
    except Exception as e:
        if print_message: 
            print(f"İlerleme yüklenemedi: {e}")
        
    return {"chapter_number": 1, "current_url": "N/A", "total_chapters": 0}    
    
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

# Çeviri kütüphanesini doğrudan googletrans olarak ayarlıyoruz
try:
    from googletrans import Translator as GTTranslator
    TRANSLATOR_BACKEND = 'google'
except ImportError:
    GTTranslator = None
    TRANSLATOR_BACKEND = None
    print("Googletrans kütüphanesi bulunamadı! 'pip install googletrans==4.0.0-rc1' komutu ile yükleyin.")

def translate_text_en_to_tr(text, control=None, source_lang='en', target_lang='tr', chapter_num=None):
    if TRANSLATOR_BACKEND is None:
        print("Çeviri yapılamıyor: googletrans kütüphanesi yüklü değil.")
        return None
        
    try:
        translator = GTTranslator()
        
        # Metin uzunsa parçalara bölerek çevir
        if len(text) > 4500:
            chunks = _split_chunks(text)
            result = []
            for i, chunk in enumerate(chunks):
                if control and control.stop_event.is_set():
                    return None
                if control and not control.pause_event.is_set():
                    control.pause_event.wait()
                
                if chapter_num:
                    sys.stdout.write(f"\rBölüm {chapter_num} - Parça {i + 1}/{len(chunks)} Google ile çevriliyor.")
                else:
                    sys.stdout.write(f"\rParça {i + 1}/{len(chunks)} Google ile çevriliyor.")
                sys.stdout.flush()
                
                translated_chunk = chunk
                retry_count = 0
                max_retries = 3
                while retry_count <= max_retries:
                    try:
                        # googletrans çağrısı
                        res = translator.translate(chunk, src=source_lang, dest=target_lang)
                        if res and res.text:
                            translated_chunk = res.text
                        break
                    except Exception:
                        retry_count += 1
                        if retry_count <= max_retries:
                            time.sleep(2)
                        else:
                            translated_chunk = chunk
                            
                sys.stdout.write("\r" + " " * 80 + "\r")
                sys.stdout.flush()
                result.append(translated_chunk)
                time.sleep(0.5)
            return '\n'.join(result)
        else:
            # Kısa metinler için doğrudan çeviri
            retry_count = 0
            max_retries = 3
            while retry_count <= max_retries:
                try:
                    res = translator.translate(text, src=source_lang, dest=target_lang)
                    if res and res.text:
                        return res.text
                    break
                except Exception:
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(2)
                    else:
                        return text
            return text
    except Exception as e:
        print(f"Çeviri hatası: {e}")
        return text

def list_untranslated_chapters(novel_dir):
    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    
    if not os.path.exists(en_dir):
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
    progress_file = os.path.join(novel_dir, "translate_progress.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_chapter": 0, "total_translated": 0}
    
def save_translation_progress(novel_dir, chapter_num, total_translated):
    progress_file = os.path.join(novel_dir, "translate_progress.json")
    progress = {"last_chapter": chapter_num, "total_translated": total_translated}
    try:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f)
        return True
    except Exception:
        return False
        
def _split_chunks(text, max_length=4500):
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
        sys.stdout.write(f"\rBölüm {chapter_num} çevriliyor... ({current_chapter_index}/{total_chapters})")
        sys.stdout.flush()
        time.sleep(0.01)
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

def translate_chapters(novel_dir, chapters, control=None, start_from=0, limit=None, source_lang="en", target_lang="tr"):
    if TRANSLATOR_BACKEND is None:
        return 0
    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir)

    total_translated = 0
    chapters_to_translate = chapters[start_from:limit] if limit else chapters[start_from:]
    
    for i, (chapter_num, filename) in enumerate(chapters_to_translate):
        if control and control.stop_event.is_set():
            last_chapter = chapters_to_translate[i-1][0] if i > 0 else 0
            save_translation_progress(novel_dir, last_chapter, total_translated)
            return -1
        
        if control and not control.pause_event.is_set():
            control.pause_event.wait()
   
        control.stop_progress_bar = False
        progress_thread = threading.Thread(target=_print_progress_bar, args=(chapter_num, i+1, len(chapters_to_translate), control))
        progress_thread.daemon = True
        progress_thread.start()
        
        en_file = os.path.join(en_dir, filename)
        tr_file = os.path.join(tr_dir, filename)
        
        try:
            with open(en_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if control:
                control.stop_progress_bar = True
            progress_thread.join()
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()

            translated = translate_text_en_to_tr(content, control, source_lang, target_lang, chapter_num)
            if translated:
                with open(tr_file, "w", encoding="utf-8") as f:
                    f.write(translated)
                
                total_translated += 1
                save_translation_progress(novel_dir, chapter_num, total_translated)
                if limit == None:
                    items = list_untranslated_chapters(novel_dir)
                    limit = len(items) + 1
                print(f"Bölüm {chapter_num} çevrildi ve kaydedildi. ({total_translated}/{limit})")
            else:
                print(f"Bölüm {chapter_num} çevrilemedi.")
        except Exception as e:
            print(f"Bölüm {chapter_num} işlenirken hata: {e}")
        
        time.sleep(1)
    return total_translated

def show_translation_menu(novel_dir):
    items = list_untranslated_chapters(novel_dir)
    total = len(items)
    print("\n_____________________________________________________________________________________")
    print(f"\n[Çeviri] Novel: {os.path.basename(novel_dir)} | Çevrilmemiş bölüm sayısı: {total}")
    
    if total:
        print(f"Çeviri dilleri: Kaynak: {source_lang}, Hedef: {target_lang}")
        print("_____________________________________________________________________________________")
        choice = "3"
        
        control = Control()
        start_keyboard_listener(control)
        
        if choice == "3":
            limit_input = input("Kaç bölüm çevrilsin? [0 = Tümü]: ").strip()
            try:
                limit = int(limit_input)
                if limit == 0:
                    limit = total
                print(f"\n[ Novel: {os.path.basename(novel_dir)} ] Çevrilmemiş bölüm sayısı: {total}")
                print(f"\nToplam [ {limit} ] bölüm çevrilecek...")
                print("_____________________________________________________________________________________\n")
                translated = translate_chapters(novel_dir, items, control, 0, limit if limit > 0 else None)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            except ValueError:
                translated = translate_chapters(novel_dir, items, control)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
    else:
        print("Çevrilecek bölüm bulunamadı.")

def list_downloaded_novels():
    novels_dir = os.path.join(os.getcwd(), "novels")
    if not os.path.exists(novels_dir):
        return []
    
    novels = []
    for item in os.listdir(novels_dir):
        novel_dir = os.path.join(novels_dir, item)
        if os.path.isdir(novel_dir) and os.path.exists(os.path.join(novel_dir, "en")):
            progress_data = load_progress(novel_dir)
            total_chapters = progress_data.get('total_chapters', 0) if progress_data else 0 
            downloaded_count = progress_data.get('chapter_number', 1) - 1

            novels.append({
                "name": item, 
                "path": novel_dir, 
                "untranslated_count": len(list_untranslated_chapters(novel_dir)),
                "total_chapters": total_chapters, 
                "downloaded_count": downloaded_count
            })
    return novels

def choose_novel_menu():
    novels = list_downloaded_novels()
    if not novels:
        print("Çevrilecek roman bulunamadı.")
        return None
    
    print("████████████████████████████████ Kayıtlı Noveller ████████████████████████████████")
    for i, novel_data in enumerate(novels, 1):
        total_info = f"/{novel_data['total_chapters']}" if novel_data['total_chapters'] > 0 else ""
        print(f"{i}. {novel_data['name']} (Çevrilmemiş Bölüm: {novel_data['untranslated_count']}{total_info})")
    print("__________________________________________________________________________________")
    while True:
        try:
            choice = input("\nÇevrilecek Noveli seçin (1-{}) veya çıkış için [Q]: ".format(len(novels))).strip().lower()
            if choice == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(novels):
                return novels[idx]["path"]
            else:
                print("Geçersiz seçim. 1-{} arası bir sayı girin.".format(len(novels)))
        except ValueError:
            print("Geçersiz giriş.")

def show_global_translation_menu():
    if TRANSLATOR_BACKEND is None:
        print("\nÇeviri yapabilmek için çeviri kütüphanesi yüklemeniz gerekiyor.")
        return
    novel_dir = choose_novel_menu()
    if novel_dir:
        show_translation_menu(novel_dir)

def show_main_menu():
    print("\n███████████████████ Ana Menü ███████████████████")
    print("█  D - Yeni İndirme Başlat")
    print("█  C - Kayıtlı İndirmelere Devam Et")
    print("█  T - Kayıtlı Novel Çevir")
    print("█  Q - Çıkış")
    print("█_______________________________________________\n")
    choice = input("█__ Seçiminizi yapın: ").strip().lower()
    print("________________________________________________\n")
    return choice

def list_saved_novels():
    novels_dir = os.path.join(os.getcwd(), "novels")
    saved_novels = []
    if os.path.exists(novels_dir):
        for novel_name in os.listdir(novels_dir):
            novel_path = os.path.join(novels_dir, novel_name)
            if os.path.isdir(novel_path):
                progress_data = load_progress(novel_path, print_message=False)
                en_dir = os.path.join(novel_path, source_lang)
                total_downloaded = 0
                if os.path.exists(en_dir):
                    total_downloaded = len([f for f in os.listdir(en_dir) if f.startswith("chapter_") and f.endswith(".txt")])

                if progress_data and progress_data.get("current_url") != "N/A":
                    current_url = progress_data.get("current_url")
                    current_chapter = progress_data.get("chapter_number")
                    total_chapters = progress_data.get("total_chapters", 0)
                    
                    saved_novels.append({
                        "name": novel_name, 
                        "path": novel_path, 
                        "url": current_url, 
                        "current_chapter": current_chapter, 
                        "downloaded_count": total_downloaded, 
                        "total_chapters": total_chapters 
                    })
    return saved_novels     
    
class Control:
    def __init__(self):
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.translate_event = threading.Event()
        self.stop_progress_bar = False
        self.part_progress_message = ""
        
def start_keyboard_listener(control):
    def keyboard_listener():
        try:
            import msvcrt
            print("      Kontroller: [P]-Duraklat]  [R]-Devam]   [S]-Durdur]  [T]-Ana Menü]")
            print("_____________________________________________________________________________________")
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
                        control.stop_event.set()
                        print("\n[Ana menüye dönülüyor...]")
                time.sleep(0.1)
        except ImportError:
            pass
    
    try:
        import msvcrt
        threading.Thread(target=keyboard_listener, daemon=True).start()
    except ImportError:
        pass
    
def main():
    while True:
        sel = show_main_menu()
        if sel == 'q':
            print("Çıkılıyor...")
            break

        elif sel == 't':
            show_global_translation_menu()
            print("\nAna menüye dönülüyor...")
            continue

        elif sel == 'd':
            start_url = input("Novelin ilk sayfasının URL'sini girin: ").strip()
            if not start_url:
                print("Geçerli bir URL girmelisiniz.")
                continue

            try:
                page_limit = int(input("Kaç sayfa indirilsin? (0 = sınırsız): "))
                print("\n_____________________________________________________________________________________")
                if page_limit < 0:
                    page_limit = 0
            except ValueError:
                page_limit = 0

            novel_base_url = find_novel_base_url(start_url)
            total_chapters = get_total_chapters(novel_base_url) 

            soup = fetch_page(start_url)
            if not soup:
                print("Başlangıç sayfası çekilemedi. Ana menüye dönülüyor.")
                continue

            novel_name = extract_novel_name(soup)
            print(f"Novel adı: {novel_name}")
            novel_dir = create_novel_directory(novel_name)

            control = Control()
            start_keyboard_listener(control)
            
            progress = load_progress(novel_dir, print_message=True) 

            current_url = start_url
            chapter_number = 1

            try:
                pages_downloaded = 0
                while current_url and current_url.lower() != "final":
                    if page_limit > 0 and pages_downloaded >= page_limit:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    if control.stop_event.is_set():
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    control.pause_event.wait()
                    
                    session_limit_display = page_limit if page_limit > 0 else '∞'
                    session_progress_info = f" ({pages_downloaded+1}/{session_limit_display})"
                    
                    print(f"\nBölüm {chapter_number} indiriliyor... {session_progress_info}")

                    soup = fetch_page(current_url)
                    if not soup:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        print("Sayfa çekilemedi. Kalınan yer kaydediliyor.")
                        break

                    content = extract_novel_content(soup)
                    if not content:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        print("İçerik çıkarılamadı. Kalınan yer kaydediliyor.")
                        break
                        
                    if save_chapter(content, chapter_number, novel_dir):
                        next_url = find_next_page_url(soup, current_url)
                        
                        if next_url and next_url.lower() == current_url.lower():
                            print("Sonraki sayfa mevcut sayfayla aynı. İşlem sonlandırılıyor.")
                            save_progress(novel_dir, chapter_number + 1, next_url, total_chapters)
                            break
                        if not next_url:
                            print("Sonraki sayfa bulunamadı. İşlem tamamlandı.")
                            save_progress(novel_dir, chapter_number + 1, "Final", total_chapters)
                            break
                        
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                    
                        chapter_number += 1
                        pages_downloaded += 1
                        current_url = next_url
                    else:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    time.sleep(1)
                    
            except KeyboardInterrupt:
                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                return

            print(f"\nİşlem tamamlandı. Toplam {pages_downloaded} sayfa indirildi.")
            continue

        elif sel == 'c':
            saved_novels = list_saved_novels()
            if not saved_novels:
                print("Kayıtlı roman bulunamadı. Lütfen önce yeni bir indirme başlatın.")
                continue

            print("\n████████████████████████████████ Kayıtlı Noveller ████████████████████████████████")
            for i, novel in enumerate(saved_novels):
                novel_name = novel['name']
                display_name = novel_name[:60] + ('...' if len(novel_name) > 60 else '')
                total_chapters_display = f" -- Toplam: {novel['total_chapters']}" if novel['total_chapters'] > 0 else ""
                print(f"{i+1}. {display_name} (İndirilen: {novel['downloaded_count']}{total_chapters_display})")
            print("____________________________________________________________________________________")

            try:
                choice = int(input("Devam etmek istediğiniz romanın numarasını girin: ")) - 1
                if 0 <= choice < len(saved_novels):
                    selected_novel = saved_novels[choice]
                    novel_dir = selected_novel['path']
                    novel_name = selected_novel['name']
                    total_chapters = selected_novel['total_chapters']

                    control = Control()
                    start_keyboard_listener(control)

                    progress = load_progress(novel_dir, print_message=True)
                    if progress:
                        current_url = progress.get("current_url")
                        chapter_number = progress.get("chapter_number", 1)
                        if not current_url:
                            continue
                            
                        if total_chapters == 0:
                            novel_base_url = find_novel_base_url(current_url) 
                            new_total_chapters = get_total_chapters(novel_base_url)
                            if new_total_chapters > 0:
                                total_chapters = new_total_chapters
                                save_progress(novel_dir, chapter_number, current_url, total_chapters) 
                        
                        print(f"\n{novel_name} Novelin {chapter_number}. bölümünden devam edecek...")
                    else:
                        continue

                    try:
                        pages_downloaded = 0
                        try:
                            page_limit = int(input("Kaç sayfa indirilsin? [0] sınırsız: "))
                            if page_limit < 0:
                                page_limit = 0
                        except ValueError:
                            page_limit = 0
                            
                        while current_url and current_url.lower() != "final":
                            if page_limit > 0 and pages_downloaded >= page_limit:
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            if control.stop_event.is_set():
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            control.pause_event.wait()
                            
                            session_limit_display = page_limit if page_limit > 0 else '∞'
                            session_progress_info = f" ({pages_downloaded+1}/{session_limit_display})"
                            
                            print(f"Bölüm {chapter_number} indiriliyor.. {session_progress_info}")

                            soup = fetch_page(current_url)
                            if not soup:
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            content = extract_novel_content(soup)
                            if not content:
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break
                                
                            if save_chapter(content, chapter_number, novel_dir):
                                next_url = find_next_page_url(soup, current_url)
                                
                                if next_url and next_url.lower() == current_url.lower():
                                    save_progress(novel_dir, chapter_number + 1, next_url, total_chapters)
                                    break
                                if not next_url:
                                    save_progress(novel_dir, chapter_number + 1, "Final", total_chapters)
                                    break
                                    
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                            
                                chapter_number += 1
                                pages_downloaded += 1
                                current_url = next_url
                            else:
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            time.sleep(1)
                            
                        print(f"\nİşlem tamamlandı. Toplam {pages_downloaded} sayfa indirildi.")
                        
                    except KeyboardInterrupt:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break
            except ValueError:
                continue 

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\nBeklenmeyen hata:", e)
        traceback.print_exc()