import os
import re
import base64
import logging
import html
import json
import copy
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

# --- تنظیمات لاگ ---
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Extractor")

PROTOCOLS = [
    'vmess', 'vless', 'trojan', 'ss', 'ssr', 'tuic', 'hysteria', 'hysteria2', 
    'hy2', 'juicity', 'snell', 'anytls', 'ssh', 'wireguard', 'wg', 
    'warp', 'socks', 'socks4', 'socks5', 'tg'
]

# دامنه‌هایی که نشان‌دهنده استفاده از سرویس‌های کلادفلر هستند
CLOUDFLARE_DOMAINS = ('.workers.dev', '.pages.dev', '.trycloudflare.com', 'chatgpt.com')

NEXT_CONFIG_LOOKAHEAD = r'(?=' + '|'.join([rf'{p}:\/\/' for p in PROTOCOLS if p != 'tg']) + r'|https:\/\/t\.me\/proxy\?|tg:\/\/proxy\?|[()\[\]"\'\s])'

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
    """ذخیره محتوا به صورت فایل متنی و Base64"""
    if not content_list: return
    content_sorted = sorted(list(set(content_list)))
    content_str = "\n".join(content_sorted)
    
    with open(os.path.join(directory, f"{filename}.txt"), "w", encoding="utf-8") as f:
        f.write(content_str)
    
    b64_str = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    with open(os.path.join(directory, f"{filename}_base64.txt"), "w", encoding="utf-8") as f:
        f.write(b64_str)

def write_files(data_map, output_dir):
    """مدیریت نوشتن فایل‌های تفکیک شده و میکس کردن هیستریا"""
    if not any(data_map.values()): return
    os.makedirs(output_dir, exist_ok=True)
    
    mixed_content = set()
    cloudflare_content = set()
    
    # میکس کردن hysteria2 و hy2 در یک لیست واحد
    hy2_combined = set()
    if 'hysteria2' in data_map: hy2_combined.update(data_map['hysteria2'])
    if 'hy2' in data_map: hy2_combined.update(data_map['hy2'])
    
    # حذف hy2 تکی از نقشه داده‌ها برای جلوگیری از تکرار و جایگزینی با لیست ترکیبی
    processed_map = copy.deepcopy(data_map)
    if 'hy2' in processed_map: del processed_map['hy2']
    processed_map['hysteria2'] = hy2_combined

    for proto, lines in processed_map.items():
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
    """تولید نسخه Base64 برای تمامی فایل‌های متنی فاقد آن (مانند خروجی تستر)"""
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

def main():
    src_dir = "src/telegram"
    out_dir = "sub"
    global_collection = {k: set() for k in PROTOCOLS}
    if not os.path.exists(src_dir): return
    patterns = {p: get_flexible_pattern(p) for p in PROTOCOLS}

    for channel_name in os.listdir(src_dir):
        channel_path = os.path.join(src_dir, channel_name)
        md_file = os.path.join(channel_path, "messages.md")
        if not os.path.isfile(md_file): continue
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            channel_collection = {k: set() for k in PROTOCOLS}
            for proto, pattern in patterns.items():
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    raw_link = match.group(0).strip()
                    clean_link = clean_telegram_link(raw_link) if proto == 'tg' else raw_link
                    if clean_link:
                        channel_collection[proto].add(clean_link)
                        global_collection[proto].add(clean_link)
            write_files(channel_collection, os.path.join(out_dir, channel_name))
        except Exception as e:
            logger.error(f"Error processing {channel_name}: {e}")
            
    if sum(len(v) for v in global_collection.values()) > 0:
        write_files(global_collection, os.path.join(out_dir, "all"))

    # نهایی‌سازی: تولید خودکار فایل‌های Base64 برای خروجی‌های تستر یا فایل‌های دستی
    auto_base64_all(out_dir)

def get_flexible_pattern(protocol_prefix):
    if protocol_prefix == 'tg':
        prefix = rf'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)'
    else:
        prefix = rf'{protocol_prefix}:\/\/'
    return rf'{prefix}(?:(?!\s{{4,}}|[()\[\]]).)+?(?={NEXT_CONFIG_LOOKAHEAD}|$)'

if __name__ == "__main__":
    main()
