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
    
# Desteklenen diller ve kodları
source_lang = "en"
target_lang = "tr"

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

# Novelin ana sayfasından toplam bölüm sayısını çeker
def get_total_chapters(novel_base_url):
    # Novelin ana sayfasından toplam bölüm sayısını çeker.
    print(f"Toplam bölüm sayısı kontrol ediliyor: {novel_base_url}")
    soup = fetch_page(novel_base_url)
    if not soup:
        print("Hata: Toplam bölüm sayısı belirlenemedi.")
        return 0
    
    try:
        # <p><strong>Chapters: </strong> <span>4720</span></p> yapısını ara
        strong_tag = soup.find('strong', string=lambda t: t and 'Chapters:' in t)
        
        if strong_tag and strong_tag.parent:
            # strong'un kardeşi olan span etiketini bul
            span_tag = strong_tag.parent.find('span')
            
            if span_tag:
                count_text = span_tag.get_text(strip=True)
                if count_text.isdigit():
                    print(f"Başarılı: Toplam bölüm sayısı: {count_text}")
                    return int(count_text)
        
        print("Uyarı: Toplam bölüm sayısı bilgisi ('Chapters: XX') sayfada bulunamadı. 0 olarak ayarlandı.")
        return 0
    except Exception as e:
        print(f"Toplam bölüm sayısı çekilirken hata oluştu: {e}")
        return 0
        
def find_next_page_url(soup, current_url):
    ## Sonraki sayfa linkini bulur.
    try:
        # NovelBuddy.io sitesinin yeni yapısına göre sonraki sayfa linki 'btn-next' id'si ile
        next_link = soup.find('a', id='btn-next')
        
        if next_link and next_link.get('href'):
            next_url = next_link['href']
            
            # **Yeni Kontrol:** Eğer href='#' ise, bu son sayfa demektir.
            if next_url == '#':
                print("Sonraki sayfa linki '#' olarak bulundu. Bu son bölümdür. İşlem sonlandırılıyor.")
                return None
            
            # Göreceli URL'yi mutlak URL'ye dönüştür
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
    no_words = ['read', 'mtl', '-', 're:', ',','.']
    
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
    # kaynak_dil en ve çevrilecek_dil tr alt klasörlerini oluştur
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
    
    # EN klasörüne kaydet
    en_dir = os.path.join(novel_dir, source_lang)
    file_path = os.path.join(en_dir, f"chapter_{chapter_number:04d}.txt")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        # Dosya yolunu kısalt
        short_path = os.path.join(source_lang, os.path.basename(file_path))
        print(f"Bölüm:{chapter_number} ::-> İçerik: {len(content)}: karakter :{short_path} kaydedildi::....")
        return True
    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")
        return False
        
