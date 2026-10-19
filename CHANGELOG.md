# Değişiklik Günlüğü (Changelog)

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Format [Keep a Changelog](https://keepachangelog.com/tr/1.1.0/) standardını temel alır ve bu proje [Semantic Versioning](https://semver.org/lang/tr/) kurallarına uyar.

## [Unreleased]
### Planned
- Yeni "Aether Katana" silahı ve Siber Dünya temalı yeni harita için altyapı çalışmaları.
- Farklı dünyalar eklemek için altyapı ve OOP çalışmaları.

## [0.4.1] - 2026-10-19
### Added
- Gerçekçi oyun mekanikleri.
- Ayarlar ekranının yatay kaydırma sistemi eklendi.

### Removed
- `settings_manager.py` ve `pass_manager.py` modülleri kullanımdan kaldırıldı.

### Changed
- lose_music.ogg yerini cant_give_up.wav aldı.

### Fixed
- Ayarlar ekranının kaydırma sistemi düzeltildi.
- Başarıların ekrandan taşması düzeltildi.

## [0.4.0] - 2026-10-17
### Added
- Yeni silah: **Altın Kılıç** eklendi.
- Kılıç hareketlerine görsel iz (*trail*) efekti eklendi.
- Ayarlar menüsüne jenerik (*credits*) bölümü ve özel jenerik müziği eklendi.
- Bölüm tamamlama / kazanma anı için özel kutlama müziği eklendi.
- Müzik kütüphanesine yeni hazır müzik parçaları eklendi.
- Başarılar ekranında henüz kilitli / açılmamış kartların da listelenmesi sağlandı.

### Changed
- Ayarlar ekranının görsel arayüzü yenilendi ve uzun listeler için kaydırma (*scroll*) sistemi eklendi.
- Silah seçme menüsünün görsel tasarımı ve düzeni iyileştirildi.
- Ana menü, ayarlar ve dünya seçme ekranlarının müzikleri yenileriyle değiştirildi.
- Başarılar ekranındaki kartların kenarlık rengi mavi olarak güncellendi.
- Oyun içi ESC duraklatma menüsündeki "Çıkış" butonu, doğrudan "Ana Menüye Dön" seçeneğiyle değiştirildi.
- Düşman boyutları farklı ekran çözünürlüklerine göre otomatik ölçeklenecek şekilde uyarlandı.

### Fixed
- Düşmanların bazı ekranlarda gereğinden çok küçük görünmesine yol açan hata giderildi.
- Çarpışma ve temas alanlarındaki (*hitbox*) hatalı sınır hesaplamaları düzeltildi.

[Unreleased]: https://github.com/LastHope48/savas-oyunu-1/compare/v0.4.0...HEAD
[0.4.1]: https://github.com/LastHope48/savas-oyunu-1/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/LastHope48/savas-oyunu-1/compare/v0.3.1...v0.4.0
