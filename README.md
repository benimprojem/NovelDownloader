# Roman İndirici ve Çevirici

Bu uygulama, web sitelerinden roman bölümlerini indirmenize, indirilen bu bölümleri farklı dillere çevirmenize ve tüm bu süreçleri kolayca yönetmenize olanak tanıyan kapsamlı bir araçtır. Kullanıcı dostu menü tabanlı arayüzü sayesinde, roman indirme ve çeviri işlemlerini adım adım gerçekleştirebilirsiniz.

## Özellikler

-   **Roman İndirme**: Belirtilen bir web adresinden (URL) roman bölümlerini otomatik olarak indirir. İndirme işlemi sırasında sayfa limiti belirleyerek kontrol sağlayabilirsiniz.
-   **Bölüm Çevirisi**: İndirilen roman bölümlerini istediğiniz hedef dile çevirir. Çeviri işlemi, her bölüm için ayrı ayrı yapılır ve çevrilen metinler düzenli bir şekilde kaydedilir.
-   **İndirmeye Devam Etme**: Yarım kalan veya kesintiye uğrayan roman indirme işlemlerine kaldığınız yerden sorunsuz bir şekilde devam etmenizi sağlar. Uygulama, her romanın ilerlemesini otomatik olarak kaydeder.
-   **Çeviriye Devam Etme**: Benzer şekilde, yarım kalan çeviri işlemlerine de kaldığınız yerden devam edebilirsiniz. Uygulama, hangi bölümlerin çevrildiğini takip eder.
-   **İlerleme Takibi**: İndirilen ve çevrilen bölümlerin sayısını anlık olarak takip edebilir, böylece projenizin genel durumunu görebilirsiniz.
-   **Durdurma Fonksiyonu**: Hem indirme hem de çeviri işlemleri sırasında, klavyeden 'S' tuşuna basarak işlemi güvenli bir şekilde durdurabilir ve ana menüye geri dönebilirsiniz. Bu, beklenmedik durumlar veya yanlış seçimler için esneklik sağlar.

## Nasıl Kullanılır?

Uygulamayı kullanmaya başlamak için aşağıdaki adımları izleyin:

### Kurulum

1.  **Python Kurulumu**: Bilgisayarınızda Python 3.x kurulu olduğundan emin olun. Python'ı [resmi web sitesinden](https://www.python.org/downloads/) indirebilirsiniz.
2.  **Bağımlılıkların Kurulumu**: Uygulamanın çalışması için gerekli olan Python kütüphanelerini kurmanız gerekmektedir. Terminal veya komut istemcisini açın ve aşağıdaki komutu çalıştırın:

    ```bash
    pip install requests beautifulsoup4 googletrans-py
    ```
    *   `requests`: Web sayfalarını indirmek için kullanılır.
    *   `beautifulsoup4`: İndirilen HTML içeriğini ayrıştırmak ve roman bölümlerini çıkarmak için kullanılır.
    *   `googletrans-py`: Roman bölümlerini farklı dillere çevirmek için Google Translate API'sini kullanır.

### Uygulamayı Çalıştırma

`noveldownload.py` dosyasının bulunduğu dizine gidin ve aşağıdaki komutu çalıştırın:

```bash
python noveldownload.py
```

Uygulama başladığında, size aşağıdaki ana menü seçeneklerini sunacaktır:

1.  **Yeni Roman İndir**:
    *   Bu seçeneği seçtiğinizde, indirmek istediğiniz romanın URL'sini girmeniz istenecektir.
    *   İsteğe bağlı olarak, kaç bölüm indirmek istediğinizi belirten bir sayfa limiti de girebilirsiniz.
    *   Uygulama, belirtilen URL'den başlayarak roman bölümlerini sırayla indirecek ve her bölümü ayrı bir metin dosyası olarak kaydedecektir.
2.  **Mevcut İndirmeye Devam Et**:
    *   Daha önce indirmeye başladığınız ancak tamamlamadığınız romanları listeler.
    *   Devam etmek istediğiniz romanı listeden seçerek, indirme işlemine kaldığınız en son bölümden devam edebilirsiniz. Her romanın yanında "Son Bölüm" bilgisi gösterilir.
