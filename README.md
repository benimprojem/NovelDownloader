# Read Novel

Python ve Tkinter ile geliştirilmiş masaüstü **novel indirme, çeviri ve
okuma uygulaması**.

Uygulama, daha önce ayrı çalışan `NovelDovnload_3.py` indirme/çeviri
kodunu grafik arayüzlü `readnovel-v1.4.pyw` uygulamasına entegre eder.
Böylece novel indirme ve çeviri işlemleri arka planda devam ederken
kayıtlı noveller ve bölümler uygulama içerisinden okunabilir.

> **Durum:** Geliştirme aşamasında. Uygulama kullanılabilir durumdadır
> ancak bazı sitelerin HTML yapısına ve çeviri servislerinin çalışma
> biçimine bağlı sınırlamalar bulunabilir.

------------------------------------------------------------------------

## Özellikler

### 📥 Novel indirme

-   İlk bölüm URL'sinden indirme başlatma.
-   İndirilecek bölüm sayısını belirleme.
-   `0` girildiğinde mevcut downloader mantığına göre tüm bölümleri
    indirme.
-   Daha önce yarım kalmış indirmeye devam etme.
-   İndirme işlemini duraklatma/devam ettirme.
-   İndirmeyi durdurma.
-   İndirme işleminin arka planda ayrı thread üzerinde çalışması.
-   İndirme sırasında:
    -   mevcut bölüm,
    -   toplam ilerleme,
    -   ilerleme çubuğu,
    -   işlem durumu,
    -   son işlemler arayüzde gösterilir.

### 🌐 Otomatik çeviri

-   İngilizce (`en`) bölümleri Türkçeye (`tr`) çevirme.
-   Daha önce çevrilmiş bölümleri tekrar çevirmeme.
-   Çevrilmemiş bölüm sayısını gösterme.
-   Çeviri işlemini arka planda yürütme.
-   Çeviri ilerlemesini arayüzde gösterme.
-   `translate_progress.json` üzerinden çeviri ilerlemesini koruma.

Çeviri altyapısı mevcut downloader içerisindeki Google Translate
desteğini kullanır.

### 📚 Novel listesi

-   `novels` klasöründeki noveller otomatik olarak algılanır.
-   Novel kartları ızgara şeklinde gösterilir.
-   Liste:
    -   yukarıdan aşağı,
    -   alan genişliği dolduğunda sağa doğru ilerler.
-   Yatay ve dikey kaydırma desteklenir.
-   Novel kartlarının boyutları eşittir.
-   Her novel için indirilen/çevirilen bölüm bilgileri gösterilir.
-   Yeni indirilen noveller yeniden liste tarandığında otomatik olarak
    görünür.

### 📖 Bölüm listesi

Bölümler ayrı bir bölüm ekranında gösterilir.

-   Orijinal (`en`) ve çeviri (`tr`) bölümleri ayrı listelenir.
-   Bölümler ızgara düzeninde gösterilir.
-   Sıralama yukarıdan aşağı, ardından sağa doğru devam eder.
-   Yatay ve dikey kaydırma desteklenir.
-   Çok fazla bölüm olduğunda gereksiz miktarda Tkinter widget'ının aynı
    anda oluşturulmaması için liste görünür alanı esas alacak şekilde
    yönetilir.
-   Aktif/son okunan bölüm açıldığında ilgili bölümün bulunduğu konuma
    gidilir.

### 📖 Okuma ekranı

-   Tam genişlikte okuma alanı.
-   Orijinal ve Türkçe bölümler arasında geçiş.
-   Son okunan novel ve bölümün saklanması.
-   Uygulama yeniden açıldığında kaldığın bölüme dönme.
-   Klavye ile bölüm gezinme desteği.

### 🎨 Tema

Mevcut uygulamada açık ve koyu tema desteği bulunur.

Tema tercihi `readnovel_state.json` içerisinde saklanır.

------------------------------------------------------------------------

## Dosya yapısı

Uygulamanın mevcut klasör yapısı özellikle korunmaktadır:

``` text
reader/
├── readnovel-v1.4.pyw
├── NovelDovnload_3.py
├── readnovel_state.json
└── novels/
    ├── Novel A/
    │   ├── en/
    │   │   ├── chapter_0001.txt
    │   │   ├── chapter_0002.txt
    │   │   └── ...
    │   ├── tr/
    │   │   ├── chapter_0001.txt
    │   │   ├── chapter_0002.txt
    │   │   └── ...
    │   ├── progress.json
    │   └── translate_progress.json
    └── Novel B/
        └── ...
```

