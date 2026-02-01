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
    if not country_code or len(str(country_code)) != 2: return "🌐"
    return "".join(chr(127397 + ord(c)) for c in str(country_code).upper())

def download_xray_knife():
    if os.path.exists("xray-knife"): return
    url = "https://github.com/lilendian0x00/xray-knife/releases/latest/download/Xray-knife-linux-64.zip"
    r = requests.get(url, timeout=30)
    with open("xray-knife.zip", "wb") as f: f.write(r.content)
    with zipfile.ZipFile("xray-knife.zip", 'r') as z: z.extractall("xray-knife-dir")
    for root, _, files in os.walk("xray-knife-dir"):
        for file in files:
            if file == "xray-knife":
                os.rename(os.path.join(root, file), "xray-knife")
    os.chmod("xray-knife", 0o755)

def rename_config(link, info):
    if not link: return None
    cc = str(info.get('cc', 'UN')).upper()
    flag = get_flag_emoji(cc)
    tag = f"{flag} {cc} | {info.get('ping', '?')}ms"
    if info.get('speed'): tag += f" | {info.get('speed')}"
    tag += " | "
    
    try:
        if link.startswith("vmess://"):
            data = json.loads(base64.b64decode(link[8:]).decode('utf-8'))
            data['ps'] = tag + data.get('ps', 'Server')
            return "vmess://" + base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
        elif "#" in link:
            base, remark = link.split("#", 1)
            return f"{base}#{quote(tag + unquote(remark))}"
        return f"{link}#{quote(tag + 'Server')}"
    except: return link

def test_process():
    input_file = "sub/all/mixed.txt"
    output_dir = "sub/tested"
    os.makedirs(output_dir, exist_ok=True)
    download_xray_knife()

    # مرحله ۱: تست پینگ
    logger.info("--- Phase 1: Latency Test ---")
    ping_csv = "res_ping.csv"
    if os.path.exists(ping_csv): os.remove(ping_csv)
    
    subprocess.run(["./xray-knife", "http", "-f", input_file, "-t", "50", "-o", ping_csv, "-x", "csv"], check=False)

    ping_ok = []
    top_list = []

    if os.path.exists(ping_csv):
        with open(ping_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            logger.info(f"Detected CSV Columns: {reader.fieldnames}") # بسیار مهم برای دیباگ
            
            for row in reader:
                # استخراج منعطف لینک، پینگ و کشور
                link = next((v for k, v in row.items() if k and k.lower() in ['config', 'link', 'url']), None)
                delay = next((v for k, v in row.items() if k and ('delay' in k.lower() or 'real' in k.lower())), '0')
                cc = next((v for k, v in row.items() if k and ('country' in k.lower() or 'cc' in k.lower())), 'UN')
                
                if link and str(delay).isdigit() and int(delay) > 0:
                    labeled = rename_config(link, {'cc': cc, 'ping': delay})
                    if labeled:
                        ping_ok.append(labeled)
                        row['sort_val'] = int(delay)
                        row['clean_link'] = link
                        top_list.append(row)

    # ذخیره فایل پینگ
    with open(os.path.join(output_dir, "ping_passed.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ping_ok) if ping_ok else "")
    
    logger.info(f"Configs with ping: {len(ping_ok)}")

    # مرحله ۲: تست سرعت (اگر پینگ‌داری وجود داشت)
    if top_list:
        top_list.sort(key=lambda x: x['sort_val'])
        top300_file = "top300.txt"
        with open(top300_file, "w", encoding="utf-8") as f:
            f.write("\n".join([r['clean_link'] for r in top_list[:300]]))

        logger.info(f"--- Phase 2: Speed Test on top {len(top_list[:300])} ---")
        speed_csv = "res_speed.csv"
        if os.path.exists(speed_csv): os.remove(speed_csv)
        
        subprocess.run(["./xray-knife", "http", "-f", top300_file, "-t", "5", "-o", speed_csv, "-x", "csv", "-p"], check=False)

        speed_ok = []
        if os.path.exists(speed_csv):
            with open(speed_csv, "r", encoding="utf-8-sig") as f:
                for s_row in csv.DictReader(f):
                    s_link = next((v for k, v in s_row.items() if k and k.lower() in ['config', 'link']), None)
                    s_speed = next((v for k, v in s_row.items() if k and 'speed' in k.lower()), '0')
                    s_delay = next((v for k, v in s_row.items() if k and ('delay' in k.lower() or 'real' in k.lower())), '0')
                    s_cc = next((v for k, v in s_row.items() if k and ('country' in k.lower() or 'cc' in k.lower())), 'UN')
                    
                    try:
                        if s_link and float(s_speed) > 0:
                            mbps = f"{float(s_speed)/1024:.1f}MB"
                            labeled = rename_config(s_link, {'cc': s_cc, 'ping': s_delay, 'speed': mbps})
                            if labeled: speed_ok.append(labeled)
                    except: continue

            with open(os.path.join(output_dir, "speed_passed.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(speed_ok) if speed_ok else "")
    
    logger.info("Process finished successfully.")

if __name__ == "__main__":
    test_process()
