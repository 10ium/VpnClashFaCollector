import os
import re
import base64
import logging

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Extractor")

# لیست پروتکل‌های مورد حمایت
PROTOCOLS = [
    'vmess', 'vless', 'trojan', 'ss', 'ssr', 'tuic', 'hysteria', 'hysteria2', 
    'hy2', 'juicity', 'snell', 'mieru', 'anytls', 'ssh', 'wireguard', 'wg', 
    'warp', 'socks', 'socks4', 'socks5', 'tg'
]

# اصلاح Lookahead برای شامل شدن هر دو مدل لینک تلگرام
NEXT_CONFIG_LOOKAHEAD = r'(?=' + '|'.join([rf'{p}:\/\/' for p in PROTOCOLS if p != 'tg']) + r'|https:\/\/t\.me\/proxy\?|tg:\/\/proxy\?)'

def get_flexible_pattern(protocol_prefix):
    """
    ایجاد الگو با تمرکز بر تجمیع لینک‌های تلگرام در پروتکل tg
    """
    if protocol_prefix == 'tg':
        prefix = rf'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)'
    else:
        prefix = rf'{protocol_prefix}:\/\/'

    return rf'{prefix}(?:(?!\s{{4,}}).)+?(?=\s{{4,}}|\n|{NEXT_CONFIG_LOOKAHEAD}|$)'

# تولید داینامیک الگوها
PATTERNS = {p: get_flexible_pattern(p) for p in PROTOCOLS}

def is_windows_compatible(link):
    """
    بررسی سازگاری لینک MTProxy با نسخه ویندوز تلگرام.
    ملاک: عدم شروع سکرت با ee و عدم وجود Padding بسیار طولانی.
    """
    secret_match = re.search(r"secret=([a-zA-Z0-9]+)", link)
    if not secret_match:
        return True
    secret = secret_match.group(1).lower()
    
    # پروتکل ee (Extensible) یا سکرت‌های بسیار طولانی در ویندوز پشتیبانی نمی‌شوند
    if secret.startswith('ee') or len(secret) > 64:
        return False
    return True

def save_content(directory, filename, content_list):
    """تابع کمکی برای ذخیره متنی و بیس64"""
    if not content_list:
        return
    
    content_sorted = sorted(list(content_list))
    content_str = "\n".join(content_sorted)
    
    # ذخیره فایل متنی
    with open(os.path.join(directory, f"{filename}.txt"), "w", encoding="utf-8") as f:
        f.write(content_str)
    
    # ذخیره فایل Base64
    b64_str = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    with open(os.path.join(directory, f"{filename}_base64.txt"), "w", encoding="utf-8") as f:
        f.write(b64_str)

def write_files(data_map, output_dir):
    """ذخیره کانفیگ‌ها با تفکیک هوشمند برای ویندوز و اندروید"""
    if not any(data_map.values()):
        return

    os.makedirs(output_dir, exist_ok=True)
    mixed_content = set()
    
    for proto, lines in data_map.items():
        if not lines: continue
        
        mixed_content.update(lines)
        
        # اگر پروتکل تلگرام است، تفکیک سیستمی انجام شود
        if proto == 'tg':
            windows_tg = {l for l in lines if is_windows_compatible(l)}
            android_tg = lines  # اندروید از همه مدل‌ها پشتیبانی می‌کند
            
            save_content(output_dir, "tg", lines) # فایل اصلی میکس
            save_content(output_dir, "tg_windows", windows_tg)
            save_content(output_dir, "tg_android", android_tg)
        else:
            # سایر پروتکل‌ها به روال عادی
            save_content(output_dir, proto, lines)

    # خروجی Mixed کلی
    if mixed_content:
        save_content(output_dir, "mixed", mixed_content)

def main():
    src_dir = "src/telegram"
    out_dir = "sub"
    global_collection = {k: set() for k in PATTERNS.keys()}
    
    if not os.path.exists(src_dir):
        logger.error(f"دایرکتوری منبع {src_dir} یافت نشد.")
        return

    for channel_name in os.listdir(src_dir):
        channel_path = os.path.join(src_dir, channel_name)
        md_file = os.path.join(channel_path, "messages.md")
        
        if not os.path.isfile(md_file): continue
        
        logger.info(f"در حال استخراج هوشمند از: {channel_name}")
        
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            channel_collection = {k: set() for k in PATTERNS.keys()}
            total_found = 0
            
            for proto, pattern in PATTERNS.items():
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    clean_conf = match.group(0).strip()
                    if clean_conf:
                        channel_collection[proto].add(clean_conf)
                        global_collection[proto].add(clean_conf)
                        total_found += 1
            
            if total_found > 0:
                write_files(channel_collection, os.path.join(out_dir, channel_name))
                logger.info(f"   -> {total_found} کانفیگ استخراج و تفکیک شد.")

        except Exception as e:
            logger.error(f"خطا در پردازش {channel_name}: {e}")

    logger.info("="*30)
    logger.info("در حال ساخت سابسکرایب جامع پلتفرم‌ها...")
    total_global = sum(len(v) for v in global_collection.values())
    
    if total_global > 0:
        write_files(global_collection, os.path.join(out_dir, "all"))
        logger.info(f"✅ عملیات موفق. فایلهای tg_windows و tg_android در {out_dir}/all آماده هستند.")
    else:
        logger.warning("⚠️ هیچ کانفیگی یافت نشد.")

if __name__ == "__main__":
    main()