### Dosyaların görevleri

  Dosya / klasör              Görevi
  --------------------------- -----------------------------------
  `readnovel-v1.4.pyw`             Ana grafik arayüz ve okuyucu
  `NovelDovnload_3.py`        Novel indirme ve çeviri motoru
  `readnovel_state.json`      Okuma ve uygulama durum bilgileri
  `novels/`                   İndirilen novellerin ana klasörü
  `en/`                       Orijinal bölümler
  `tr/`                       Türkçe çevrilmiş bölümler
  `progress.json`             İndirme ilerlemesi
  `translate_progress.json`   Çeviri ilerlemesi

**Önemli:** `NovelDovnload_3.py`, `readnovel-v1.4.pyw` ile aynı klasörde
bulunmalıdır.

------------------------------------------------------------------------

## Kurulum

### 1. Python

Python 3.x gereklidir.

Windows'ta `.pyw` dosyası Python ile ilişkilendirilmişse:

``` text
readnovel-v1.4.pyw
```

dosyasına çift tıklayarak uygulama başlatılabilir.

İlişkilendirme yoksa:

``` bash
python readnovel-v1.4.pyw
```

ile de çalıştırılabilir.

### 2. Gerekli Python paketleri

Downloader aşağıdaki paketleri kullanır:

``` bash
python -m pip install requests
python -m pip install beautifulsoup4
python -m pip install googletrans
```

Kurulum sırasında kullanılan Google Translate paketi sisteminizde farklı
bir sürüm gerektiriyorsa, downloader dosyasındaki mevcut import/çeviri
altyapısına uygun sürüm kullanılmalıdır.

------------------------------------------------------------------------

## Kullanım

### Yeni novel indirmek

1.  `Downloads` sekmesini açın.
2.  **İlk bölüm URL** alanına novelin ilk bölüm URL'sini girin.
3.  **Bölüm sayısı** alanına indirilecek bölüm sayısını yazın.
    -   `10` → 10 bölüm
    -   `100` → 100 bölüm
    -   `0` → tüm bölümler
4.  **Yeni İndirme** butonuna basın.
5.  İndirme arka planda devam eder.

Uygulamayı kullanmaya, novel listesine geçmeye veya mevcut bölümleri
okumaya devam edebilirsiniz.

### Yarım kalan indirmeye devam etmek

1.  `Downloads` listesinden noveli seçin.
2.  **Seçileni Devam Ettir** butonuna basın.

Downloader'ın mevcut `progress.json` kaydından devam edilir.

### Çeviri yapmak

1.  `Downloads` listesinden çevrilecek noveli seçin.
2.  **Çevir** butonuna basın.
3.  Uygulama çevrilmemiş bölümleri belirler.
4.  Çeviri arka planda devam eder.
5.  İlerleme bilgisi ekranda gösterilir.

Çevrilmiş bölümler tekrar çevrilmez.

### Novel okumak

1.  `Novel Listesi` sekmesine geçin.
2.  Novel kartını açın.
3.  `Bölümler` sekmesinden bölüm seçin.
4.  `Okuma` sekmesinden okuyun.

Son okuma konumu uygulama tarafından kaydedilir.

------------------------------------------------------------------------

## Arka planda çalışma

İndirme ve çeviri işlemleri ana Tkinter arayüzünü kilitlememek için ayrı
thread'lerde çalıştırılır.

Bu sayede işlem devam ederken:

-   novel listesine geçilebilir,
-   bölüm listesi incelenebilir,
-   mevcut bölümler okunabilir,
-   uygulama durumu takip edilebilir.

İşlem sırasında `Downloads` ekranındaki durum alanı hangi işlemin
yürütüldüğünü gösterir.

------------------------------------------------------------------------

## Veri güvenliği ve mevcut kayıtlar

Uygulama mevcut novel kayıtlarının yapısını değiştirmemek üzere
tasarlanmıştır.

Özellikle:

``` text
novels/
Novel Adı/
en/
tr/
progress.json
translate_progress.json
```

yapısı korunur.

`readnovel-v1.4.pyw` uygulaması klasör yollarını kendi bulunduğu klasöre göre
belirler. Böylece uygulama farklı bir çalışma dizininden başlatılsa bile
`novels` klasörünü yanlış yerde aramaması amaçlanmıştır.

