import os
import json
import shutil
import subprocess
import time
from datetime import datetime
import customtkinter as ctk
import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
import PyPDF2

# --- إعدادات المظهر ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

CONFIG_FILE = "last_folder.txt"
APP_CONFIG_FILE = "config.json"

def ar(text):
    if not text: return ""
    return get_display(arabic_reshaper.reshape(text))

def ar_title(text):
    return arabic_reshaper.reshape(text)

# دالة إصدار صوت تنبيه النظام في لينكس
def play_alert_sound():
    try:
        subprocess.Popen(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])
    except (FileNotFoundError, OSError):
        print("\a")

# الخريطة الشاملة
DEFAULT_MAP = {
    "Videos": ["mp4", "mkv", "mov", "avi", "flv", "webm"],
    "Images": ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp"],
    "Documents": ["pdf", "doc", "docx", "txt", "xlsx", "xls", "ppt", "pptx", "odt", "md"],
    "Archives": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
    "Nzb&Torrent": ["nzb", "torrent"],
    "App": ["deb", "AppImage", "rpm", "sh", "flatpakref"],
    "Audio": ["mp3", "wav", "flac", "ogg", "m4a"],
    "Font":['ttf', "otf"]
}

KEYWORDS_FINANCE = ["فاتورة", "invoice", "عقد", "contract", "payment", "سداد", "bank", "مصرف"]
DEFAULT_APP_CONFIG = {
    "finance_keywords_additions": [],
    "category_extensions_additions": {}
}