# İçerik çıkarma başarısız olursa, div#chapter-content'i deneyecek yedek mekanizma eklendi.
def extract_novel_content(soup):
    try:
        # Tüm HTML'yi metin olarak al
        html = soup.decode()
        
        inner_html = None
        
        # INFOLINKS_ON ile INFOLINKS_OFF arasındaki içeriği eksiksiz alır.
        #match = re.search(r'(.*?)', html, re.DOTALL | re.IGNORECASE)
        match = re.search(r'<!--INFOLINKS_ON-->(.*?)<!--INFOLINKS_OFF-->', html, re.DOTALL | re.IGNORECASE)
        if match:
            inner_html = match.group(1)
        else:
            # 2. Yedek Yöntem: Yaygın Bölüm İçerik Etiketleri
            # NovelBuddy/Yaygın ID
            content_div = soup.find('div', id='chapter-content')
            if not content_div:
                # Yaygın class Sınıfı çalışıyor...
                content_div = soup.find('div', class_='content-inner') 
            
            if content_div:
                inner_html = str(content_div)
            else:
                # Kullanıcıdan gelen hatayı önlemek için daha açıklayıcı uyarı
                print("Uyarı: INFOLINKS veya bilinen içerik etiketi bulunamadı.") 
                return None
                
        if not inner_html:
             print("Uyarı: İçerik HTML'i boş.")
             return None
             
        # İçeriği metne çevirirken satır sonlarını koru
        inner_soup = BeautifulSoup(inner_html, 'html.parser')
        
        for tag in inner_soup(['script', 'style']):
            tag.decompose()
        text = inner_soup.get_text(separator='\n')
        
        # Satır sonlarını ve boşlukları normalize et
        text = re.sub(r'\r\n?', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        text = re.sub(r'\n{2,}', '\n', text)
        
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
        
def find_novel_base_url(chapter_url):
    # Kaba tahmin: URL'nin son chapter-XXXX kısmını kaldır.
    # Örn: https://.../novel-name/chapter-10/ -> https://.../novel-name/
    parts = chapter_url.split('/')
    # Eğer son parça 'chapter-' ile başlıyorsa, onu at.
    if parts[-1].startswith('chapter-'):
        return '/'.join(parts[:-1]) + '/'
    # Eğer chapter linki değilse, bir önceki seviyeye dön
    return '/'.join(parts[:-1])

def get_total_chapters(novel_base_url):
    # Novelin ana sayfasından toplam bölüm sayısını çeker.
    print(f"Toplam bölüm sayısı için ana sayfa kontrol ediliyor: {novel_base_url}")
    soup = fetch_page(novel_base_url)
    if not soup:
        print("Hata: Ana sayfa çekilemedi, toplam bölüm sayısı belirlenemedi.")
        return 0
    
    try:
        # <p><strong>Chapters: </strong> <span>4720</span></p> yapısını ara
        strong_tag = soup.find('strong', string=lambda t: t and 'Chapters:' in t)
        
        if strong_tag and strong_tag.parent:
            # strong'un kardeşi olan span etiketini bul
            span_tag = strong_tag.parent.find('span')
            
            if span_tag:
                count_text = span_tag.get_text(strip=True)
                if count_text.isdigit():
                    print(f"Başarılı: Toplam bölüm sayısı: {count_text}")
                    return int(count_text)
        
        print("Uyarı: Toplam bölüm sayısı bilgisi ('Chapters: XX') sayfada bulunamadı. 0 olarak ayarlandı.")
        return 0
    except Exception as e:
        print(f"Toplam bölüm sayısı çekilirken hata oluştu: {e}")
        return 0        
    
# GÜNCELLENDİ: total_chapters parametresi eklendi
def save_progress(novel_dir, chapter_number, current_url, total_chapters=0):
    ##İlerlemeyi novel klasörüne progress.json olarak yazar.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        data = {
            "chapter_number": chapter_number,
            "current_url": current_url,
            "total_chapters": total_chapters # Eklendi
        }
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # URL'yi kısaltarak göster
        short_url = current_url.split('/')[-1] if '/' in current_url else current_url
        if len(short_url) > 50:
            short_url = short_url[:47] + "..."
        # Çıktıya total_chapters bilgisini de ekle
        print(f"İlerleme kaydedildi: bölüm={chapter_number}, url=.../{short_url}, toplam={total_chapters}")
    except Exception as e:
        print(f"İlerleme kaydedilemedi: {e}")
        
