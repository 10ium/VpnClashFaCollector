import os, subprocess, logging, zipfile, requests, csv, base64, json, sys, re
from urllib.parse import quote, unquote

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("ProxyLab")

XRAY_KNIFE = "./xray-knife"
INPUT_FILE = "sub/all/mixed.txt"
BASE_DIR = "sub/tested"
RAW_DIR = os.path.join(BASE_DIR, "raw_results")
PING_THREADS = "100"
SPEED_THREADS = "2"
MAX_DELAY_MS = 5000
TOP_CANDIDATES_LIMIT = 300
SPEED_TEST_AMOUNT_KB = 5000
HTTP_TEST_URL = "https://cloudflare.com/cdn-cgi/trace"


def to_base64(text):
    """تبدیل متن به فرمت بیس۶۴"""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def get_flag(cc):
    """تبدیل کد کشور به ایموجی پرچم"""
    cc = str(cc).upper()
    return "".join(chr(127397 + ord(c)) for c in cc) if len(cc) == 2 else "🌐"

def download_engine():
    """دانلود موتور ایکس‌ری نایف در صورت عدم وجود"""
    if os.path.exists("xray-knife"): return
    url = "https://github.com/lilendian0x00/xray-knife/releases/latest/download/Xray-knife-linux-64.zip"
    try:
        r = requests.get(url, timeout=30)
        with open("engine.zip", "wb") as f: f.write(r.content)
        with zipfile.ZipFile("engine.zip", 'r') as z: z.extractall("dir")
        for root, _, files in os.walk("dir"):
            for file in files:
                if file == "xray-knife": os.rename(os.path.join(root, file), "xray-knife")
        os.chmod("xray-knife", 0o755)
        if os.path.exists("engine.zip"): os.remove("engine.zip")
        if os.path.exists("dir"): subprocess.run(["rm", "-rf", "dir"])
    except Exception as e:
        logger.error(f"Failed to download engine: {e}")

def rename_config(link, info, rank=None):
    """تغییر نام و برچسب‌گذاری کانفیگ بر اساس نتایج تست"""
    try:
        cc = info.get('cc', 'UN')
        ping = info.get('ping', '?')
        speed = info.get('speed')

        tag_parts = [get_flag(cc), cc, f"{ping}ms"]
        if speed and "Low" not in str(speed):
            tag_parts.append(speed)

        prefix = f"[{rank}] " if rank else ""
        tag = prefix + " | ".join(tag_parts) + " | "

        if link.startswith("vmess://"):
            data = json.loads(base64.b64decode(link[8:]).decode('utf-8'))
            data['ps'] = tag + data.get('ps', 'Server')
            return "vmess://" + base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
        elif "#" in link:
            base, remark = link.split("#", 1)
            return f"{base}#{quote(tag + unquote(remark))}"
        return f"{link}#{quote(tag + 'Server')}"
    except: return link


def supported_http_flags():
    """پرچم‌های پشتیبانی‌شده توسط نسخه نصب‌شده xray-knife را برمی‌گرداند."""
    try:
        result = subprocess.run([XRAY_KNIFE, "help", "http"], capture_output=True, text=True, check=False)
        return result.stdout + result.stderr
    except Exception:
        return ""


def append_if_supported(command, help_text, flag, value=None):
    """برای سازگاری با نسخه‌های قدیمی xray-knife فقط فلگ‌های موجود در help را اضافه می‌کند."""
    if flag not in help_text:
        return
    command.append(flag)
    if value is not None:
        command.append(str(value))


def run_xray_http(output_file, extra_args):
    """اجرای xray-knife http با حذف خروجی قبلی تا نتیجه کهنه دوباره خوانده نشود."""
    if os.path.exists(output_file):
        os.remove(output_file)

    command = [XRAY_KNIFE, "http", *extra_args]
    logger.info("Running: %s", " ".join(command))
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.error("xray-knife failed with exit code %s", result.returncode)
        if result.stderr:
            logger.error(result.stderr.strip())
        return False

    if not os.path.exists(output_file):
        logger.error("xray-knife did not create expected output file: %s", output_file)
        return False

    return True


def field(row, *names, default=""):
    """خواندن ستون CSV با پشتیبانی از نام‌های کوچک/بزرگ و نسخه‌های متفاوت ابزار."""
    normalized = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    for name in names:
        value = normalized.get(name.lower())
        if value not in (None, ""):
            return value
    return default


def parse_positive_int(value, default=0):
    try:
        parsed = int(float(str(value).strip()))
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def parse_non_negative_float(value, default=0.0):
    try:
        parsed = float(str(value).strip())
        return parsed if parsed >= 0 else default
    except (TypeError, ValueError):
        return default


