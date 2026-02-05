import os
import re
import base64
import logging
import html
import json
import copy
import shutil
import requests  # نیاز به نصب دارد: pip install requests
from urllib.parse import urlparse, parse_qs

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Extractor")

# ==========================================
# بخش تنظیمات کاربر (لینک‌های جهت تقسیم‌بندی)
# ==========================================
# فرمت: {'url': 'لینک', 'name': 'نام_پوشه', 'chunk_size': تعداد_در_هر_فایل}
SPLIT_SOURCES = [
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/tested/ping_passed.txt',
        'name': 'ping_passed',
        'chunk_size': 500
    },
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/mixed.txt',
        'name': 'mixed',
        'chunk_size': 500
    },
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/vless.txt',
        'name': 'vless',
        'chunk_size': 500
    },
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/vmess.txt',
        'name': 'vmess',
        'chunk_size': 500
    },
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/trojan.txt',
        'name': 'trojan.',
        'chunk_size': 500
    },
    {
        'url': 'https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/ss.txt',
        'name': 'ss',
        'chunk_size': 500
    },
    # لینک‌های بیشتر را اینجا اضافه کنید
    # {
    #     'url': 'LINK_2',
    #     'name': 'MyConfigCollection',
    #     'chunk_size': 20
    # },
]

# ==========================================
# تنظیمات عمومی و پروتکل‌ها
# ==========================================

PROTOCOLS = [
    'vmess', 'vless', 'trojan', 'ss', 'ssr', 'tuic', 'hysteria', 'hysteria2', 
    'hy2', 'juicity', 'snell', 'anytls', 'ssh', 'wireguard', 'wg', 
    'warp', 'socks', 'socks4', 'socks5', 'tg'
]

CLOUDFLARE_DOMAINS = ('.workers.dev', '.pages.dev', '.trycloudflare.com', 'chatgpt.com')

NEXT_CONFIG_LOOKAHEAD = r'(?=' + '|'.join([rf'{p}:\/\/' for p in PROTOCOLS if p != 'tg']) + r'|https:\/\/t\.me\/proxy\?|tg:\/\/proxy\?|[()\[\]"\'\s])'

# ==========================================
# توابع کمکی (Helper Functions)
# ==========================================

def get_flexible_pattern(protocol_prefix):
    if protocol_prefix == 'tg':
        prefix = rf'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)'
    else:
        prefix = rf'{protocol_prefix}:\/\/'
    return rf'{prefix}(?:(?!\s{{4,}}|[()\[\]]).)+?(?={NEXT_CONFIG_LOOKAHEAD}|$)'

def clean_telegram_link(link):
    """پاکسازی لینک تلگرام و تبدیل موجودیت‌های HTML"""
    link = html.unescape(link)
    link = re.sub(r'[()\[\]\s!.,;\'"]+$', '', link)
    return link

def is_windows_compatible(link):
    """اعمال فیلتر سخت‌گیرانه برای تلگرام دسکتاپ (ویندوز)"""
    secret_match = re.search(r"secret=([a-zA-Z0-9%_\-]+)", link)
    if not secret_match:
        return False
    
    secret = secret_match.group(1).lower()
    if '%' in secret or '_' in secret or '-' in secret:
        return False
    if secret.startswith('ee'):
        return False
    if secret.startswith('dd'):
        actual_secret = secret[2:]
    else:
        actual_secret = secret
    if not re.fullmatch(r'[0-9a-f]{32}', actual_secret):
        return False
    return True

def is_behind_cloudflare(link):
    """بررسی می‌کند که آیا کانفیگ از دامنه‌های کلادفلر استفاده می‌کند یا خیر"""
    def check_domain(domain):
        if not domain: return False
        domain = domain.lower()
        return domain == "chatgpt.com" or any(domain.endswith(d) for d in CLOUDFLARE_DOMAINS)

    try:
        if not link.startswith('vmess://'):
            parsed = urlparse(link)
            if check_domain(parsed.hostname):
                return True
            query = parse_qs(parsed.query)
            for param in ['sni', 'host', 'peer']:
                values = query.get(param, [])
                if any(check_domain(v) for v in values):
                    return True
            return False
        else:
            b64_str = link[8:]
            missing_padding = len(b64_str) % 4
            if missing_padding: b64_str += '=' * (4 - missing_padding)
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8')
                data = json.loads(decoded)
                for field in ['add', 'host', 'sni']:
                    if check_domain(data.get(field)):
                        return True
            except: return False
    except: return False
    return False