# total_chapters yüklemesi ve görüntülemesi yapıldı
def load_progress(novel_dir, print_message=False):
    ##Novel klasöründeki progress.json'ı okur.
    try:
        progress_path = os.path.join(novel_dir, "progress.json")
        if os.path.exists(progress_path):
            with open(progress_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Tüm gerekli anahtarları güvenli bir şekilde al, yoksa varsayılan değerler ata.
            chapter_num = data.get("chapter_number", 1)
            current_url = data.get("current_url", "N/A")
            # total_chapters bilgisini güvenle al, yoksa 0 varsay.
            total_chapters = data.get("total_chapters", 0) 

            if print_message:
                # URL'yi kısaltarak göster
                short_url = current_url.split('/')[-1] if '/' in current_url else current_url
                if len(short_url) > 50:
                    short_url = short_url[:47] + "..."
                print("--------------------------------------------------------------------------")
                # Toplam bölüm sayısını da göster
                print(f"Mevcut ilerleme bulundu: bölüm={chapter_num}, toplam={total_chapters}, url=.../{short_url}")
            
            # Veriyi döndürmeden önce tüm anahtarları ekle (güvenlik için)
            data["chapter_number"] = chapter_num
            data["current_url"] = current_url
            data["total_chapters"] = total_chapters
            return data
    except Exception as e:
        if print_message: 
            print(f"İlerleme yüklenemedi: {e}")
        # Hata durumunda veya dosya yoksa varsayılan boş bir ilerleme nesnesi döndür
        
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
        print("Yüklemek için: py pip install deep-translator  veya  py -m pip install googletrans==4.0.0-rc1")

# Çeviri Fonksionu    
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
                    
                    sys.stdout.write(f"\rBölüm {chapter_num} - Parça {i + 1}/{len(chunks)} Deep ile çevriliyor... ")
                    sys.stdout.flush()

                    retry_count = 0
                    max_retries = 2  # Maksimum tekrar deneme sayısı (toplamda 3 deneme: 1 ilk deneme + 2 tekrar)

                    while retry_count <= max_retries:
                        try:
                            # **1. Çeviri İşlemi**
                            translated = translator.translate(chunk)
                            break  # Başarılı olursa döngüden çık
                        except Exception as e:
                            # **2. Hata Durumu**
                            if retry_count < max_retries:
                                # Tekrar deneme hakkı varsa
                                retry_count += 1
                                print(f"Çeviri hatası Parça:{i + 1}, Çeviri Tekrar Deneniyor. :(Deneme {retry_count + 1}/{max_retries + 1}):")
                                # İsteğe bağlı: Kısa bir bekleme ekleyebilirsiniz (örn: time.sleep(1))
                                continue  # Döngünün başına dön ve tekrar dene
                            else:
                                # Tekrar deneme hakkı kalmadıysa
                                print(f"Çeviri hatası: Parça:{i + 1}: :: Maksimum Denemeye Ulaşıldı. Parça Orjinal Olarak Kaydedildi.")
                                translated = chunk  # Hata veren parçayı orijinal hâliyle ekle
                                break # Hata kaydedildi, döngüden çık

                    # Bu noktada 'translated' değişkeninde ya başarılı çeviri ya da orijinal 'chunk' olacaktır.
                    
                    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
                    sys.stdout.flush()
                    result.append(translated)
                    time.sleep(1)
                return '\n'.join(result)
            else:
                try:
                    return translator.translate(text)
                except Exception as e:
                    #msg = str(e)
                    #short = msg[-168:] if len(msg) > 168 else msg
                    print(f"Çeviri hatası:::Orjinal Olarak Kaydedildi.")
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
                    
                    sys.stdout.write(f"\rBölüm {chapter_num} - Parça {i + 1}/{len(chunks)} Foogle ile çevriliyor... ")
                    sys.stdout.flush()
                    
                    retry_count = 0
                    max_retries = 2  # Maksimum tekrar deneme sayısı (toplamda 3 deneme: 1 ilk deneme + 2 tekrar)

                    while retry_count <= max_retries:
                        try:
                            # **1. Çeviri İşlemi**
                            # GTTranslator'ı fonksiyon içinde çağır
                            from googletrans import Translator as GTTranslator
                            translator = GTTranslator()
                            translated = translator.translate(chunk, src=source_lang, dest=target_lang).text
                            break  # Başarılı olursa döngüden çık
                        except Exception as e:
                            # **2. Hata Durumu**
                            if retry_count < max_retries:
                                # Tekrar deneme hakkı varsa
                                retry_count += 1
                                print(f"Çeviri hatası Parça:{i + 1}, Çeviri Tekrar Deneniyor. :(Deneme {retry_count + 1}/{max_retries + 1}):")
                                # İsteğe bağlı: Kısa bir bekleme ekleyebilirsiniz (örn: time.sleep(1))
                                continue  # Döngünün başına dön ve tekrar dene
                            else:
                                # Tekrar deneme hakkı kalmadıysa
                                print(f"Foogle Çeviri hatası: Parça:{i + 1}:: Maksimum Denemeye Ulaşıldı. Parça Orjinal Olarak Kaydedildi.")
                                translated = chunk  # Hata veren parçayı orijinal hâliyle ekle
                                break # Hata kaydedildi, döngüden çık

                    # Bu noktada 'translated' değişkeninde ya başarılı çeviri ya da orijinal 'chunk' olacaktır.
                    
                    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
                    sys.stdout.flush()
                    result.append(translated)
                    time.sleep(1)
                return '\n'.join(result)
            else:
                try:
                    # GTTranslator'ı fonksiyon içinde çağır
                    from googletrans import Translator as GTTranslator
                    translator = GTTranslator()
                    return translator.translate(text, src=source_lang, dest=target_lang).text
                except Exception as e:
                    #msg = str(e)
                    #short = msg[-168:] if len(msg) > 168 else short
                    print(f"Çeviri hatası:::Orjinal Olarak Kaydedildi.")
                    return text  # Tek parça hatasında orijinal metni döndür
    except Exception as e:
        msg = str(e)
        short = msg[-168:] if len(msg) > 168 else short
        #print(f"Çeviri hatası: {short}:::Orjinal Olarak Kaydedildi.")
        print(f"Çeviri Yapılamadı::::Orjinal Olarak Kaydedildi.")
        return text  # Genel hatada da orijinal metinle akışı sürdür
def list_untranslated_chapters(novel_dir):
    ##Çevrilmemiş bölümleri listeler.
    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
    
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
        #progress_percentage = (current_chapter_index / total_chapters)
        #filled_length = int(20 * progress_percentage)
        #bar = '█' * filled_length + '-' * (20 - filled_length)
        #sys.stdout.write(f"\rBölüm {chapter_num} çevriliyor... ({current_chapter_index}/{total_chapters}) [{bar}]")
        sys.stdout.write(f"\rBölüm {chapter_num} çevriliyor... ({current_chapter_index}/{total_chapters})")
        sys.stdout.flush()
        time.sleep(0.01)
    sys.stdout.write("\r" + " " * 80 + "\r") # Clear the line
    sys.stdout.flush()

def translate_chapters(novel_dir, chapters, control=None, start_from=0, limit=None, source_lang="en", target_lang="tr"):
    ##Belirtilen bölümleri çevirir.
    if TRANSLATOR_BACKEND is None:
        print("Çeviri yapılamıyor: Çeviri kütüphanesi yüklü değil.")
        return 0
    en_dir = os.path.join(novel_dir, source_lang)
    tr_dir = os.path.join(novel_dir, target_lang)
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
                if limit == None:
                    ##Çeviri menüsünü gösterir ve işlemleri yönetir.
                    items = list_untranslated_chapters(novel_dir)
                    limit = len(items)
                    limit += 1
                print(f"Bölüm {chapter_num} çevrildi ve kaydedildi. ({total_translated}/{limit})")
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
    print("\n------------------------------------------------------------------------------------")
    print(f"\n[Çeviri] Novel: {os.path.basename(novel_dir)} | Çevrilmemiş bölüm sayısı: {total}")
    print("------------------------------------------------------------------------------------\n")
    if total:
        # Global dil ayarlarını kullan
        print(f"Çeviri dilleri: Kaynak: {source_lang}, Hedef: {target_lang}")

        show_all = input("Tam liste gösterilsin mi? (E/H): ").strip().lower()
        print("--------------------------------------------------------------------------")
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
                #print("--------------------------------------------------------------------------\n")
                control = Control()
                start_keyboard_listener(control)
                
                print("\nÇeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                print("--------------------------------------------------------------------------")
                translated = translate_chapters(novel_dir, items, control, start_idx, total, source_lang, target_lang)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
                return
        
        print("\nÇevrilecek bölümleri seçin:")
        print("     1. Tek bölüm      2. Bölüm aralığı  3. Tüm bölümleri  M. Ana menüye dön")
        #print("2. Bölüm aralığı  ")
        #print("3. Tüm bölümleri  ")
        #print("M. Ana menüye dön ")
        
        choice = input("Seçiminiz (1/2/3/M): ").strip()
        #print("--------------------------------------------------------------------------")
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
                print("\n--------------------------------------------------------------------------")
                translated = translate_chapters(novel_dir, selected_items, control, 0, total, source_lang, target_lang)
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
                #print("\n--------------------------------------------------------------------------")
                print(f"\n{len(selected_items)} bölüm çevrilecek ({start_num}-{end_num})...")
                print("Çeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                print("--------------------------------------------------------------------------")
                translated = translate_chapters(novel_dir, selected_items, control, 0, total, source_lang, target_lang)
                if translated == -1:
                    return
                print(f"\nÇeviri tamamlandı. {translated} bölüm çevrildi.")
            
            except ValueError:
                print("Geçersiz bölüm numarası.")
        
        elif choice == "3":
            limit_input = input("Kaç bölüm çevrilsin? (0=tümü): ").strip()
            try:
                limit = int(limit_input)
                if limit == 0:
                    limit = total
                
                print(f"\nToplam {limit} bölüm çevrilecek...")
                print("Çeviri başlıyor... (Duraklatmak için 'P', durdurmak için 'S' tuşuna basın)")
                print("--------------------------------------------------------------------------\n")
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

# Bu fonksiyonun güncellenmiş versiyonu list_saved_novels'tan önce olmalı.
def list_downloaded_novels():
    ##İndirilmiş # Novelleri listeler.
    novels_dir = os.path.join(os.getcwd(), "novels")
    if not os.path.exists(novels_dir):
        print("Henüz indirilmiş roman bulunmuyor.")
        return []
    
    novels = []
    for item in os.listdir(novels_dir):
        novel_dir = os.path.join(novels_dir, item)
        if os.path.isdir(novel_dir) and os.path.exists(os.path.join(novel_dir, "en")):
            progress_data = load_progress(novel_dir)
            
            # total_chapters'ı al
            total_chapters = progress_data.get('total_chapters', 0) if progress_data else 0 

            # İndirilen bölüm sayısını hesapla
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
    # Novel seçim menüsünü gösterir.
    novels = list_downloaded_novels()
    
    if not novels:
        print("Çevrilecek roman bulunamadı.")
        return None
    
    print("Kayıtlı Noveller:")
    for i, novel_data in enumerate(novels, 1):
        total_info = f"/{novel_data['total_chapters']}" if novel_data['total_chapters'] > 0 else ""
        print(f"{i}. {novel_data['name']} (Çevrilmemiş Bölüm: {novel_data['untranslated_count']}{total_info})")
    
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
    print("--------------------------------------------------------------------------\n")
    return choice

# Kayıtlı Noveller Listesi
def list_saved_novels():
    novels_dir = os.path.join(os.getcwd(), "novels")
    saved_novels = []
    if os.path.exists(novels_dir):
        for novel_name in os.listdir(novels_dir):
            novel_path = os.path.join(novels_dir, novel_name)
            if os.path.isdir(novel_path):
                # progress'i sessizce yükle (print_message=False)
                progress_data = load_progress(novel_path, print_message=False)
                
                # 1. İndirilen bölüm sayısını hesapla (EN klasöründeki dosyalar)
                en_dir = os.path.join(novel_path, source_lang)
                total_downloaded = 0
                if os.path.exists(en_dir):
                    total_downloaded = len([f for f in os.listdir(en_dir) if f.startswith("chapter_") and f.endswith(".txt")])

                # Sadece geçerli ilerlemesi olanları listele
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
            print("========================================================")
            print("Kontroller: P=Duraklat, R=Devam, S=Durdur, T=Ana Menü")
            print("--------------------------------------------------------")
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
            # sys.stdin.fileno() ile standart Linux/macOS girişi de dinlenebilir,
            # ancak basitlik için bu uyarıyı tutuyorum.
            print("Uyarı: Windows dışı sistemde klavye dinleyici çalışmayabilir.")
    
    # msvcrt sadece Windows'ta olduğu için kontrol et
    try:
        import msvcrt
        threading.Thread(target=keyboard_listener, daemon=True).start()
    except ImportError:
        # msvcrt yoksa (Linux/macOS) dinleyiciyi başlatma
        print("Uyarı: Klavye dinleyici sadece Windows'ta aktiftir (P/R/S/T tuşları).")
    
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
            # Yeni İndirme akışı
            start_url = input("Novelin ilk sayfasının URL'sini girin: ").strip()
            if not start_url:
                print("Geçerli bir URL girmelisiniz.")
                continue

            try:
                page_limit = int(input("Kaç sayfa indirilsin? (0 = sınırsız): "))
                print("------------------------------------------------------------------------")
                if page_limit < 0:
                    page_limit = 0
            except ValueError:
                print("Geçersiz sayı, sınırsız olarak devam ediliyor.")
                page_limit = 0

            # Total Chapters'ı çek
            novel_base_url = find_novel_base_url(start_url)
            total_chapters = get_total_chapters(novel_base_url) 
            # --------------------------------

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
                    
                    # Sayfa sınırı
                    if page_limit > 0 and pages_downloaded >= page_limit:
                        print(f"Sayfa sınırına ulaşıldı ({page_limit} sayfa). İlerleme kaydediliyor...")
                        # total_chapters bilgisini kaydet
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    # Durdurma talebi
                    if control.stop_event.is_set():
                        print("Durdurma talebi alındı. İlerleme kaydediliyor...")
                        # total_chapters bilgisini kaydet
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    # Duraklatma
                    control.pause_event.wait()
                    
                    # İndirme oturumu limiti bilgisi: (1/2), (2/2) vs.
                    session_limit_display = page_limit if page_limit > 0 else '∞'
                    session_progress_info = f" ({pages_downloaded+1}/{session_limit_display})"
                    
                    # GÜNCELLENDİ: Sadece istenen çıktı formatı. (Kullanıcı isteği: URL ve Toplam bilgisi kaldırıldı.)
                    print(f"\nBölüm {chapter_number} indiriliyor... {session_progress_info}")

                    soup = fetch_page(current_url)
                    if not soup:
                        # total_chapters bilgisini kaydet
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        print("Sayfa çekilemedi. Kalınan yer kaydediliyor.")
                        break

                    content = extract_novel_content(soup)
                    if not content:
                        # total_chapters bilgisini kaydet
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        print("İçerik çıkarılamadı (belki reklam veya son sayfa). Kalınan yer kaydediliyor.")
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
                            
                        # Başarılı kayıtta ilerlemeleri artır ve URL'yi güncelle
                        chapter_number += 1
                        pages_downloaded += 1
                        current_url = next_url
                    else:
                        # Kayıt başarısız (dosya hatası): Dur.
                        print("Bölüm kaydedilemedi. İşlem durduruluyor ve ilerleme kaydediliyor.")
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
                        break

                    # Her başarılı indirmeden sonra bekleme
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nCtrl+C yakalandı. İlerleme kaydediliyor...")
                # total_chapters bilgisini kaydet
                save_progress(novel_dir, chapter_number, current_url, total_chapters)
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

            # GÜNCELLENMİŞ LİSTELEME FORMATI
            print("\n==================== Kayıtlı Romanlar ===========================")
            for i, novel in enumerate(saved_novels):
                total_chapters_display = f" -- Toplam Sayfa: {novel['total_chapters']}" if novel['total_chapters'] > 0 else ""
                print(f"{i+1}. {novel['name']} (İndirilen: {novel['downloaded_count']}{total_chapters_display})")
            print("===================================================================")

            try:
                choice = int(input("Devam etmek istediğiniz romanın numarasını girin: ")) - 1
                if 0 <= choice < len(saved_novels):
                    selected_novel = saved_novels[choice]
                    novel_dir = selected_novel['path']
                    novel_name = selected_novel['name']
                    # total_chapters'ı selected_novel'dan al
                    total_chapters = selected_novel['total_chapters']

                    control = Control()
                    start_keyboard_listener(control)

                    progress = load_progress(novel_dir, print_message=True)
                    if progress:
                        current_url = progress.get("current_url")
                        chapter_number = progress.get("chapter_number", 1)
                        if not current_url:
                            if total_chapters > 0 and chapter_number > total_chapters:
                                print(f"Romanın tüm {total_chapters} bölümü zaten indirilmiş görünüyor.")
                            else:
                                print("Kayıtlı ilerleme dosyasında URL bulunamadı veya 'Final' olarak işaretlenmiş. Ana menüye dönülüyor.")
                            continue
                        
                        # total_chapters kontrolü ve güncelleme**
                        if total_chapters == 0:
                            print("\n!! DİKKAT: Toplam bölüm sayısı (0) bulunamadı. Güncelleniyor...")
                            # Base URL'yi bulmak için current_url'yi kullan
                            novel_base_url = find_novel_base_url(current_url) 
                            # Yeni total_chapters'ı çek
                            new_total_chapters = get_total_chapters(novel_base_url)
                            if new_total_chapters > 0:
                                total_chapters = new_total_chapters
                                print(f"Güncel toplam bölüm sayısı bulundu: {total_chapters}")
                                # Hemen progress dosyasını güncelle
                                save_progress(novel_dir, chapter_number, current_url, total_chapters) 
                            else:
                                print("Toplam bölüm sayısı bulunamadı, indirme devam ediyor.")
                        
                        # Novel adı ve bölüm bilgisini göster
                        print(f"\n{novel_name} Novelin {chapter_number}. bölümünden devam edecek...")
                        
                    else:
                        print("Seçilen Novel için ilerleme dosyası bulunamadı. Ana menüye dönülüyor.")
                        continue

                    try:
                        pages_downloaded = 0
                        try:
                            page_limit = int(input("Kaç sayfa indirilsin? (0 = sınırsız): "))
                            print("\n------------------------------------------------------------------------")
                            if page_limit < 0:
                                page_limit = 0
                        except ValueError:
                            print("Geçersiz sayı, sınırsız olarak devam ediliyor.")
                            page_limit = 0
                            
                        # İndirme döngüsü
                        while current_url and current_url.lower() != "final":
                            # Sayfa sınırı
                            if page_limit > 0 and pages_downloaded >= page_limit:
                                print(f"Sayfa Limitine ulaşıldı ({page_limit} sayfa). İlerleme kaydediliyor...")
                                # total_chapters bilgisini kaydet
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            # Durdurma talebi
                            if control.stop_event.is_set():
                                print("Durdurma talebi alındı. İlerleme kaydediliyor...")
                                # total_chapters bilgisini kaydet
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            # Duraklatma
                            control.pause_event.wait()
                            
                            # İndirme oturumu limiti bilgisi: (1/2), (2/2) vs.
                            session_limit_display = page_limit if page_limit > 0 else '∞'
                            session_progress_info = f" ({pages_downloaded+1}/{session_limit_display})"
                            
                            
                            print(f"Bölüm {chapter_number} indiriliyor... {session_progress_info}")

                            soup = fetch_page(current_url)
                            if not soup:
                                # total_chapters bilgisini kaydet
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                print("Sayfa çekilemedi. Kalınan yer kaydediliyor.")
                                break

                            content = extract_novel_content(soup)
                            if not content:
                                # total_chapters bilgisini kaydet
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                print("İçerik çıkarılamadı (belki reklam veya son sayfa). Kalınan yer kaydediliyor.")
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
                                
                                # Başarılı kayıtta ilerlemeleri artır ve URL'yi güncelle
                                chapter_number += 1
                                pages_downloaded += 1
                                current_url = next_url
                            else:
                                # Kayıt başarısız (dosya hatası): Dur.
                                print("Bölüm kaydedilemedi. İşlem durduruluyor ve ilerleme kaydediliyor.")
                                save_progress(novel_dir, chapter_number, current_url, total_chapters)
                                break

                            time.sleep(1)
                            
                        # Döngü sonunda, kaç sayfa indirildiğini göster
                        print(f"\nİşlem tamamlandı. Toplam {pages_downloaded} sayfa indirildi.")
                        
                    except KeyboardInterrupt:
                        print("\nCtrl+C yakalandı. İlerleme kaydediliyor...")
                        # total_chapters bilgisini kaydet
                        save_progress(novel_dir, chapter_number, current_url, total_chapters)
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
        # input("\nHata ayrıntısını görmek için Enter'a basın...")
