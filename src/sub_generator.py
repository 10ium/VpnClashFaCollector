import os
import requests
import time
import subprocess
import json
import logging
from urllib.parse import quote, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MultiSource_Generator")

def run_subconverter():
    if not os.path.exists("subconverter/subconverter"):
        logger.info("Downloading Subconverter...")
        url = "https://github.com/MetaCubeX/subconverter/releases/latest/download/subconverter_linux64.tar.gz"
        subprocess.run(["wget", url, "-O", "subconverter.tar.gz"], check=True)
        subprocess.run(["tar", "-xvf", "subconverter.tar.gz"], check=True)
        os.chmod("subconverter/subconverter", 0o755)
    
    proc = subprocess.Popen(["./subconverter/subconverter"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    return proc

def generate_subs():
    # ۱. لیست منابع ورودی (لینک‌های مستقیم گیت‌هاب شما)
    source_urls = [
        "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/refs/heads/main/sub/tested/speed_passed_base64.txt",
        "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/refs/heads/main/sub/tested/ping_passed_base64.txt",
        "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/refs/heads/main/sub/all/hysteria2_base64.txt",
        "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/refs/heads/main/sub/all/mixed_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/all/ss_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/all/ssh_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/all/trojan_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/all/vless_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/all/vmess_base64.txt",
        "https://github.com/10ium/VpnClashFaCollector/raw/refs/heads/main/sub/AR14N24B/mixed_base64.txt"
    ]

    config_path = "config/sub_params.json"
    base_output_dir = "sub/final"
    base_api = "http://127.0.0.1:25500/sub"

    # خواندن تنظیمات کلاینت‌ها (Clash, V2Ray, ...)
    with open(config_path, "r", encoding="utf-8") as f:
        client_configs = json.load(f)

    for source_url in source_urls:
        # استخراج نام پوشه از روی نام فایل (مثلاً speed_passed_base64)
        source_name = os.path.basename(urlparse(source_url).path).replace(".txt", "")
        
        # برای لینک آخر که نام تکراری دارد (mixed_base64 در پوشه متفاوت)، 
        # اگر لازم است تفکیک شود، نام پوشه والد را هم اضافه می‌کنیم:
        if "AR14N24B" in source_url:
            source_name = f"AR14N24B_{source_name}"
            
        current_dest_dir = os.path.join(base_output_dir, source_name)
        os.makedirs(current_dest_dir, exist_ok=True)
        
        logger.info(f"--- Processing Source: {source_name} ---")

        for client_name, params in client_configs.items():
            # کپی کردن پارامترها برای هر کلاینت
            current_params = params.copy()
            target_filename = current_params.pop("filename", f"{client_name}.txt")
            
            # تنظیم URL منبع (در اینجا ساب‌کانورتر خودش لینک گیت‌هاب را دانلود می‌کند)
            current_params["url"] = source_url
            
            # ساخت Query String
            query_string = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in current_params.items() if v != ""])
            final_url = f"{base_api}?{query_string}"

            try:
                response = requests.get(final_url, timeout=120)
                if response.status_code == 200:
                    output_file = os.path.join(current_dest_dir, target_filename)
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    logger.info(f"  [OK] {client_name} -> {source_name}/{target_filename}")
                else:
                    logger.error(f"  [Failed] {client_name} for {source_name}: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"  [Error] {client_name} for {source_name}: {e}")

if __name__ == "__main__":
    sub_proc = None
    try:
        sub_proc = run_subconverter()
        generate_subs()
    finally:
        if sub_proc:
            sub_proc.terminate()
            logger.info("Subconverter stopped.")
