# Novel Downloader ve Çevirici

Bu proje, NovelBuddy (ve benzeri) platformlardaki roman bölümlerini indirir, temiz metni çıkarır ve yerel klasöre kaydeder. Ayrıca İngilizce bölümleri Türkçeye çevirir, ilerlemeyi kaydeder ve kaldığı yerden devam edebilir.

## Özellikler
- Bölümleri otomatik olarak indirip `novels/<Roman_Adi>/chapters` klasörüne kaydeder.
- Paragrafları filtreleyerek bölüm metnini temiz şekilde çıkarır.
- İngilizce → Türkçe çeviri yapar; duraklatma/devam/durdurma kontrolü vardır.
- İndirme ve çeviri ilerlemesini JSON dosyalarında saklar.
- Etkileşimli menülerle roman seçimi, indirme ve çeviri yönetimi.

## Gerekli Kütüphaneler
- `requests`: HTTP istekleri
- `beautifulsoup4` (`bs4`): HTML parse
- `json`: ilerleme kaydı
- `os`, `re`, `time`, `traceback`: dosya işlemleri, regex, bekleme, hata
- `threading`: duraklat/devam/durdur yönetimi
- `deep-translator` (tercih edilen): çeviri motoru
- `googletrans` (yedek): `deep-translator` yoksa kullanılır

Kurulum (Windows/PowerShell):
```
 pip install requests beautifulsoup4 deep-translator
# İsteğe bağlı yedek
pip install googletrans==4.0.0-rc1
```

## Klasör/Dosya Yapısı
```
novels/
	<Roman_Adi>/
		en/
			00001.txt
			00002.txt
			...
		tr/
			00001.txt
			00002.txt
			...
		download_progress.json
		translation_progress.json
DownloaderStart.bat		
novel_downloader.py
README.md
```

## Çalıştırma
```
py novel_downloader.py
```
- Ana menü üzerinden roman URL’sini girerek indirme başlatılır.
- Çeviri menülerinden tek bölüm/dizi çeviri başlatılabilir.

## Klavye Kısayolları (Çeviri/İndirme sırasında)
- `P`: Duraklat
- `R`: Devam et
- `S`: Durdur
- `T`: Çeviri menüsüne hızlı geçiş (akışa bağlı)

## Ana Akış
- `main()` uygulamayı başlatır.
- İndirme: URL → sayfa al → içerik çıkar → kaydet → sonraki sayfayı bul.
- Çeviri: Roman seç → çevrilmemiş dosyaları listele → parçala → çevir → kaydet.

## Fonksiyonlar ve Sınıflar
İndirme/Parse:
- `fetch_page(url)`: URL’den HTML alır ve `BeautifulSoup` döndürür.
- `extract_novel_content(soup)`: Bölüm metnini paragrafları filtreleyerek çıkarır.
- `find_next_page_url(soup)`: Sonraki bölüm linkini bulur (örn. `id='btn-next'`).
- `extract_novel_name(soup)`: Roman adını sayfa başlığından çıkarır.
- `create_novel_directory(novel_name)`: Roman klasör yapısını oluşturur.
- `save_chapter(novel_dir, chapter_index, text)`: Bölüm dosyasını yazar.
- `save_progress(novel_dir, progress)`: İndirme ilerlemesini JSON’a kaydeder.
- `load_progress(novel_dir)`: İndirme ilerlemesini yükler.
- `list_downloaded_novels()`: İndirilmiş roman klasörlerini listeler.

Çeviri:
- `list_untranslated_chapters(novel_dir)`: Çevrilmemiş bölüm dosyalarını listeler.
- `load_translation_progress(novel_dir)`: Çeviri ilerlemesini yükler.
- `save_translation_progress(novel_dir, progress)`: Çeviri ilerlemesini kaydeder.
- `_split_chunks(text, max_length=4500)`: Metni çeviri limiti için paragraf bazlı parçalara böler.
- `translate_text_en_to_tr(text, control)`: Seçilen backend ile EN→TR çeviri yapar, `pause/stop` destekler.
- `translate_chapters(novel_dir, items, control, start_idx=0, limit=None)`: Bölümleri topluca çevirir ve sonuçları kaydeder.

Menüler ve Kontrol:
- `show_translation_menu(novel_dir, control)`: Çeviri seçeneklerini sunar.
- `choose_novel_menu()`: İndirilmiş romanlar arasından seçim yapar.
- `show_global_translation_menu()`: Roman seçimi sonrası çeviri menüsü.
- `show_main_menu()`: Ana menü (indirme/çeviri/çıkış).
- `Control`: `pause_event` ve `stop_event` ile durum yönetimi.
- `start_keyboard_listener(control)`: P/R/S/T tuşları için klavye dinleyicisi başlatır.

## Kullanım Adımları
1. Gerekli kütüphaneleri kurun.
2. Programı çalıştırın: `py novel_downloader.py`.
3. Ana menüden roman URL’sini girin ve indirmenin tamamlanmasını bekleyin.
4. `choose_novel_menu()` ile romanı seçin.
5. `show_global_translation_menu()` üzerinden çeviri menüsüne girin.
6. Tek bölüm veya bir aralıktaki bölümlerin çevirisini başlatın.
7. İster duraklatın (`P`), ister devam edin (`R`), isterseniz durdurun (`S`).

## Notlar ve Sınırlamalar
- Site yapısı değişirse (`find_next_page_url` vb.) kuralları güncellemek gerekebilir.
- `googletrans` bazı Python sürümlerinde uyumsuzluk yaşayabilir; `deep-translator` önerilir.
- Çok hızlı isteklerde rate-limit oluşabilir; gerekirse bekleme ekleyin (`time.sleep`).

## Sorun Giderme
- Çeviri çalışmıyorsa: `deep-translator` veya `googletrans` kurulu mu? `pip show deep-translator` veya `pip show oogletrans` ile kontrol edin.
- Hata mesajlarında `traceback` çıktısını kontrol edin ve gerekirse URL/HTML yapısını doğrulayın.
- PATH sorunu: Scripts klasörünün PATH’e eklendiğinden emin olun.

Windows'ta PATH değişkenini şu şekilde ekleyebilirsiniz:

1.
   Windows tuşu + R tuşlarına basın ve "sysdm.cpl" yazıp Enter tuşuna basın
2.
   "Gelişmiş" sekmesine tıklayın
3.
   "Ortam Değişkenleri" düğmesine tıklayın
4.
   "Kullanıcı değişkenleri" bölümünde "Path" değişkenini seçin ve "Düzenle" düğmesine tıklayın
5.  ( Python un kurulu olduğu dizin,  Kendi sisteminize göre ayarlayın. Aşağıdaki örnekde: Asus sizinkinde farklı olacaktır. )
   "Yeni" düğmesine tıklayın ve " C:\Users\Asus\AppData\Local\Python\pythoncore-3.14-64\Scripts " yolunu ekleyin
   "Yeni" düğmesine tıklayın ve " C:\Users\Asus\AppData\Local\Python\pythoncore-3.14-64 " yolunu ekleyin
   "Yeni" düğmesine tıklayın ve " C:\Users\Asus\AppData\Local\Python " yolunu ekleyin
6.
   "Tamam" düğmesine tıklayarak tüm pencereleri kapatın
Bu değişiklikten sonra, açık olan tüm komut istemcilerini kapatıp yeniden açmanız gerekecektir. Daha sonra deep-translator komutunu doğrudan çalıştırabilirsiniz.
