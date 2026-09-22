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
from urllib.parse import urljoin, urlparse
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
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # HTTP hatalarını kontrol et
        # Sunucunun gerçek karakter kodlamasını mümkün olduğunca koru.
        response.encoding = response.encoding or response.apparent_encoding
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        msg = str(e)
        short = msg[-100:] if len(msg) > 100 else msg
        print(f"Hata::Sayfa çekilemedi - {url}")
        print(f"Hata detayı::{msg}")
        return None
        
# Bölüm URL'sinden ana roman sayfasının URL'sini bulur
def find_novel_base_url(chapter_url):
    """Bölüm URL'sinden mümkün olan roman ana URL'sini çıkarır.

    Örnek:
        https://site.com/novel/my-novel/chapter-123/foo
    ->  https://site.com/novel/my-novel/
    """
    if not chapter_url:
        return chapter_url

    parsed = urlparse(chapter_url)
    path_parts = [part for part in parsed.path.split("/") if part]

    # URL içinde "chapter-123", "chapter", "bölüm" vb. bir parça bul.
    chapter_index = None
    for i, part in enumerate(path_parts):
        if re.search(r"(?:chapter|bölüm)[-_]?\d*", part, re.IGNORECASE):
            chapter_index = i
            break

    if chapter_index is None:
        return chapter_url.rstrip("/") + "/"

    base_path = "/" + "/".join(path_parts[:chapter_index]) + "/"
    return f"{parsed.scheme}://{parsed.netloc}{base_path}"

def get_total_chapters(novel_base_url):
    """Novel ana sayfasından toplam bölüm sayısını mümkün olduğunca güvenilir biçimde bulur."""
    print(f"Toplam bölüm sayısı kontrol ediliyor: {novel_base_url}")
    soup = fetch_page(novel_base_url)
    if not soup:
        print("Hata: Toplam bölüm sayısı belirlenemedi.")
        return 0

    try:
        # Önce açıkça yazılmış "Chapters: 123" benzeri alanları ara.
        chapter_text = soup.find(
            string=re.compile(r"Chapters\s*:", re.IGNORECASE)
        )
        if chapter_text:
            match = re.search(r"Chapters\s*:\s*(\d+)", chapter_text, re.IGNORECASE)
            if match:
                total = int(match.group(1))
                print(f"Toplam bölüm: {total}")
                return total

        # "999+" / "1000+" gibi rozetler kesin sayı değildir.
        badge_tag = soup.find("span", string=lambda t: t and "+" in t)
        if badge_tag:
            badge_text = badge_tag.get_text(" ", strip=True)
            if re.fullmatch(r"\d+\+", badge_text):
                print(f"Bölüm rozeti bulundu: {badge_text} (kesin sayı değil)")

        # Sayfadaki tüm chapter-N bağlantılarından en büyük numarayı al.
        numbers = []
        for tag in soup.find_all("a", href=True):
            match = re.search(
                r"(?:chapter|bölüm)[-_]?(\d+)",
                tag["href"],
                re.IGNORECASE,
            )
            if match:
                numbers.append(int(match.group(1)))

        if numbers:
            total_count = max(numbers)
            print(f"Bağlantılardan tespit edilen en yüksek bölüm: {total_count}")
            return total_count

        print("Uyarı: Toplam bölüm sayısı belirlenemedi. 0 olarak ayarlandı.")
        return 0

    except Exception as e:
        print(f"Toplam bölüm sayısı çekilirken hata oluştu: {e}")
        return 0

def find_next_page_url(soup, current_url):
    """Sayfadaki 'Next' bağlantısını bulur ve mutlak URL döndürür."""
    try:
        next_link = soup.find(
            "a",
            attrs={"title": re.compile(r"Next|Sonraki", re.IGNORECASE)},
        )

        if not next_link:
            next_link = soup.find(
                "a",
                string=re.compile(r"^\s*(Next|Sonraki)\s*$", re.IGNORECASE),
            )

        if not next_link:
            # Next yazısı bir span içindeyse üstteki <a> etiketini kullan.
            span_next = soup.find(
                "span",
                string=re.compile(r"^\s*(Next|Sonraki)\s*$", re.IGNORECASE),
            )
            if span_next:
                next_link = span_next.find_parent("a")

        # Bazı sitelerde aria-label kullanılıyor.
        if not next_link:
            next_link = soup.find(
                "a",
                attrs={"aria-label": re.compile(r"Next|Sonraki", re.IGNORECASE)},
            )

        if not next_link or not next_link.get("href"):
            print("Sonraki sayfa linki bulunamadı.")
            return None

        href = next_link["href"].strip()
        if not href or href == "#":
            print("Sonraki sayfa linki yok. İşlem sonlandırılıyor.")
            return None

        # urljoin; /chapter/2, chapter/2 ve https://... biçimlerinin
        # tamamını doğru şekilde çözer.
        next_url = urljoin(current_url, href)
        return next_url

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
        os.makedirs(novel_dir, exist_ok=True)
        print(f"Klasör oluşturuldu: .../{short_dir}")
    else:
        print(f"Klasör zaten mevcut: .../{short_dir}")

    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    short_en = os.path.join("novels", safe_name, source_lang)
    short_tr = os.path.join("novels", safe_name, target_lang)
    if not os.path.exists(en_dir):
        os.makedirs(en_dir, exist_ok=True)
        print(f"Klasör oluşturuldu: .../{short_en}")
    else:
        print(f"Klasör zaten mevcut: .../{short_en}")
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir, exist_ok=True)
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
        text = re.sub(r'[ \t]+', ' ', text)
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
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
    
