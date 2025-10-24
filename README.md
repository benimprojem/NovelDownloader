# Roman İndirici ve Çevirici

Bu uygulama, belirtilen URL'lerden romanları indirmenize, indirilen bölümleri çevirmenize ve indirme/çeviri ilerlemenizi yönetmenize olanak tanır.

## Özellikler

-   **Roman İndirme**: Belirtilen bir URL'den roman bölümlerini indirir.
-   **Bölüm Çevirisi**: İndirilen roman bölümlerini seçilen bir dile çevirir.
-   **İndirmeye Devam Etme**: Yarım kalan indirmelere kaldığı yerden devam etme imkanı sunar.
-   **Çeviriye Devam Etme**: Yarım kalan çevirilere kaldığı yerden devam etme imkanı sunar.
-   **İlerleme Takibi**: İndirilen ve çevrilen bölümlerin sayısını gösterir.
-   **Durdurma Fonksiyonu**: İndirme veya çeviri sırasında 'S' tuşuna basarak işlemi durdurma ve ana menüye dönme.

## Nasıl Kullanılır?

Uygulamayı çalıştırmak için `noveldownload.py` dosyasını Python ile çalıştırın:

```bash
python noveldownload.py
```

Uygulama başladığında size ana menüyü sunacaktır:

1.  **Yeni Roman İndir**: Yeni bir roman indirmeye başlamak için bu seçeneği kullanın. Romanın URL'sini ve indirme limitini (isteğe bağlı) girmeniz istenecektir.
2.  **Mevcut İndirmeye Devam Et**: Daha önce indirmeye başladığınız bir romana devam etmek için bu seçeneği kullanın. Kayıtlı romanlar listelenecek ve devam etmek istediğiniz romanı seçebileceksiniz.
3.  **Kayıtlı Romanları Çevir**: İndirilmiş romanlarınızı çevirmek için bu seçeneği kullanın. Çevrilmemiş bölümleri olan romanlar listelenecek ve çevirmek istediğiniz romanı seçebileceksiniz. Ayrıca çeviri dilini de seçmeniz istenecektir.

## Ana Fonksiyonlar

-   `main()`: Uygulamanın ana giriş noktasıdır ve ana menüyü yönetir.
-   `show_main_menu()`: Kullanıcıya ana menü seçeneklerini gösterir ve seçimini alır.
-   `download_novel(novel_url, page_limit=None)`: Belirtilen URL'den romanı indirir. İsteğe bağlı olarak bir sayfa limiti belirlenebilir.
-   `show_translation_menu()`: Çeviri menüsünü gösterir, indirilen romanları listeler ve çeviri seçeneklerini sunar.
-   `translate_chapters(novel_dir, target_language, start_chapter=1)`: Belirtilen roman dizinindeki bölümleri hedef dile çevirir. Çeviri sırasında durdurma imkanı sunar.
-   `list_saved_novels()`: Kaydedilmiş romanların listesini ve her roman için son kaydedilen bölüm numarasını döndürür.
-   `list_downloaded_novels()`: İndirilmiş romanların listesini ve her roman için çevrilmemiş bölüm sayısını döndürür.
-   `save_progress(novel_dir, chapter_number, current_url)`: Bir romanın indirme ilerlemesini (bölüm numarası ve URL) kaydeder.
-   `list_untranslated_chapters(novel_dir)`: Belirtilen roman dizinindeki çevrilmemiş bölümlerin listesini döndürür.

## Bağımlılıklar

Bu uygulama standart Python kütüphaneleri ve muhtemelen `requests`, `BeautifulSoup` gibi web kazıma ve `googletrans` gibi çeviri kütüphaneleri kullanmaktadır. Gerekli kütüphaneleri `pip` ile kurmanız gerekebilir:

```bash
pip install requests beautifulsoup4 googletrans-py
```

## Notlar

-   Çeviri işlemi sırasında 'S' tuşuna basarak işlemi durdurabilir ve ana menüye dönebilirsiniz.
-   Uygulama, roman ilerlemesini her romanın kendi dizinindeki `progress.json` dosyasında saklar.
-   Çevrilen bölümler, roman dizini içinde `[dil_kodu]` (örn. `tr`) adında bir klasörde saklanır.
