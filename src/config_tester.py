import os, subprocess, logging, zipfile, requests, csv, base64, json, sys
from urllib.parse import quote, unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("ProxyLab")

def to_base64(text):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def get_flag(cc):
    cc = str(cc).upper()
    return "".join(chr(127397 + ord(c)) for c in cc) if len(cc) == 2 else "🌐"

def download_engine():
    if os.path.exists("xray-knife"): return
    url = "https://github.com/lilendian0x00/xray-knife/releases/latest/download/Xray-knife-linux-64.zip"
    r = requests.get(url, timeout=30)
    with open("engine.zip", "wb") as f: f.write(r.content)
    with zipfile.ZipFile("engine.zip", 'r') as z: z.extractall("dir")
    for root, _, files in os.walk("dir"):
        for file in files:
            if file == "xray-knife": os.rename(os.path.join(root, file), "xray-knife")
    os.chmod("xray-knife", 0o755)

def rename_config(link, info):
    try:
        cc = info.get('cc', 'UN')
        tag = f"{get_flag(cc)} {cc} | {info.get('ping', '?')}ms"
        if info.get('speed') and info.get('speed') != "LowSpeed":
            tag += f" | {info.get('speed')}"
        tag += " | "
        
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
    base_dir = "sub/tested"
    raw_dir = os.path.join(base_dir, "raw_results")
    os.makedirs(raw_dir, exist_ok=True)
    download_engine()

    # --- مرحله ۱: پینگ ---
    logger.info("Phase 1: Latency Test...")
    p_csv = os.path.join(raw_dir, "ping_raw.csv")
    # فعال کردن لاگ برای دیدن پیشرفت
    subprocess.run(["./xray-knife", "http", "-f", input_file, "-t", "100", "-o", p_csv, "-x", "csv"])

    top_300_links = []
    if os.path.exists(p_csv):
        with open(p_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = sorted([r for r in reader if r.get('delay') and int(r['delay']) > 0], key=lambda x: int(x['delay']))
            top_300_links = [r.get('link') or r.get('Config') for r in rows[:300]]
            
            # ذخیره نسخه پینگ‌شده (همه کانفیگ‌های سالم)
            ping_passed = [rename_config(r.get('link') or r.get('Config'), {'cc': r.get('location', 'UN'), 'ping': r.get('delay')}) for r in rows]
            p_text = "\n".join(filter(None, ping_passed))
            with open(os.path.join(base_dir, "ping_passed.txt"), "w", encoding="utf-8") as f: f.write(p_text)
            with open(os.path.join(base_dir, "ping_passed_base64.txt"), "w", encoding="utf-8") as f: f.write(to_base64(p_text))

    # --- مرحله ۲: سرعت ---
    if top_300_links:
        tmp_txt = "top300.txt"
        with open(tmp_txt, "w") as f: f.write("\n".join(filter(None, top_300_links)))
        
        logger.info("Phase 2: Speed Testing (Check raw_results for JSON/CSV)...")
        s_csv = os.path.join(raw_dir, "speed_raw.csv")
        s_json = os.path.join(raw_dir, "speed_raw.json")
        
        # تست سرعت با خروجی همزمان CSV و JSON و نمایش لاگ موتور
        subprocess.run(["./xray-knife", "http", "-f", tmp_txt, "-t", "10", "-o", s_csv, "-x", "csv", "-p", "-a", "10000"])
        subprocess.run(["./xray-knife", "http", "-f", tmp_txt, "-t", "10", "-o", s_json, "-x", "json", "-p", "-a", "10000"], stdout=subprocess.DEVNULL)

        speed_final = []
        if os.path.exists(s_csv):
            with open(s_csv, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    lnk = row.get('link') or row.get('Config')
                    # اصلاح اصلی: خواندن ستون download به جای speed
                    raw_speed = row.get('download') or row.get('speed') or "0"
                    dly = row.get('delay') or "0"
                    cc = row.get('location') or "UN"
                    
                    try:
                        spd_bytes = float(raw_speed)
                        if spd_bytes > 0:
                            # تبدیل بایت بر ثانیه به مگابایت بر ثانیه
                            mbps = f"{spd_bytes / (1024 * 1024):.2f}MB"
                            speed_final.append(rename_config(lnk, {'cc': cc, 'ping': dly, 'speed': mbps}))
                        else:
                            speed_final.append(rename_config(lnk, {'cc': cc, 'ping': dly, 'speed': "LowSpeed"}))
                    except:
                        speed_final.append(rename_config(lnk, {'cc': cc, 'ping': dly}))

        s_text = "\n".join(filter(None, speed_final))
        with open(os.path.join(base_dir, "speed_passed.txt"), "w", encoding="utf-8") as f: f.write(s_text)
        with open(os.path.join(base_dir, "speed_passed_base64.txt"), "w", encoding="utf-8") as f: f.write(to_base64(s_text))

    logger.info("Process Finished. Results saved in sub/tested/")

if __name__ == "__main__":
    test_process()
