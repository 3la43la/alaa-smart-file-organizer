import os
import shutil

# حدد المجلد الذي تريد تنظيمه (هنا مجلد Downloads كمثال)
# تذكر تغيير 'alaa' لاسم المستخدم الخاص بك إذا لزم الأمر
target_dir = os.path.expanduser("~/Downloads")

# خريطة الامتدادات والمجلدات المقابلة لها
extensions = {
    ".pdf": "Documents",
    ".docx": "Documents",
    ".jpg": "Images",
    ".png": "Images",
    ".mp4": "Videos",
    ".zip": "Archives",
    ".tar": "Archives",
    ".gs": "Archives",
    ".gz": "Archives",
    ".tgz": "Archives",
    ".xz": "Archives",
    ".torrent": "Torrent",
    ".deb": "App",
    ".AppImage": "App",
    ".nzb": "NZB"
}

def organize_files():
    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)
        
        # التأكد أنه ملف وليس مجلد
        if os.path.isfile(filepath):
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in extensions:
                dest_dir = os.path.join(target_dir, extensions[ext])
                
                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs(dest_dir, exist_ok=True)
                
                # نقل الملف
                shutil.move(filepath, os.path.join(dest_dir, filename))
                print(f"تم نقل: {filename} إلى {extensions[ext]}")

if __name__ == "__main__":
    organize_files()
    print("✅ تم الانتهاء من تنظيم المجلد!")