------------------------------------------------------------------------

## İsimlendirme

Novel klasör isimleri downloader içerisindeki mevcut isim temizleme
mekanizması kullanılarak oluşturulur.

Downloader'ın `_clear_name()` fonksiyonu:

-   bazı gereksiz ifadeleri temizler,
-   dosya sistemi açısından sorun oluşturabilecek karakterleri kaldırır,
-   novel adını güvenli klasör adına dönüştürür.

Novel adı üzerine uygulama tarafından ayrıca yapay bir prefix/suffix
eklenmez.

Bölüm dosyaları ise mevcut downloader formatında saklanır:

``` text
chapter_0001.txt
chapter_0002.txt
chapter_0003.txt
...
```

------------------------------------------------------------------------

## Desteklenen kaynak siteler

Downloader belirli bir sitenin HTML yapısına göre içerik seçicileri
kullanmaktadır. Bu nedenle her novel sitesi otomatik olarak
desteklenmeyebilir.

Özellikle:

-   bölüm URL yapısı,
-   toplam bölüm sayısının sayfada bulunma şekli,
-   bölüm metninin HTML içerisindeki konumu,
-   sonraki bölüm bağlantısının yapısı

kaynak siteye göre değişebilir.

Yeni bir site desteği gerektiğinde temel olarak `NovelDovnload_3.py`
içerisindeki:

``` text
find_novel_base_url()
get_total_chapters()
extract_novel_name()
extract_novel_content()
find_next_page_url()
```

fonksiyonlarının ilgili sitenin yapısına göre uyarlanması gerekir.

------------------------------------------------------------------------

## Bilinen sınırlamalar

-   Bazı web siteleri bot/otomatik istekleri engelleyebilir.
-   Site HTML yapısı değişirse bölüm çıkarma veya sonraki bölüm bulma
    işlemi çalışmayabilir.
-   Google Translate tarafında istek sınırı veya geçici erişim problemi
    oluşabilir.
-   Çok büyük novel listelerinde bölüm arayüzü performansını korumak
    için görünür alan odaklı listeleme kullanılır.
-   Çeviri hızı kullanılan çeviri servisinin yanıt süresine bağlıdır.
-   Uygulama şu anda öncelikle Windows masaüstü kullanımı düşünülerek
    geliştirilmiştir.

------------------------------------------------------------------------

## Proje bileşenleri

``` text
readnovel-v1.4.pyw
        │
        ├── Grafik arayüz
        ├── Novel listesi
        ├── Bölüm listesi
        ├── Okuyucu
        └── Arka plan işlemleri
                 │
                 ▼
        NovelDovnload_3.py
                 │
                 ├── Web sayfası indirme
                 ├── Bölüm çıkarma
                 ├── Bölüm kaydetme
                 ├── İndirme ilerlemesi
                 └── Çeviri
```

`readnovel-v1.4.pyw`, downloader kodunu ayrı bir kopyaya dönüştürmek yerine
aynı klasördeki:

``` text
NovelDovnload_3.py
```

dosyasını dinamik olarak yükler.

Bu nedenle iki Python dosyasının aynı klasörde bulunması önemlidir.

------------------------------------------------------------------------

## Geliştirme

Proje halen geliştirme aşamasındadır.

Öncelikli geliştirme alanları:

-   daha fazla kaynak site desteği,
-   çeviri altyapısının geliştirilmesi,
-   bölüm listesi performansının daha da iyileştirilmesi,
-   okuyucu özelliklerinin geliştirilmesi,
-   indirme ve çeviri hata yönetiminin geliştirilmesi,
-   kullanıcı arayüzünün iyileştirilmesi.

------------------------------------------------------------------------

## Katkı

Hata bildirirken mümkünse aşağıdaki bilgileri ekleyin:

-   kullanılan kaynak site,
-   bölüm URL'si,
-   hata mesajı,
-   hangi işlem sırasında hata oluştuğu,
-   mümkünse ilgili ekran görüntüsü.

Kaynak sitenin HTML yapısı değişmişse ilgili bölüm yapısı da
belirtilirse sorunun tespit edilmesi kolaylaşır.

------------------------------------------------------------------------

## Lisans

Bu sürüm için README içerisinde özel bir lisans belirtilmemiştir.
------------------------------------------------------------------------

## Proje adı

**Read Novel**

İndirme motoru:

**NovelDovnload_3.py**

Okuyucu:

**readnovel-v1.4.pyw**