def save_content(directory, filename, content_list):
    """ذخیره محتوا به صورت فایل متنی و Base64 (نسخه استاندارد)"""
    if not content_list: return
    # حذف دایرکتوری در صورت وجود فایل (برای جلوگیری از تداخل)
    os.makedirs(directory, exist_ok=True)
    
    content_sorted = sorted(list(set(content_list)))
    content_str = "\n".join(content_sorted)
    
    # ذخیره فایل معمولی
    file_path = os.path.join(directory, f"{filename}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content_str)
    
    # ذخیره فایل Base64
    b64_str = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    b64_path = os.path.join(directory, f"{filename}_base64.txt")
    with open(b64_path, "w", encoding="utf-8") as f:
        f.write(b64_str)

def extract_configs_from_text(text):
    """استخراج کانفیگ‌ها از یک متن خام"""
    patterns = {p: get_flexible_pattern(p) for p in PROTOCOLS}
    extracted_data = {k: set() for k in PROTOCOLS}
    
    for proto, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            raw_link = match.group(0).strip()
            clean_link = clean_telegram_link(raw_link) if proto == 'tg' else raw_link
            if clean_link:
                extracted_data[proto].add(clean_link)
    
    return extracted_data

def merge_hysteria(data_map):
    """ترکیب hy2 و hysteria2 در یک کلید واحد"""
    hy2_combined = set()
    if 'hysteria2' in data_map: hy2_combined.update(data_map['hysteria2'])
    if 'hy2' in data_map: hy2_combined.update(data_map['hy2'])
    
    processed_map = copy.deepcopy(data_map)
    # حذف کلید hy2
    if 'hy2' in processed_map: del processed_map['hy2']
    # ذخیره همه در hysteria2
    processed_map['hysteria2'] = hy2_combined
    return processed_map

def write_files_standard(data_map, output_dir):
    """مدیریت نوشتن فایل‌های تفکیک شده (روش استاندارد قدیمی)"""
    # ادغام هیستریا قبل از نوشتن
    final_map = merge_hysteria(data_map)
    
    if not any(final_map.values()): return
    os.makedirs(output_dir, exist_ok=True)
    
    mixed_content = set()
    cloudflare_content = set()
    
    for proto, lines in final_map.items():
        if not lines: continue
        
        if proto != 'tg':
            mixed_content.update(lines)
            for line in lines:
                if is_behind_cloudflare(line):
                    cloudflare_content.add(line)
            
        if proto == 'tg':
            windows_tg = {l for l in lines if is_windows_compatible(l)}
            save_content(output_dir, "tg", lines)
            save_content(output_dir, "tg_windows", windows_tg)
            save_content(output_dir, "tg_android", lines)
        else:
            save_content(output_dir, proto, lines)
            
    if mixed_content:
        save_content(output_dir, "mixed", mixed_content)
    if cloudflare_content:
        save_content(output_dir, "cloudflare", cloudflare_content)

def auto_base64_all(directory):
    """تولید نسخه Base64 برای تمامی فایل‌های متنی"""
    if not os.path.exists(directory): return
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt") and not file.endswith("_base64.txt"):
                name_without_ext = file[:-4]
                base64_name = f"{name_without_ext}_base64.txt"
                if base64_name not in files:
                    try:
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        if content.strip():
                            b64_data = base64.b64encode(content.encode("utf-8")).decode("utf-8")
                            with open(os.path.join(root, base64_name), "w", encoding="utf-8") as f:
                                f.write(b64_data)
                    except Exception as e:
                        logger.error(f"Auto-base64 error for {file}: {e}")

def cleanup_legacy_hy2(directory):
    """حذف فایل‌های hy2.txt و hy2_base64.txt در صورت وجود"""
    if not os.path.exists(directory): return
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "hy2.txt" or file == "hy2_base64.txt":
                try:
                    os.remove(os.path.join(root, file))
                    logger.info(f"Deleted legacy file: {os.path.join(root, file)}")
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")

# ==========================================
# توابع جدید برای قابلیت Splitting
# ==========================================

def fetch_url_content(url):
    """دانلود محتوا از لینک"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return ""

def save_split_output(config_list, base_name, chunk_size):
    """ذخیره لیست کانفیگ‌ها به صورت فایل‌های خرد شده"""
    if not config_list:
        return
    
    # مرتب‌سازی و حذف تکراری‌ها
    unique_configs = sorted(list(set(config_list)))
    total_configs = len(unique_configs)
    
    # مسیرهای خروجی
    path_normal = os.path.join("sub", "split", "normal", base_name)
    path_base64 = os.path.join("sub", "split", "base64", base_name)
    
    # ساخت دایرکتوری‌ها (اگر وجود دارند پاک نمی‌شوند، روی آن‌ها نوشته می‌شود)
    os.makedirs(path_normal, exist_ok=True)
    os.makedirs(path_base64, exist_ok=True)
    
    # تقسیم‌بندی
    chunks = [unique_configs[i:i + chunk_size] for i in range(0, total_configs, chunk_size)]
    
    logger.info(f"Splitting '{base_name}': {total_configs} configs into {len(chunks)} files.")
    
    for idx, chunk in enumerate(chunks):
        file_number = str(idx + 1) # نام فایل: 1, 2, 3 ...
        content_str = "\n".join(chunk)
        b64_str = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        
        # 1. ذخیره نرمال: sub/split/normal/Name/1
        with open(os.path.join(path_normal, file_number), "w", encoding="utf-8") as f:
            f.write(content_str)
            
        # 2. ذخیره بیس64: sub/split/base64/Name/1
        with open(os.path.join(path_base64, file_number), "w", encoding="utf-8") as f:
            f.write(b64_str)

def process_split_mode():
    """اجرای منطق تقسیم‌بندی برای لینک‌های تعریف شده"""
    if not SPLIT_SOURCES:
        return

    logger.info("--- Starting Split Mode ---")
    
    for item in SPLIT_SOURCES:
        url = item.get('url')
        name = item.get('name')
        chunk_size = item.get('chunk_size', 50)
        
        if not url or not name: continue
        
        logger.info(f"Processing split for: {name}")
        content = fetch_url_content(url)
        
        if content:
            # استخراج
            extracted = extract_configs_from_text(content)
            
            # ادغام هیستریا (مهم: hy2 و hysteria2 یکی می‌شوند)
            merged_data = merge_hysteria(extracted)
            
            # جمع‌آوری تمام کانفیگ‌ها در یک لیست واحد برای تقسیم‌بندی
            all_configs = []
            for proto, lines in merged_data.items():
                if proto != 'tg': # معمولاً پروکسی تلگرام در سابسکریپشن کلاینت‌ها استفاده نمی‌شود، اما اگر نیاز بود حذف شرط کنید
                    all_configs.extend(lines)
            
            # ذخیره نهایی
            save_split_output(all_configs, name, chunk_size)

# ==========================================
# بدنه اصلی برنامه
# ==========================================

def main():
    # --- بخش 1: پردازش پوشه تلگرام (ویژگی قبلی) ---
    src_dir = "src/telegram"
    out_dir = "sub"
    global_collection = {k: set() for k in PROTOCOLS}
    
    if os.path.exists(src_dir):
        logger.info("--- Processing Telegram Directory ---")
        for channel_name in os.listdir(src_dir):
            channel_path = os.path.join(src_dir, channel_name)
            md_file = os.path.join(channel_path, "messages.md")
            if not os.path.isfile(md_file): continue
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                channel_data = extract_configs_from_text(content)
                
                # جمع‌آوری در گلوبال
                for p, s in channel_data.items():
                    global_collection[p].update(s)
                
                # نوشتن فایل‌های هر کانال
                write_files_standard(channel_data, os.path.join(out_dir, channel_name))
                
            except Exception as e:
                logger.error(f"Error processing channel {channel_name}: {e}")
        
        # نوشتن فایل All
        if sum(len(v) for v in global_collection.values()) > 0:
            write_files_standard(global_collection, os.path.join(out_dir, "all"))
    
    # --- بخش 2: پردازش لینک‌های اسپلیت (ویژگی جدید) ---
    process_split_mode()

    # --- بخش 3: نهایی‌سازی و پاکسازی ---
    auto_base64_all(out_dir)     # ساخت بیس64 برای فایل‌هایی که ندارند
    cleanup_legacy_hy2(out_dir)  # حذف hy2.txt و hy2_base64.txt از همه جا

if __name__ == "__main__":
    main()