# Çeviri kütüphanesi: önce deep-translator, yoksa googletrans.
DTTranslator = None
GTTranslator = None
TRANSLATOR_BACKEND = None

# ============================================================
# GOOGLE TRANSLATE
# ============================================================

try:
    from googletrans import Translator as GTTranslator

    TRANSLATOR_BACKEND = "google"

except Exception as e:

    GTTranslator = None
    TRANSLATOR_BACKEND = None

    print("Google Translate kütüphanesi yüklenemedi.")
    print(f"Import hatası: {e}")
    print()
    print("Kurulum için:")
    print("python -m pip install -U googletrans")
    
    
def translate_text_en_to_tr(text, control=None, source_lang='en', target_lang='tr', chapter_num=None):
    """
    Metni Google Translate ile çevirir.

    Kurallar:
    - Uzun metinleri parçalara böler.
    - Her parça en fazla 3 kez denenir.
    - 3 denemede de başarısız olursa parçanın ORİJİNALİ kullanılır.
    - Başarısız parça nedeniyle bölüm durmaz.
    - Sonraki parçaya mutlaka geçilir.
    - Böylece hiçbir parça boş bırakılmaz.
    """

    if GTTranslator is None:
        print("Google Translate kullanılamıyor.")
        return text

    try:
        translator = GTTranslator()

        # ---------------------------------------------------------
        # METNİ PARÇALARA AYIR
        # ---------------------------------------------------------
        if len(text) > 4500:
            chunks = _split_chunks(text)
        else:
            chunks = [text]

        result = []

        total_chunks = len(chunks)

        # ---------------------------------------------------------
        # HER PARÇAYI AYRI AYRI ÇEVİR
        # ---------------------------------------------------------
        for i, chunk in enumerate(chunks):

            # Durdurma kontrolü
            if control and control.stop_event.is_set():
                return None

            # Duraklatma kontrolü
            if control and not control.pause_event.is_set():
                control.pause_event.wait()

            chunk_number = i + 1

            if chapter_num:
                print(
                    f"Bölüm {chapter_num} - "
                    f"Parça {chunk_number}/{total_chunks} çevriliyor..."
                )
            else:
                print(
                    f"Parça {chunk_number}/{total_chunks} çevriliyor..."
                )

            # -----------------------------------------------------
            # ÖNEMLİ:
            # Başlangıç değeri ORİJİNAL PARÇA.
            #
            # Çeviri başarısız olursa bu değer korunacak.
            # Böylece parça ASLA boş kalmayacak.
            # -----------------------------------------------------
            translated_chunk = chunk
            translation_success = False

            max_retries = 3

            # -----------------------------------------------------
            # 3 DENEME
            # -----------------------------------------------------
            for attempt in range(1, max_retries + 1):

                # Durdurma kontrolü
                if control and control.stop_event.is_set():
                    return None

                # Duraklatma kontrolü
                if control and not control.pause_event.is_set():
                    control.pause_event.wait()

                try:

                    # Google Translate isteği
                    response = translator.translate(
                        chunk,
                        src=source_lang,
                        dest=target_lang
                    )

                    if response and response.text:
                        translated_chunk = response.text
                        translation_success = True
                        break

                except Exception as e:

                    error_text = str(e)

                    print(
                        f"Çeviri parçası hatası "
                        f"(deneme {attempt}/{max_retries}): {error_text}"
                    )

                    # Son deneme değilse bekle
                    if attempt < max_retries:

                        # Rate limit durumunda daha uzun bekle
                        if (
                            "too many requests" in error_text.lower()
                            or "429" in error_text
                            or "server error" in error_text.lower()
                        ):
                            wait_time = 5 * attempt
                        else:
                            wait_time = 3 * attempt

                        print(
                            f"Tekrar denenecek... "
                            f"{wait_time} saniye bekleniyor."
                        )

                        # Beklerken durdurma kontrolünü de yap
                        for _ in range(wait_time * 10):
                            if control and control.stop_event.is_set():
                                return None

                            time.sleep(0.1)

            # -----------------------------------------------------
            # 3 DENEME DE BAŞARISIZSA
            # ORİJİNAL PARÇA KULLANILACAK
            # -----------------------------------------------------
            if not translation_success:

                print(
                    f"Bölüm {chapter_num if chapter_num else ''} "
                    f"Parça {chunk_number}/{total_chunks} "
                    f"3 denemede çevrilemedi."
                )

                print(
                    "Bu parça orijinal haliyle kaydedilecek ve "
                    "sonraki parçaya geçilecek."
                )

                # translated_chunk zaten ORİJİNAL chunk
                translated_chunk = chunk

            # -----------------------------------------------------
            # PARÇAYI SONUCA EKLE
            #
            # Başarılı veya başarısız olması fark etmez.
            # ASLA boş bırakılmayacak.
            # -----------------------------------------------------
            result.append(translated_chunk)

            # -----------------------------------------------------
            # Google'a arka arkaya çok hızlı istek göndermeyelim.
            # -----------------------------------------------------
            if chunk_number < total_chunks:
                time.sleep(1.2)

        # ---------------------------------------------------------
        # TÜM PARÇALARI BİRLEŞTİR
        # ---------------------------------------------------------
        final_text = "\n".join(result)

        # Güvenlik:
        # Sonuç nedense boşsa orijinal metni döndür.
        if not final_text.strip():
            return text

        return final_text

    except Exception as e:

        print(f"Çeviri genel hatası: {e}")

        # Genel hata durumunda bile metni kaybetme.
        return text
        