3.  **Kayıtlı Romanları Çevir**:
    *   İndirilmiş romanlarınızı listeler. Her romanın yanında çevrilmemiş bölüm sayısı gösterilir.
    *   Çevirmek istediğiniz romanı seçtikten sonra, hedef çeviri dilini (örn. "en" for English, "tr" for Turkish) girmeniz istenecektir.
    *   Uygulama, seçilen romanın çevrilmemiş bölümlerini hedef dile çevirecek ve çevrilen metinleri romanın kendi dizini içinde ilgili dil klasörüne kaydedecektir.

## Ana Fonksiyonlar

Uygulamanın temel işlevlerini yerine getiren ana fonksiyonlar aşağıda açıklanmıştır:

-   `main()`: Uygulamanın ana yürütme noktasıdır. Ana menüyü görüntüler, kullanıcıdan seçim alır ve seçime göre ilgili fonksiyonları çağırır. Uygulamanın genel akışını yönetir.
-   `show_main_menu()`: Ana menü seçeneklerini (Yeni Roman İndir, Mevcut İndirmeye Devam Et, Kayıtlı Romanları Çevir, Çıkış) kullanıcıya sunar ve kullanıcının seçimini döndürür.
-   `download_novel(novel_url, page_limit=None)`: Verilen `novel_url` adresinden roman bölümlerini indirir. `page_limit` parametresi ile indirilecek maksimum bölüm sayısı belirlenebilir. İndirilen her bölüm, romanın kendi dizininde bir metin dosyası olarak saklanır.
-   `show_translation_menu()`: Çeviri menüsünü görüntüler. Kullanıcının çevirmek istediği romanı ve hedef dili seçmesini sağlar. `translate_chapters` fonksiyonunu çağırarak çeviri işlemini başlatır.
-   `translate_chapters(novel_dir, target_language, start_chapter=1)`: Belirtilen `novel_dir` dizinindeki roman bölümlerini `target_language` diline çevirir. `start_chapter` parametresi ile çeviriye hangi bölümden başlanacağı belirlenebilir. Çeviri sırasında 'S' tuşuna basılarak durdurulabilir.
-   `list_saved_novels()`: Uygulama tarafından kaydedilmiş tüm romanların bir listesini döndürür. Her roman için adı, dizin yolu ve en son kaydedilen bölüm numarası (`current_chapter`) bilgilerini içerir. Bu bilgi, `progress.json` dosyasından alınır.
-   `list_downloaded_novels()`: Yerel olarak indirilmiş tüm romanların bir listesini döndürür. Her roman için adı, dizin yolu ve çevrilmemiş bölüm sayısı (`untranslated_count`) bilgilerini içerir. Bu bilgi, `list_untranslated_chapters` fonksiyonu kullanılarak hesaplanır.
-   `save_progress(novel_dir, chapter_number, current_url)`: Belirli bir romanın (`novel_dir`) indirme ilerlemesini (`chapter_number` ve `current_url`) `progress.json` dosyasına kaydeder. Bu, uygulamanın kaldığı yerden devam etmesini sağlar.
-   `list_untranslated_chapters(novel_dir)`: Belirtilen `novel_dir` dizinindeki roman için henüz çevrilmemiş olan bölümlerin bir listesini döndürür. Bu liste, çeviri menüsünde romanların yanında gösterilen "Çevrilmemiş Bölüm" sayısını hesaplamak için kullanılır.
-   `fetch_page(url)`: Verilen URL'den web sayfasının içeriğini (HTML) çeker. Web kazıma işleminin temelini oluşturur.
-   `find_next_page_url(soup)`: BeautifulSoup nesnesi (`soup`) kullanarak bir web sayfasındaki "sonraki sayfa" bağlantısının URL'sini bulmaya çalışır. Roman bölümleri arasında gezinmek için kullanılır.

## Dosya Yapısı

Uygulama, indirilen romanları ve ilerleme bilgilerini aşağıdaki gibi bir dizin yapısında saklar:

