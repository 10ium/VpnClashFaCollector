import os, subprocess, logging, zipfile, requests, csv, base64, json, sys, re
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

def rename_config(link, info, rank=None):
    try:
        cc = info.get('cc', 'UN')
        ping = info.get('ping', '?')
        speed = info.get('speed')
        
        # ساخت تگ مشخصات
        tag_parts = [get_flag(cc), cc, f"{ping}ms"]
        if speed and "Low" not in str(speed):
            tag_parts.append(speed)
        
        # اضافه کردن رتبه عددی در صورت وجود
        prefix = f"[{rank}] " if rank else ""
        tag = prefix + " | ".join(tag_parts) + " | "
        
        if link.startswith("vmess://"):
            data = json.loads(base64.b64decode(link[8:]).decode('utf-8'))
            data['ps'] = tag + data.get('ps', 'Server')
            return "vmess://" + base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
        elif "#" in link:
            base, remark = link.split("#", 1)
            # استفاده از unquote برای حفظ اسم اصلی و سپس کوت کردن مجدد کل نام جدید
            return f"{base}#{quote(tag + unquote(remark))}"
        return f"{link}#{quote(tag + 'Server')}"
    except: return link

def test_process():
    input_file = "sub/all/mixed.txt"
    base_dir = "sub/tested"
    raw_dir = os.path.join(base_dir, "raw_results")
    os.makedirs(raw_dir, exist_ok=True)
    download_engine()

    # --- فاز ۱: پینگ ---
    logger.info("--- Phase 1: Latency Test ---")
    p_csv = os.path.join(raw_dir, "ping_raw.csv")
    subprocess.run(["./xray-knife", "http", "-f", input_file, "-t", "100", "-o", p_csv, "-x", "csv"], stdout=subprocess.DEVNULL)

    top_candidates = []
    if os.path.exists(p_csv):
        with open(p_csv, "r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            valid_rows = [r for r in reader if r.get('delay') and str(r['delay']).isdigit() and int(r['delay']) > 0]
            valid_rows.sort(key=lambda x: int(x['delay']))
            
            # ذخیره نتایج پینگ (مرتب شده بر اساس تاخیر)
            ping_passed = [rename_config(r.get('link') or r.get('Config'), {'cc': r.get('location', 'UN'), 'ping': r.get('delay')}) for r in valid_rows]
            with open(os.path.join(base_dir, "ping_passed.txt"), "w", encoding="utf-8") as f: f.write("\n".join(filter(None, ping_passed)))
            
            top_candidates = [r.get('link') or r.get('Config') for r in valid_rows[:400]]

    # --- فاز ۲: تست سرعت واقعی ---
    if top_candidates:
        tmp_txt = "top400_tmp.txt"
        with open(tmp_txt, "w") as f: f.write("\n".join(filter(None, top_candidates)))
        
        logger.info("--- Phase 2: Speed Test & Ranking (Top 400) ---")
        s_csv = os.path.join(raw_dir, "speed_raw.csv")
        speed_url = "https://speed.cloudflare.com/__down?bytes=5000000"
        
        subprocess.run(["./xray-knife", "http", "-f", tmp_txt, "-t", "5", "-o", s_csv, "-x", "csv", "-p", "-u", speed_url, "-a", "5000"], stdout=subprocess.DEVNULL)

        speed_results = []
        if os.path.exists(s_csv):
            with open(s_csv, "r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    raw_down = float(row.get('download') or 0)
                    speed_results.append({
                        'link': row.get('link') or row.get('Config'),
                        'speed_val': raw_down,
                        'delay': row.get('delay') or "0",
                        'cc': row.get('location') or "UN"
                    })
            
            # مرتب‌سازی بر اساس سرعت (نزولی - بیشترین اول)
            speed_results.sort(key=lambda x: x['speed_val'], reverse=True)

            final_list = []
            for i, res in enumerate(speed_results, 1):
                spd = res['speed_val']
                if spd >= 1024:
                    f_speed = f"{spd / 1024:.1f}MB"
                elif spd > 0:
                    f_speed = f"{int(spd)}KB"
                else:
                    f_speed = "LowSpeed"
                
                # فراخوانی تابع تغییر نام با رتبه (i)
                final_list.append(rename_config(res['link'], {'cc': res['cc'], 'ping': res['delay'], 'speed': f_speed}, rank=i))

            s_text = "\n".join(filter(None, final_list))
            with open(os.path.join(base_dir, "speed_passed.txt"), "w", encoding="utf-8") as f: f.write(s_text)
            with open(os.path.join(base_dir, "speed_passed_base64.txt"), "w", encoding="utf-8") as f: f.write(to_base64(s_text))

    if os.path.exists(tmp_txt): os.remove(tmp_txt)
    logger.info("Process complete. Speed sorted and ranked.")

if __name__ == "__main__":
    test_process()
