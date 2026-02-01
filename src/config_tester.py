import os
import subprocess
import logging
import zipfile
import requests
import csv
import base64
import json
from urllib.parse import quote, unquote

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Tester")

def get_flag_emoji(country_code):
    if not country_code or country_code.lower() == "unknown" or len(country_code) != 2:
        return "🌐"
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())

def download_xray_knife():
    if os.path.exists("xray-knife"): return
    url = "https://github.com/lilendian0x00/xray-knife/releases/latest/download/Xray-knife-linux-64.zip"
    logger.info("Downloading xray-knife...")
    r = requests.get(url, timeout=30)
    with open("xray-knife.zip", "wb") as f: f.write(r.content)
    with zipfile.ZipFile("xray-knife.zip", 'r') as zip_ref:
        zip_ref.extractall("xray-knife-dir")
    for root, dirs, files in os.walk("xray-knife-dir"):
        for file in files:
            if file == "xray-knife":
                os.rename(os.path.join(root, file), "xray-knife")
                break
    os.chmod("xray-knife", 0o755)

def rename_config(link, info_dict):
    """تغییر نام منعطف کانفیگ بر اساس اطلاعات موجود"""
    flag = get_flag_emoji(info_dict.get('country', ''))
    ping = info_dict.get('ping', '')
    speed = info_dict.get('speed', '')
    
    # ساختن برچسب نام: [Flag] [Country] | [Ping]ms | [Speed]MB
    parts = [flag, info_dict.get('country', '')]
    if ping: parts.append(f"{ping}ms")
    if speed:
        s_val = f"{float(speed)/1024:.1f}MB" if str(speed).replace('.','').isdigit() else speed
        parts.append(s_val)
    
    info_tag = " | ".join([p for p in parts if p]) + " | "
    
    try:
        if link.startswith("vmess://"):
            v2_json_str = base64.b64decode(link[8:]).decode('utf-8')
            data = json.loads(v2_json_str)
            data['ps'] = info_tag + data.get('ps', 'Server')
            return "vmess://" + base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
        elif any(link.startswith(p) for p in ["vless://", "trojan://", "ss://", "ssr://", "wireguard://"]):
            base, remark = link.split("#", 1) if "#" in link else (link, "Server")
            new_remark = info_tag + unquote(remark)
            return f"{base}#{quote(new_remark)}"
        return link
    except:
        return link

def run_test(input_path, output_csv, threads=50, speedtest=False):
    cmd = [
        "./xray-knife", "http", "-f", input_path,
        "-t", str(threads), "-o", output_csv, "-x", "csv"
    ]
    if speedtest: cmd.append("-p")
    subprocess.run(cmd, check=False)

def test_process():
    input_file = "sub/all/mixed.txt"
    output_dir = "sub/tested"
    os.makedirs(output_dir, exist_ok=True)
    download_xray_knife()

    # --- فاز ۱: تست پینگ بر روی همه ---
    logger.info("Phase 1: Ping testing all configs...")
    run_test(input_file, "ping_results.csv", threads=50, speedtest=False)
    
    ping_passed_links = []
    top_300_input = "top_300_for_speed.txt"
    
    if os.path.exists("ping_results.csv"):
        with open("ping_results.csv", "r", encoding="utf-8") as f:
            results = list(csv.DictReader(f))
            # مرتب‌سازی بر اساس پینگ (کمترین پینگ اول)
            results.sort(key=lambda x: int(x.get('Delay', 9999)) if str(x.get('Delay')).isdigit() else 9999)
            
            for row in results:
                link = row.get('Config') or row.get('Link')
                if link and int(row.get('Delay', 0)) > 0:
                    labeled = rename_config(link, {
                        'country': row.get('Country Code', 'UN'),
                        'ping': row.get('Delay')
                    })
                    ping_passed_links.append(labeled)

        # ذخیره خروجی پینگ‌دارها
        with open(os.path.join(output_dir, "ping_passed.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(ping_passed_links))
        
        # جدا کردن ۳۰۰ تای اول برای تست سرعت
        top_configs = [row.get('Config') or row.get('Link') for row in results[:300]]
        with open(top_300_input, "w", encoding="utf-8") as f:
            f.write("\n".join(top_configs))

        # --- فاز ۲: تست سرعت بر روی ۳۰۰ تای برتر ---
        logger.info("Phase 2: Speed testing top 300 configs...")
        run_test(top_300_input, "speed_results.csv", threads=10, speedtest=True)
        
        if os.path.exists("speed_results.csv"):
            speed_passed_links = []
            with open("speed_results.csv", "r", encoding="utf-8") as f:
                s_results = list(csv.DictReader(f))
                for row in s_results:
                    link = row.get('Config') or row.get('Link')
                    speed = row.get('Download Speed') or row.get('Speed', '0')
                    if link and (float(speed) > 0 if str(speed).replace('.','').isdigit() else False):
                        labeled = rename_config(link, {
                            'country': row.get('Country Code', 'UN'),
                            'ping': row.get('Delay'),
                            'speed': speed
                        })
                        speed_passed_links.append(labeled)
            
            with open(os.path.join(output_dir, "speed_passed.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(speed_passed_links))
            
            logger.info(f"✅ Finished. Ping-passed: {len(ping_passed_links)}, Speed-passed: {len(speed_passed_links)}")

if __name__ == "__main__":
    test_process()