def list_untranslated_chapters(novel_dir):
    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    
    if not os.path.exists(en_dir):
        return []
    if not os.path.exists(tr_dir):
        os.makedirs(tr_dir, exist_ok=True)
    
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
    """Metni mümkün olduğunca paragraf sınırlarını koruyarak parçalara böler."""
    if not text:
        return []

    chunks = []
    current = []

    def flush():
        if current:
            chunks.append("\n".join(current))
            current.clear()

    for paragraph in text.splitlines():
        paragraph = paragraph.strip()

        if not paragraph:
            if current and len("\n".join(current)) + 1 <= max_length:
                current.append("")
            continue

        candidate = "\n".join(current + [paragraph])
        if len(candidate) <= max_length:
            current.append(paragraph)
            continue

        flush()

        # Tek bir paragraf limitten uzunsa onu da böl.
        while len(paragraph) > max_length:
            chunks.append(paragraph[:max_length])
            paragraph = paragraph[max_length:]

        if paragraph:
            current.append(paragraph)

    flush()
    return chunks
'''
def _print_progress_bar(chapter_num, current_chapter_index, total_chapters, control):
    while not control.stop_progress_bar:
        sys.stdout.write(f"\rBölüm {chapter_num} çevriliyor... ({current_chapter_index}/{total_chapters})")
        sys.stdout.flush()
        time.sleep(0.01)
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()
'''
def translate_chapters(
    novel_dir,
    chapters,
    control=None,
    start_from=0,
    limit=None,
    source_lang="en",
    target_lang="tr",
):
    if TRANSLATOR_BACKEND is None:
        return 0

    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    os.makedirs(tr_dir, exist_ok=True)

    if limit is None:
        chapters_to_translate = chapters[start_from:]
    else:
        chapters_to_translate = chapters[start_from:start_from + limit]

    total_translated = 0
    total_to_translate = len(chapters_to_translate)

    for i, (chapter_num, filename) in enumerate(chapters_to_translate):
        if control and control.stop_event.is_set():
            last_chapter = (
                chapters_to_translate[i - 1][0] if i > 0 else 0
            )
            save_translation_progress(
                novel_dir, last_chapter, total_translated
            )
            return -1

        if control:
            control.pause_event.wait()
            if control.stop_event.is_set():
                save_translation_progress(
                    novel_dir,
                    chapters_to_translate[i - 1][0] if i > 0 else 0,
                    total_translated,
                )
                return -1
            control.stop_progress_bar.clear()

        progress_thread = None
        if control:
            progress_thread = threading.Thread(
                target=_print_progress_bar,
                args=(chapter_num, i + 1, total_to_translate, control),
                daemon=True,
            )
            progress_thread.start()

        en_file = os.path.join(en_dir, filename)
        tr_file = os.path.join(tr_dir, filename)

        try:
            with open(en_file, "r", encoding="utf-8") as f:
                content = f.read()

            if control:
                control.stop_progress_bar.set()
                progress_thread.join()

            translated = translate_text_en_to_tr(
                content,
                control,
                source_lang,
                target_lang,
                chapter_num,
            )

            if translated:
                with open(tr_file, "w", encoding="utf-8") as f:
                    f.write(translated)

                total_translated += 1
                save_translation_progress(
                    novel_dir, chapter_num, total_translated
                )
                print(
                    f"Bölüm {chapter_num} çevrildi ve kaydedildi. "
                    f"({total_translated}/{total_to_translate})"
                )
            else:
                print(f"Bölüm {chapter_num} çevrilemedi.")

        except Exception as e:
            print(f"Bölüm {chapter_num} işlenirken hata: {e}")
        finally:
            if control:
                control.stop_progress_bar.set()
                if progress_thread and progress_thread.is_alive():
                    progress_thread.join(timeout=1)

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
                translated = translate_chapters(
                    novel_dir, items, control, 0, limit if limit > 0 else None
                )
                control.stop_event.set()
                control.stop_progress_bar.set()
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            except ValueError:
                translated = translate_chapters(novel_dir, items, control)
                control.stop_event.set()
                control.stop_progress_bar.set()
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
            downloaded_count = len([
                f for f in os.listdir(os.path.join(novel_dir, "en"))
                if f.startswith("chapter_") and f.endswith(".txt")
            ])

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
        # pause_event SET ise işlem devam eder.
        # CLEAR ise işlem duraklatılmıştır.
        self.pause_event = threading.Event()
        self.pause_event.set()

        # İşlemi tamamen durdur.
        self.stop_event = threading.Event()
        self.stop_event.clear()

        # T tuşu ile ana menüye dönme isteği.
        self.return_to_menu = False

        # Progress bar thread'ini durdur.
        self.stop_progress_bar = threading.Event()
        self.stop_progress_bar.set()

        # Keyboard listener'ın kapanmasını istemek için.
        self.keyboard_stop = threading.Event()

    def request_stop(self, return_to_menu=False):
        self.return_to_menu = return_to_menu
        self.stop_event.set()
        self.pause_event.set()  # wait() durumunda kalmışsa serbest bırak.