class AlaasOrganizerV1_4_0(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.version = "1.4.0"
        self.title(ar_title(f"منظم ملفات علاء الذكي - الإصدار {self.version}"))
        self.geometry("700x620")
        self.center_main_window(700, 620)

        self.raw_src = self.load_last_folder()
        self.user_config = self.load_app_config()
        self.finance_keywords = []
        self.map_by_category = {}
        self.apply_user_config()

        # الواجهة
        self.label = ctk.CTkLabel(self, text=ar("مساعد علاء الذكي (مع تنبيهات صوتية)"), 
                                 font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=20)

        self.path_label = ctk.CTkLabel(self, text=ar(f"المجلد: {self.raw_src}"), wraplength=500)
        self.path_label.pack(pady=5)

        self.btn_select = ctk.CTkButton(self, text=ar("تغيير المجلد"), command=self.select_folder)
        self.btn_select.pack(pady=10)

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20)

        self.btn_start = ctk.CTkButton(self.button_frame, text=ar("تنظيم شامل"), 
                                      command=self.start_smart_analysis,
                                      fg_color="#2980b9", hover_color="#3498db", width=250)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_cleanup = ctk.CTkButton(self.button_frame, text=ar("تنظيف قديم"), 
                                        command=self.run_smart_cleanup,
                                        fg_color="#d35400", width=150)
        self.btn_cleanup.grid(row=0, column=1, padx=10)

        self.btn_settings = ctk.CTkButton(self.button_frame, text=ar("الإعدادات"), 
                                         command=self.open_settings_window,
                                         fg_color="#34495e", hover_color="#46627f", width=120)
        self.btn_settings.grid(row=0, column=2, padx=10)

        self.log_box = ctk.CTkTextbox(self, width=620, height=250)
        self.log_box.pack(pady=10)
        self.log("تم تحميل الإعدادات.")

    def center_main_window(self, width, height):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {ar(message)}\n")
        self.log_box.see("end")

    def load_last_folder(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = f.read().strip()
                if saved:
                    return saved
        return str(Path.home() / "Downloads")

    def save_last_folder(self, path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(path)

    def default_map_copy(self):
        return {
            category: [ext.lower().lstrip(".") for ext in extensions if isinstance(ext, str) and ext.strip()]
            for category, extensions in DEFAULT_MAP.items()
        }

    def load_app_config(self):
        if not os.path.exists(APP_CONFIG_FILE):
            self.save_app_config(DEFAULT_APP_CONFIG)
            return {
                "finance_keywords_additions": [],
                "category_extensions_additions": {}
            }

        try:
            with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.save_app_config(DEFAULT_APP_CONFIG)
            return {
                "finance_keywords_additions": [],
                "category_extensions_additions": {}
            }

        return {
            "finance_keywords_additions": raw.get("finance_keywords_additions", []),
            "category_extensions_additions": raw.get("category_extensions_additions", {})
        }

    def save_app_config(self, config):
        with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def normalize_extensions(self, extensions):
        normalized = []
        for ext in extensions:
            if not isinstance(ext, str):
                continue
            clean_ext = ext.strip().lower().lstrip(".")
            if clean_ext and clean_ext not in normalized:
                normalized.append(clean_ext)
        return normalized

    def apply_user_config(self):
        merged_keywords = []
        for word in KEYWORDS_FINANCE + self.user_config.get("finance_keywords_additions", []):
            if not isinstance(word, str):
                continue
            clean_word = word.strip().lower()
            if clean_word and clean_word not in merged_keywords:
                merged_keywords.append(clean_word)
        self.finance_keywords = merged_keywords

        merged_map = self.default_map_copy()
        additions = self.user_config.get("category_extensions_additions", {})
        if isinstance(additions, dict):
            for category, raw_exts in additions.items():
                if not isinstance(category, str):
                    continue
                clean_category = category.strip()
                if not clean_category:
                    continue
                normalized_exts = self.normalize_extensions(raw_exts if isinstance(raw_exts, list) else [])
                if not normalized_exts:
                    continue
                if clean_category not in merged_map:
                    merged_map[clean_category] = []
                for ext in normalized_exts:
                    if ext not in merged_map[clean_category]:
                        merged_map[clean_category].append(ext)

        self.map_by_category = merged_map

    def select_folder(self):
        try:
            folder = subprocess.check_output(['zenity', '--file-selection', '--directory']).decode('utf-8').strip()
            if folder:
                self.raw_src = folder
                self.save_last_folder(folder)
                self.path_label.configure(text=ar(f"المجلد المختار: {folder}"))
                self.log("تم تحديث المجلد بنجاح.")
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            self.log("تعذر فتح نافذة اختيار المجلد. تأكد من توفر zenity.")

    def serialize_map_additions(self):
        additions = self.user_config.get("category_extensions_additions", {})
        if not isinstance(additions, dict):
            return ""
        lines = []
        for category, exts in additions.items():
            if not isinstance(category, str):
                continue
            normalized_exts = self.normalize_extensions(exts if isinstance(exts, list) else [])
            if normalized_exts:
                lines.append(f"{category}: {', '.join(normalized_exts)}")
        return "\n".join(lines)

    def open_settings_window(self):
        settings = ctk.CTkToplevel(self)
        settings.title(ar_title("الإعدادات"))
        width, height = 620, 500
        self.update_idletasks()
        root_x = self.winfo_x()
        root_y = self.winfo_y()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        pos_x = root_x + (root_w - width) // 2
        pos_y = root_y + (root_h - height) // 2
        settings.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        settings.attributes("-topmost", True)

        help_text = (
            "الإضافات فقط: لن يتم حذف الامتدادات الأساسية.\n"
            "1) كلمات مالية/قانونية إضافية: كلمة بكل سطر.\n"
            "2) امتدادات إضافية: كل سطر بصيغة Category: ext1, ext2"
        )
        ctk.CTkLabel(settings, text=ar(help_text), justify="left", wraplength=680).pack(pady=10)

        ctk.CTkLabel(settings, text=ar("كلمات مفتاحية إضافية")).pack()
        keyword_box = ctk.CTkTextbox(settings, width=700, height=160)
        keyword_box.pack(pady=6)
        existing_keywords = self.user_config.get("finance_keywords_additions", [])
        keyword_box.insert("1.0", "\n".join(existing_keywords if isinstance(existing_keywords, list) else []))

        ctk.CTkLabel(settings, text=ar("تصنيفات/امتدادات إضافية")).pack(pady=(6, 0))
        map_box = ctk.CTkTextbox(settings, width=700, height=200)
        map_box.pack(pady=6)
        map_box.insert("1.0", self.serialize_map_additions())

        ctk.CTkButton(
            settings,
            text=ar("حفظ الإعدادات"),
            command=lambda: self.save_settings_from_window(keyword_box, map_box, settings)
        ).pack(pady=10)

    def parse_map_text(self, raw_text):
        parsed = {}
        for line_no, line in enumerate(raw_text.splitlines(), start=1):
            clean_line = line.strip()
            if not clean_line:
                continue
            if ":" not in clean_line:
                raise ValueError(f"السطر {line_no} غير صحيح: استخدم الصيغة Category: ext1, ext2")
            category, extensions_part = clean_line.split(":", 1)
            clean_category = category.strip()
            if not clean_category:
                raise ValueError(f"اسم التصنيف فارغ في السطر {line_no}.")
            extensions = self.normalize_extensions(extensions_part.split(","))
            if not extensions:
                raise ValueError(f"لا توجد امتدادات صالحة في السطر {line_no}.")
            if clean_category not in parsed:
                parsed[clean_category] = []
            for ext in extensions:
                if ext not in parsed[clean_category]:
                    parsed[clean_category].append(ext)
        return parsed

    def save_settings_from_window(self, keyword_box, map_box, window):
        raw_keywords = keyword_box.get("1.0", "end").strip()
        raw_map = map_box.get("1.0", "end").strip()
        additions_keywords = []
        for line in raw_keywords.splitlines():
            clean_word = line.strip().lower()
            if clean_word and clean_word not in additions_keywords:
                additions_keywords.append(clean_word)
        try:
            additions_map = self.parse_map_text(raw_map) if raw_map else {}
        except ValueError as err:
            self.show_finish_message("خطأ في الإعدادات", str(err))
            self.log(str(err))
            return

        self.user_config = {
            "finance_keywords_additions": additions_keywords,
            "category_extensions_additions": additions_map
        }
        self.save_app_config(self.user_config)
        self.apply_user_config()
        self.log("تم حفظ الإعدادات الجديدة بنجاح.")
        window.destroy()
        self.show_finish_message("تم الحفظ", "تم تحديث الإعدادات دون حذف أي امتداد أساسي.")

    def next_available_path(self, path):
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        index = 1
        while True:
            candidate = path.with_name(f"{stem}_{index}{suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def safe_move(self, src_path, dest_dir):
        dest_dir.mkdir(exist_ok=True)
        destination = self.next_available_path(dest_dir / src_path.name)
        shutil.move(str(src_path), str(destination))
        return destination

    def check_content(self, file_path):
        ext = file_path.suffix.lower()
        try:
            if ext == ".pdf":
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    if not reader.pages:
                        return False
                    first_page_text = reader.pages[0].extract_text() or ""
                    text_content = first_page_text.lower()
            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read(1000).lower()
            else:
                return False
            return any(word in text_content for word in self.finance_keywords)
        except (OSError, UnicodeDecodeError, PyPDF2.errors.PdfReadError, IndexError):
            return False

    def validate_source(self):
        source = Path(self.raw_src)
        if not source.exists() or not source.is_dir():
            self.show_finish_message("خطأ", "المجلد المحدد غير صالح. اختر مجلدًا صحيحًا.")
            self.log("فشل التحقق من المجلد المحدد.")
            return None
        return source

    def start_smart_analysis(self):
        source = self.validate_source()
        if source is None:
            return

        self.log("بدأ التنظيم الشامل.")
        moved_count = 0
        ext_to_cat = {ext.lower(): cat for cat, exts in self.map_by_category.items() for ext in exts}
        
        for p in source.iterdir():
            if p.is_file():
                ext = p.suffix.lower().lstrip(".")
                if ext in ["pdf", "txt"] and self.check_content(p):
                    dest_dir = source / "Finance_&_Legal"
                    moved_to = self.safe_move(p, dest_dir)
                    self.log(f"نقل الملف المالي/القانوني: {moved_to.name}")
                    moved_count += 1
                    continue
                if ext in ext_to_cat:
                    target_folder = ext_to_cat[ext]
                    dest_dir = source / target_folder
                    moved_to = self.safe_move(p, dest_dir)
                    self.log(f"نقل الملف: {moved_to.name} -> {target_folder}")
                    moved_count += 1

        self.log("اكتملت عملية التنظيم.")
        
        play_alert_sound()
        
        self.show_finish_message("اكتمل التنظيم", f"تمت معالجة {moved_count} ملف بنجاح!")

    def run_smart_cleanup(self):
        source = self.validate_source()
        if source is None:
            return

        self.log("بدأ التنظيف الذكي.")
        cleanup_dir = source / "Smart_Cleanup"
        days, current_time, count = 30, time.time(), 0
        target_exts = ['.deb', '.iso', '.zip', '.tar', '.gz']

        for p in source.iterdir():
            if p.is_file() and p.suffix.lower() in target_exts:
                if (current_time - p.stat().st_mtime) / 86400 > days:
                    moved_to = self.safe_move(p, cleanup_dir)
                    self.log(f"عزل ملف قديم: {moved_to.name}")
                    count += 1

        play_alert_sound()
        self.log("اكتملت عملية التنظيف الذكي.")
        
        self.show_finish_message("التنظيف الذكي", f"تم عزل {count} ملف قديم.")

    def show_finish_message(self, title, message):
        msg_window = ctk.CTkToplevel(self)
        msg_window.title(ar_title(title))
        width, height = 350, 180
        self.update_idletasks()
        root_x = self.winfo_x()
        root_y = self.winfo_y()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        pos_x = root_x + (root_w - width) // 2
        pos_y = root_y + (root_h - height) // 2
        msg_window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        msg_window.attributes("-topmost", True)
        ctk.CTkLabel(msg_window, text=ar(message), pady=25).pack()
        ctk.CTkButton(msg_window, text=ar("موافق"), command=msg_window.destroy).pack()

if __name__ == "__main__":
    app = AlaasOrganizerV1_4_0()
    app.mainloop()