```
.
├── noveldownload.py          # Ana uygulama dosyası
├── README.md                 # Bu README dosyası
└── novels_data/              # İndirilen tüm romanların saklandığı ana dizin
    ├── Roman_Adi_1/          # İlk romanın dizini
    │   ├── chapter_001.txt   # İlk bölümün orijinal metni
    │   ├── chapter_002.txt
    │   ├── progress.json     # Romanın indirme ilerlemesi (son bölüm, URL)
    │   ├── en/               # İngilizce çevirilerin saklandığı dizin
    │   │   ├── chapter_001.txt
    │   │   └── chapter_002.txt
    │   └── tr/               # Türkçe çevirilerin saklandığı dizin (örnek)
    │       ├── chapter_001.txt
    │       └── chapter_002.txt
    └── Roman_Adi_2/          # İkinci romanın dizini
        ├── chapter_001.txt
        ├── progress.json
        └── ...
```

## Notlar

-   Çeviri işlemi sırasında 'S' tuşuna basarak işlemi durdurabilir ve ana menüye dönebilirsiniz.
-   Uygulama, roman ilerlemesini her romanın kendi dizinindeki `progress.json` dosyasında saklar.
-   Çevrilen bölümler, roman dizini içinde `[dil_kodu]` (örn. `en`, `tr`) adında bir klasörde saklanır.
-   Web sitelerinin yapısı değiştiğinde `fetch_page` ve `find_next_page_url` fonksiyonlarının güncellenmesi gerekebilir.




# 📖 NovelReader - Yerel Roman Okuyucu ve Yönetim Uygulaması

**NovelReader**, yerel diskinizde depolanan romanları (novel) düzenli bir şekilde listelemek ve okumak için tasarlanmış basit ve kullanıcı dostu bir masaüstü uygulamasıdır. `tkinter` kullanılarak Python ile geliştirilmiştir ve düşük kaynak tüketimiyle hızlı bir okuma deneyimi sunar.

## ✨ Temel Özellikler

* **Düzenli Klasör Yapısı:** Romanları `novels/[Roman Adı]/[en/tr]/` yapısında yöneterek çok dilli içeriği destekler.
* **Bölüm Bazlı Okuma Akışı:** Sol alttaki butonlar ile sayfalar arasında değil, bir sonraki/önceki bölüme kolayca geçiş yapabilirsiniz.
* **Tam Bölüm Gösterimi:** Okuyucu sekmesi, bölüm içeriğinin tamamını kaydırılabilir tek bir metin kutusunda gösterir.
* **Sekmeli Dil Yönetimi:** Sağdaki bölüm listesi, **Orijinal (en)**, **Çeviri (tr)** ve ileride eklenecek **PDF** sekmeleri ile dil seçimini ve bölüm listesini netleştirir.
* **Koyu/Açık Tema Desteği:** Tek tıkla tema değişimi ile göz yorgunluğunu azaltabilirsiniz.
* **Otomatik Kayıt:** Okuma durumu (hangi romanda hangi bölümü okuduğunuz) otomatik olarak kaydedilir ve bir sonraki açılışta kalınan yerden devam edilir.
* **Bağımsız Kontrol Çubuğu:** Ana butonlar, uygulamanın üst kısmında bağımsız bir kontrol çubuğunda yer alır.

## 📁 Klasör Yapısı (Kurulum)

Uygulamanın düzgün çalışması için, tüm roman dosyalarınızın aşağıdaki hiyerarşiye uygun bir klasör içinde bulunması gerekmektedir. Varsayılan olarak, uygulamanın çalıştığı dizinde `novels` adında bir ana klasör arar.

/ ├── readnovel.py # Ana uygulama dosyası ├── readnovel_state.json # Okuma durumunun kaydedildiği dosya ├── novels/ # Romanların ana klasörü │ ├── RomanAdı_1/ # Her roman için bir klasör │ │ ├── en/ # İngilizce/Orijinal bölümler │ │ │ └── chapter_0001.txt │ │ │ └── chapter_0002.txt │ │ └── tr/ # Türkçe/Çeviri bölümler (isteğe bağlı) │ │ └── chapter_0001.txt │ └── RomanAdı_2/ │ └── en/ │ └── chapter_0001.txt


## 🛠️ Kurulum ve Çalıştırma

