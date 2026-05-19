"""
Barcha media fayllarni (rasmlar va videolar) Cloudinary'ga yuklash skripti.
Natijalar media_urls.json fayliga saqlanadi.
"""

import cloudinary
import cloudinary.uploader
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Cloudinary konfiguratsiya
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Yuklash kerak bo'lgan fayllar
IMAGES = [
    "1.jpg", "2.jpg", "3.jpg", "4.jpg",
    "earth.jpg", "harakat.jpg", "havo.jpg", "kashfiyot.jpg",
    "kosmos.jpg", "litosfera.jpg", "metallar.jpg", "modda.jpg",
    "sun.jpg", "suv.jpg", "tabiat.jpg", "tuproq.jpg",
    "yer.jpg", "yonuvchi.jpg"
]

VIDEOS = [
    "earth.mp4", "harakat.mp4", "havo.mp4", "kashfiyot.mp4",
    "kosmos.mp4", "litosfera.mp4", "metallar.mp4", "modda.mp4",
    "sun.mp4", "suv.mp4", "tabiat.mp4", "tuproq.mp4",
    "tuproqdarslik.mp4", "yer.mp4", "yonuvchi.mp4"
]

def upload_file(file_path, public_id, resource_type="image"):
    """Faylni Cloudinary'ga yuklash"""
    try:
        print(f"  Yuklanmoqda: {file_path} -> {public_id} ({resource_type})")
        result = cloudinary.uploader.upload(
            file_path,
            public_id=f"kichikOlimUZ/{public_id}",
            resource_type=resource_type,
            overwrite=True
        )
        url = result["secure_url"]
        print(f"  ✅ Muvaffaqiyatli: {url}")
        return url
    except Exception as e:
        print(f"  ❌ Xatolik: {e}")
        return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "static", "images")
    videos_dir = os.path.join(base_dir, "static", "videos")
    
    media_urls = {
        "images": {},
        "videos": {}
    }
    
    # Rasmlarni yuklash
    print("\n📷 RASMLAR YUKLANMOQDA...")
    print("=" * 60)
    for img in IMAGES:
        img_path = os.path.join(images_dir, img)
        if os.path.exists(img_path):
            name = os.path.splitext(img)[0]
            url = upload_file(img_path, f"images/{name}", "image")
            if url:
                media_urls["images"][name] = url
        else:
            print(f"  ⚠️ Fayl topilmadi: {img_path}")
    
    # Videolarni yuklash
    print("\n🎬 VIDEOLAR YUKLANMOQDA...")
    print("=" * 60)
    for vid in VIDEOS:
        vid_path = os.path.join(videos_dir, vid)
        if os.path.exists(vid_path):
            name = os.path.splitext(vid)[0]
            url = upload_file(vid_path, f"videos/{name}", "video")
            if url:
                media_urls["videos"][name] = url
        else:
            print(f"  ⚠️ Fayl topilmadi: {vid_path}")
    
    # Natijalarni saqlash
    output_path = os.path.join(base_dir, "media_urls.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(media_urls, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Barcha URL'lar saqlandi: {output_path}")
    print(f"📷 Rasmlar: {len(media_urls['images'])} ta")
    print(f"🎬 Videolar: {len(media_urls['videos'])} ta")
    print("=" * 60)

if __name__ == "__main__":
    main()
