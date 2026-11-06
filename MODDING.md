# Savaş Oyunu 1 - Mod Geliştirme Kılavuzu (API v1.0)

Savaş Oyunu 1'e hoş geldiniz! Bu kılavuz, oyun için nasıl özel silahlar, eşyalar, bölümler ve yeni dünyalar (kasetler) geliştirebileceğinizi açıklar.

---

## 1. Hızlı Başlangıç

Tüm modlar oyunun ana klasöründeki `mods/` dizini altında yer alır.

1. `mods/` klasörü içinde modunuz için bir klasör açın: `mods/benim_modum/`
2. Mod klasörünün içine iki temel dosya koyun:
   * `mod.json` (Mod bilgileri)
   * `main.py` (Mod kodları)
   * `icon.png` (İsteğe bağlı, 64x64 veya 128x128 mod menüsü simgesi)

---

## 2. `mod.json` Manifest Dosyası

Oyunun modunuzu tanıması ve ayarlar menüsünde gösterebilmesi için gereklidir:

```json
{
  "id": "benim_modum",
  "name": "Plazma Katanası ve Neon Şehir",
  "version": "1.0.0",
  "author": "Geliştirici Adı",
  "description": "Oyuna yeni bir kaset dünyası ve 5. seviyeye özel Işın Kılıcı ekler.",
  "enabled": true
}