Bu uygulama saf Python ve standart `tkinter` kütüphanesi ile geliştirilmiştir. Harici bir paket (library) yüklemeniz gerekmez.

1.  **Python Kurulumu:** Bilgisayarınızda Python 3'ün kurulu olduğundan emin olun.
2.  **Dosyaları İndirme:** `readnovel.py` dosyasını indirin.
3.  **Roman Klasörünü Oluşturma:** Uygulama dosyasının bulunduğu dizinde `novels` adında bir klasör oluşturun ve romanlarınızı yukarıdaki yapıya göre yerleştirin.
4.  **Uygulamayı Başlatma:** Terminal/Komut İstemi üzerinden uygulamayı çalıştırın:

    ```bash
    python readnovel.py
    ```

## 🖥️ Kullanım Kılavuzu

### 1. Ana Ekran

Uygulama açıldığında, ekran üç ana bölüme ayrılır:

| Bölüm | Konum | İçerik |
| :--- | :--- | :--- |
| **Üst Kontrol Çubuğu** | Üstte, sağa hizalı | `Novel (Klasör Seçimi)`, `Kaydet`, `⭐ (Tema)`, `PDF` butonları. |
| **Sol İçerik Alanı** | Sol, Geniş | **Novel Listesi** ve **Okuyucu** sekmeleri. |
| **Sağ Bölüm Listesi** | Sağ, Dar | Bölüm dosyalarının listelendiği **Orijinal**, **Çeviri** ve **PDF** sekmeleri. |

### 2. Roman Yükleme ve Seçimi

* **Novel Listesi Sekmesi:** Uygulama açılışta `novels` klasöründeki romanları listeler.
* **Roman Seçimi:** Soldaki listeden bir romana tıklayarak sağdaki Bölüm Listesi'ni o romana ait bölümlerle doldurursunuz.
* **Klasör Değiştirme:** Eğer romanlarınız başka bir yerdeyse, üstteki **Novel** butonuna tıklayarak yeni ana `novels` klasörünü seçebilirsiniz.

### 3. Bölüm Okuma

1.  **Dil Seçimi:** Sağdaki Bölüm Listesi alanından **Orijinal (en)** veya **Çeviri (tr)** sekmesini seçin.
2.  **Bölüm Açma:** İstenen bölüm dosyasına (örneğin `chapter_0001.txt`) **çift tıklayın**.
3.  **Okuyucu Sekmesi:** Uygulama otomatik olarak **Okuyucu** sekmesine geçer ve bölümün **tamamını** yükler. Metin kutusunun kaydırma çubuğunu kullanarak bölümü okuyabilirsiniz.

### 4. İlerleme ve Navigasyon

* **İleri/Geri Butonları:** Okuyucu sekmesinin altında bulunan **`<< Geri`** ve **`İleri >>`** butonları, okuduğunuz dildeki **bir önceki veya bir sonraki bölüme** geçiş yapar.
* **Otomatik Kayıt:** Bölüm değiştirdiğinizde veya uygulamayı kapattığınızda, okuma durumunuz (`readnovel_state.json` dosyasına) sessizce kaydedilir.
* **Manuel Kayıt:** Üst çubuktaki **Kaydet** butonu ile istediğiniz zaman manuel kayıt yapabilirsiniz. (Bu işlemde bilgilendirme mesajı görünür).

## 💡 İpuçları

* **Tema Değişimi:** Üst çubukta bulunan **⭐** butonuna tıklayarak Açık ve Koyu tema arasında geçiş yapabilirsiniz.
* **Dosya Formatı:** Bölüm dosyaları düz metin (`.txt`) formatında ve `utf-8` kodlamasında olmalıdır.
* **Çeviri Sekmesi:** `Çeviri (tr)` sekmesi, ilgili roman klasörünün içindeki `tr` alt klasöründeki dosyaları listeler.

## 🛑 Bilinen Kısıtlamalar

* **PDF Desteği:** Sağdaki `PDF` sekmesi henüz işlevsel değildir ve ileride geliştirilecektir.
* **Arama/Filtreleme:** Novel listesi veya Bölüm listesi için henüz arama (filtreleme) özelliği mevcut değildir.

---

**© [2025] [cem/DissConnected]**
