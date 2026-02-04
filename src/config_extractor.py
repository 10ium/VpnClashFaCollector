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

# دامین‌های وایت و تمیز کلادفلر برای جایگزینی
CLEAN_IP_DOMAINS = ['FUCK.TAWANAPROXY.ONLINE', 'FUCK1.TAWANAPROXY.ONLINE']

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
    """
    بررسی می‌کند که آیا کانفیگ از دامنه‌های کلادفلر استفاده می‌کند یا خیر.
    """
    try:
        if not link.startswith('vmess://'):
            parsed = urlparse(link)
            if parsed.hostname and parsed.hostname.lower().endswith(CLOUDFLARE_DOMAINS):
                return True
            query = parse_qs(parsed.query)
            for param in ['sni', 'host', 'peer']:
                values = query.get(param, [])
                for val in values:
                    if val.lower().endswith(CLOUDFLARE_DOMAINS):
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
                    value = data.get(field, '')
                    if value and str(value).lower().endswith(CLOUDFLARE_DOMAINS):
                        return True
            except: return False
    except: return False
    return False

def generate_clean_ip_configs(link):
    """
    دامین‌های کلادفلر را با دامین‌های تمیز جایگزین کرده و از هر کانفیگ دو نسخه می‌سازد.
    """
    new_configs = []
    try:
        for clean_domain in CLEAN_IP_DOMAINS:
            if not link.startswith('vmess://'):
                parsed = urlparse(link)
                query = parse_qs(parsed.query)
                
                # جایگزینی در بخش‌های مختلف
                new_hostname = parsed.hostname
                if new_hostname and new_hostname.lower().endswith(CLOUDFLARE_DOMAINS):
                    new_hostname = clean_domain
                
                for param in ['sni', 'host', 'peer']:
                    if param in query:
                        query[param] = [clean_domain if v.lower().endswith(CLOUDFLARE_DOMAINS) else v for v in query[param]]
                
                # بازسازی URL
                new_query_str = urlencode(query, doseq=True)
                new_netloc = new_hostname
                if parsed.port: new_netloc += f":{parsed.port}"
                if parsed.username: new_netloc = f"{parsed.username}@{new_netloc}"
                
                new_link = urlunparse((parsed.scheme, new_netloc, parsed.path, parsed.params, new_query_str, parsed.fragment))
                new_configs.append(new_link)
            
            else:
                # برای VMess
                b64_str = link[8:]
                missing_padding = len(b64_str) % 4
                if missing_padding: b64_str += '=' * (4 - missing_padding)
                
                decoded = base64.b64decode(b64_str).decode('utf-8')
                data = json.loads(decoded)
                
                for field in ['add', 'host', 'sni']:
                    if data.get(field, '').lower().endswith(CLOUDFLARE_DOMAINS):
                        data[field] = clean_domain
                
                # اضافه کردن تگ برای تمایز
                if 'ps' in data:
                    data['ps'] = f"{data['ps']} - CleanIP"
                
                new_b64 = base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
                new_configs.append(f"vmess://{new_b64}")
                
    except Exception as e:
        logger.debug(f"Error in clean IP generation: {e}")
        
    return new_configs

def save_content(directory, filename, content_list):
    if not content_list: return
    content_sorted = sorted(list(set(content_list)))
    content_str = "\n".join(content_sorted)
    with open(os.path.join(directory, f"{filename}.txt"), "w", encoding="utf-8") as f:
        f.write(content_str)
    b64_str = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    with open(os.path.join(directory, f"{filename}_base64.txt"), "w", encoding="utf-8") as f:
        f.write(b64_str)

def write_files(data_map, output_dir):
    if not any(data_map.values()): return
    os.makedirs(output_dir, exist_ok=True)
    
    mixed_content = set()
    cloudflare_content = set()
    cloudflare_clean_ip_content = set() # خروجی جدید
    
    for proto, lines in data_map.items():
        if not lines: continue
        
        if proto != 'tg':
            mixed_content.update(lines)
            for line in lines:
                if is_behind_cloudflare(line):
                    cloudflare_content.add(line)
                    # تولید نسخه‌های IP تمیز
                    clean_versions = generate_clean_ip_configs(line)
                    cloudflare_clean_ip_content.update(clean_versions)
            
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
    if cloudflare_clean_ip_content:
        save_content(output_dir, "cloudflare_clean_ip", cloudflare_clean_ip_content)

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
            logger.error(f"Error: {e}")
            
    if sum(len(v) for v in global_collection.values()) > 0:
        write_files(global_collection, os.path.join(out_dir, "all"))

def get_flexible_pattern(protocol_prefix):
    if protocol_prefix == 'tg':
        prefix = rf'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)'
    else:
        prefix = rf'{protocol_prefix}:\/\/'
    return rf'{prefix}(?:(?!\s{{4,}}|[()\[\]]).)+?(?={NEXT_CONFIG_LOOKAHEAD}|$)'

if __name__ == "__main__":
    main()
