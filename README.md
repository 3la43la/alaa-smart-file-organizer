# Alaa Smart File Organizer

تطبيق سطح مكتب بـ Python لتنظيم الملفات تلقائيًا حسب الامتداد، مع تحليل بسيط للمحتوى المالي/القانوني داخل ملفات `PDF` و`TXT`.

## Features
- تنظيم الملفات إلى مجلدات مثل: `Videos`, `Images`, `Documents`, `Archives` وغيرها.
- تصنيف ملفات مالية/قانونية إلى مجلد `Finance_&_Legal` حسب كلمات مفتاحية.
- تنظيف الملفات القديمة إلى `Smart_Cleanup`.
- واجهة عربية باستخدام `customtkinter`.
- إعدادات إضافية عبر `config.json` بدون حذف الامتدادات الأساسية.

## Requirements
- Python 3
- المكتبات:
  - `customtkinter`
  - `arabic_reshaper`
  - `python-bidi`
  - `PyPDF2`

## Run
```bash
python3 o.py
```

## Config
- `config.json`:
  - `finance_keywords_additions`: كلمات إضافية للتحليل المالي/القانوني.
  - `category_extensions_additions`: امتدادات إضافية لكل تصنيف.

## Notes
- آخر مجلد مستخدم يُحفظ في `last_folder.txt`.
- التنبيه الصوتي يعتمد على `paplay` في Linux.