def is_passed(row):
    status = str(field(row, "status")).strip().lower()
    return status in ("", "passed", "pass", "ok", "true")


def read_passed_rows(csv_file, require_download=False):
    """فقط ردیف‌هایی را نگه می‌دارد که واقعاً توسط xray-knife پاس شده‌اند."""
    passed_rows = []
    with open(csv_file, "r", encoding="utf-8-sig", errors="ignore") as f:
        for row in csv.DictReader(f):
            delay = parse_positive_int(field(row, "delay", "Delay"))
            download = parse_non_negative_float(field(row, "download", "Download"))
            link = field(row, "link", "Config")

            if not link or not is_passed(row) or not (0 < delay <= MAX_DELAY_MS):
                continue
            if require_download and download <= 0:
                continue

            passed_rows.append({
                "link": link,
                "delay": delay,
                "download": download,
                "cc": field(row, "location", "country", "cc", default="UN") or "UN",
            })
    return passed_rows


def test_process():
    os.makedirs(RAW_DIR, exist_ok=True)
    download_engine()

    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file {INPUT_FILE} not found!")
        return

    help_text = supported_http_flags()

    # --- Phase 1: Latency Test ---
    logger.info("--- Phase 1: Latency Test (Threads: %s) ---", PING_THREADS)
    p_csv = os.path.join(RAW_DIR, "ping_raw.csv")
    ping_args = ["-f", INPUT_FILE, "-t", PING_THREADS, "-o", p_csv, "-x", "csv", "-d", str(MAX_DELAY_MS), "-u", HTTP_TEST_URL]
    append_if_supported(ping_args, help_text, "--timeout", MAX_DELAY_MS)
    append_if_supported(ping_args, help_text, "--retries", 1)

    top_candidates = []
    if run_xray_http(p_csv, ping_args):
        valid_rows = read_passed_rows(p_csv)
        valid_rows.sort(key=lambda x: x["delay"])

        ping_passed_list = [rename_config(r['link'], {'cc': r['cc'], 'ping': r['delay']}) for r in valid_rows]
        ping_passed_text = "\n".join(filter(None, ping_passed_list))

        with open(os.path.join(BASE_DIR, "ping_passed.txt"), "w", encoding="utf-8") as f:
            f.write(ping_passed_text)

        with open(os.path.join(BASE_DIR, "ping_passed_base64.txt"), "w", encoding="utf-8") as f:
            f.write(to_base64(ping_passed_text))

        logger.info(f"Ping test complete. {len(valid_rows)} configs passed.")
        top_candidates = [r['link'] for r in valid_rows[:TOP_CANDIDATES_LIMIT]]

    # --- Phase 2: Speed Test ---
    if top_candidates:
        tmp_txt = "top_candidates_tmp.txt"
        with open(tmp_txt, "w", encoding="utf-8") as f: f.write("\n".join(filter(None, top_candidates)))

        logger.info("--- Phase 2: Speed Test (%sKB - Threads: %s) ---", SPEED_TEST_AMOUNT_KB, SPEED_THREADS)
        s_csv = os.path.join(RAW_DIR, "speed_raw.csv")
        speed_args = ["-f", tmp_txt, "-t", SPEED_THREADS, "-o", s_csv, "-x", "csv", "-p", "-a", str(SPEED_TEST_AMOUNT_KB), "-d", str(MAX_DELAY_MS)]
        append_if_supported(speed_args, help_text, "--timeout", MAX_DELAY_MS)
        append_if_supported(speed_args, help_text, "--retries", 1)

        speed_results = []
        if run_xray_http(s_csv, speed_args):
            speed_results = read_passed_rows(s_csv, require_download=True)
            speed_results.sort(key=lambda x: x['download'], reverse=True)

            final_list = []
            for i, res in enumerate(speed_results, 1):
                spd = res['download']
                if spd >= 1024:
                    f_speed = f"{spd / 1024:.1f}MB"
                elif spd > 0:
                    f_speed = f"{int(spd)}KB"
                else:
                    f_speed = "Low"

                final_list.append(rename_config(res['link'], {'cc': res['cc'], 'ping': res['delay'], 'speed': f_speed}, rank=i))

            s_text = "\n".join(filter(None, final_list))
            with open(os.path.join(BASE_DIR, "speed_passed.txt"), "w", encoding="utf-8") as f: f.write(s_text)
            with open(os.path.join(BASE_DIR, "speed_passed_base64.txt"), "w", encoding="utf-8") as f: f.write(to_base64(s_text))

            logger.info(f"Speed test complete. {len(speed_results)} configs ranked.")

    if os.path.exists("top_candidates_tmp.txt"): os.remove("top_candidates_tmp.txt")
    logger.info("All tests finished successfully.")

if __name__ == "__main__":
    test_process()