def _print_progress_bar(chapter_num, current_chapter_index, total_chapters, control):
    while not control.stop_progress_bar.is_set():
        sys.stdout.write(
            f"\rBölüm {chapter_num} çevriliyor... "
            f"({current_chapter_index}/{total_chapters})"
        )
        sys.stdout.flush()
        time.sleep(0.1)

    sys.stdout.write("\r" + " " * 100 + "\r")
    sys.stdout.flush()


def start_keyboard_listener(control):
    """
    Windows konsolunda P/R/S/T tuşlarını dinler.

    P = Duraklat
    R = Devam
    S = Durdur ve işlemi sonlandır
    T = Durdur ve ana menüye dön

    Her Control nesnesi için yalnızca bir listener oluşturulur.
    """
    def keyboard_listener():
        try:
            import msvcrt
        except ImportError:
            return

        print("      Kontroller: [P]-Duraklat  [R]-Devam  [S]-Durdur  [T]-Ana Menü")
        print("_____________________________________________________________________________________")

        while not control.keyboard_stop.is_set():
            try:
                if msvcrt.kbhit():
                    raw = msvcrt.getch()

                    # Normal ASCII karakterler.
                    if raw in (b'p', b'P'):
                        control.pause_event.clear()
                        print("\n[Duraklatıldı - devam için 'R']")

                    elif raw in (b'r', b'R'):
                        control.pause_event.set()
                        print("\n[Devam ediliyor]")

                    elif raw in (b's', b'S'):
                        control.request_stop(return_to_menu=False)
                        print("\n[Durdurma talebi alındı]")

                    elif raw in (b't', b'T'):
                        control.request_stop(return_to_menu=True)
                        print("\n[Ana menüye dönülüyor...]")

                    # Özel tuşların ikinci byte'ını temizle.
                    elif raw in (b'\x00', b'\xe0'):
                        if msvcrt.kbhit():
                            msvcrt.getch()

            except (OSError, ValueError):
                break

            time.sleep(0.05)

    try:
        import msvcrt
    except ImportError:
        print("Klavye kısayolları yalnızca Windows konsolunda kullanılabilir.")
        return None

    thread = threading.Thread(
        target=keyboard_listener,
        daemon=True,
        name="NovelKeyboardListener"
    )
    thread.start()
    return thread


def stop_keyboard_listener(control):
    """Keyboard listener thread'inin kapanmasını ister."""
    control.keyboard_stop.set()
    control.pause_event.set()
    control.stop_progress_bar.set()


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

            parsed_start = urlparse(start_url)
            if parsed_start.scheme not in ("http", "https") or not parsed_start.netloc:
                print("Geçerli bir http/https URL girmelisiniz.")
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
                stop_keyboard_listener(control)
                return

            stop_keyboard_listener(control)
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
                            
                        stop_keyboard_listener(control)
                        print(f"\nİşlem tamamlandı. Toplam {pages_downloaded} sayfa indirildi.")
                        
                    except KeyboardInterrupt:
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        stop_keyboard_listener(control)
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