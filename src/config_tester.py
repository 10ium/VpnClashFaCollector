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
    if not link: return None
    flag = get_flag_emoji(info_dict.get('country', ''))
    ping = info_dict.get('ping', '')
    speed = info_dict.get('speed', '')
    
    parts = [flag, info_dict.get('country', '')]
    if ping: parts.append(f"{ping}ms")
    if speed:
        try:
            s_val = f"{float(speed)/1024:.1f}MB"
            parts.append(s_val)
        except: parts.append(str(speed))
    
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

    # --- فاز ۱: تست پینگ ---
    logger.info("Phase 1: Ping testing...")
    run_test(input_file, "ping_results.csv", threads=50, speedtest=False)
    
    if not os.path.exists("ping_results.csv"):
        logger.error("Ping results CSV not found!")
        return

    ping_passed_links = []
    valid_rows_for_speed = []

    with open("ping_results.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = row.get('Config') or row.get('Link')
            delay_str = row.get('Delay') or row.get('Real Delay')
            
            # فقط مواردی که لینک دارند و پینگ‌شان معتبر (عدد مثبت) است
            if link and delay_str and str(delay_str).isdigit():
                delay_int = int(delay_str)
                if delay_int > 0:
                    labeled = rename_config(link, {
                        'country': row.get('Country Code') or row.get('Country', 'UN'),
                        'ping': delay_str
                    })
                    if labeled: ping_passed_links.append(labeled)
                    valid_rows_for_speed.append(row)

    # ذخیره همه پینگ‌دارها
    with open(os.path.join(output_dir, "ping_passed.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ping_passed_links))
    
    # مرتب‌سازی برای انتخاب ۳۰۰ تای برتر
    valid_rows_for_speed.sort(key=lambda x: int(x.get('Delay') or x.get('Real Delay') or 9999))
    top_rows = valid_rows_for_speed[:300]
    
    top_configs_links = [r.get('Config') or r.get('Link') for r in top_rows if (r.get('Config') or r.get('Link'))]
    
    if top_configs_links:
        top_300_input = "top_300_for_speed.txt"
        with open(top_300_input, "w", encoding="utf-8") as f:
            f.write("\n".join(top_configs_links))

        # --- فاز ۲: تست سرعت ---
        logger.info(f"Phase 2: Speed testing top {len(top_configs_links)} configs...")
        run_test(top_300_input, "speed_results.csv", threads=10, speedtest=True)
        
        if os.path.exists("speed_results.csv"):
            speed_passed_links = []
            with open("speed_results.csv", "r", encoding="utf-8") as f:
                s_reader = csv.DictReader(f)
                for s_row in s_reader:
                    s_link = s_row.get('Config') or s_row.get('Link')
                    s_speed = s_row.get('Download Speed') or s_row.get('Speed', '0')
                    
                    if s_link and (float(s_speed) > 0 if str(s_speed).replace('.','').isdigit() else False):
                        labeled = rename_config(s_link, {
                            'country': s_row.get('Country Code') or s_row.get('Country', 'UN'),
                            'ping': s_row.get('Delay') or s_row.get('Real Delay'),
                            'speed': s_speed
                        })
                        if labeled: speed_passed_links.append(labeled)
            
            with open(os.path.join(output_dir, "speed_passed.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(speed_passed_links))
    
    logger.info("✅ All phases completed.")

if __name__ == "__main__":
    test_process()
