import os
import requests
import time
import subprocess
import json
import logging
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Split_Converter")

def run_subconverter():
    if not os.path.exists("subconverter/subconverter"):
        logger.info("Downloading Subconverter binary...")
        url = "https://github.com/MetaCubeX/subconverter/releases/latest/download/subconverter_linux64.tar.gz"
        subprocess.run(["wget", url, "-O", "subconverter.tar.gz"], check=True)
        subprocess.run(["tar", "-xvf", "subconverter.tar.gz"], check=True)
        os.chmod("subconverter/subconverter", 0o755)
    
    proc = subprocess.Popen(["./subconverter/subconverter"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    return proc

def generate_subs():
    base_sub_dir = "sub"
    base_output_dir = "sub/final"
    split_base_dir = "sub/split/base64"
    config_path = "config/sub_params.json"
    base_api = "http://127.0.0.1:25500/sub"

    # پارامترهای اختصاصی شما فقط برای بخش Split Clash
    split_clash_params = {
        "target": "clash",
        "config": "https://raw.githubusercontent.com/10ium/clash_rules/refs/heads/main/ACL4SSR/vpnclashfa.ini",
        "fdn": "true",
        "list": "false",
        "udp": "true",
        "tfo": "false",
        "emoji": "true",
        "scv": "false",
        "sort": "false",
        "append_type": "false",
        "rename": "",
        "new_name": "true",
        "tls13": "false",
        "classic": "false",
        "expand": "true"
    }

    # لود کردن تنظیمات برای بخش‌های دیگر (Special Folders & Mixed)
    with open(config_path, "r", encoding="utf-8") as f:
        client_configs = json.load(f)

    # --- بخش 1: پردازش استاندارد (بدون تغییر، از فایل JSON استفاده می‌کند) ---
    logger.info("--- Starting Standard Processing (from JSON) ---")
    for root, dirs, files in os.walk(base_sub_dir):
        if "final" in root or "split" in root: continue

        parent_folder = os.path.basename(root)
        is_special_folder = parent_folder in ["tested", "all"]

        for file in files:
            if not file.endswith("base64.txt"): continue
            if not is_special_folder and "mixed" not in file: continue

            source_path = os.path.abspath(os.path.join(root, file))
            file_clean_name = file.replace(".txt", "").replace("_base64", "")
            dest_folder_name = f"{parent_folder}_{file_clean_name}" if is_special_folder else parent_folder
            dest_dir = os.path.join(base_output_dir, dest_folder_name)
            os.makedirs(dest_dir, exist_ok=True)

            # استفاده از پارامترهای فایل JSON
            for client_name, params in client_configs.items():
                p = params.copy()
                fname = p.pop("filename", f"{client_name}.txt")
                p["url"] = source_path
                query = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in p.items() if v])
                
                try:
                    res = requests.get(f"{base_api}?{query}", timeout=60)
                    if res.status_code == 200:
                        with open(os.path.join(dest_dir, fname), "w", encoding="utf-8") as f:
                            f.write(res.text)
                except Exception as e:
                    logger.error(f"Error {client_name}: {e}")

    # --- بخش 2: پردازش اختصاصی Split (فقط برای کلش و در مسیر درخواستی) ---
    if os.path.exists(split_base_dir):
        logger.info("--- Starting Split Clash Processing (Custom Rules) ---")
        for root, dirs, files in os.walk(split_base_dir):
            collection_name = os.path.basename(root)
            if collection_name == "base64": continue

            for file in files: # file همان شماره بخش است (1, 2, 3...)
                source_path = os.path.abspath(os.path.join(root, file))
                
                # مسیر خروجی دقیق: sub/split/clash/name/1
                dest_dir = os.path.join("sub/split/clash", collection_name)
                os.makedirs(dest_dir, exist_ok=True)
                target_path = os.path.join(dest_dir, file)

                # استفاده از پارامترهای دستی که بالا تعریف کردیم
                payload = split_clash_params.copy()
                payload["url"] = source_path
                
                query = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in payload.items() if v])
                
                try:
                    res = requests.get(f"{base_api}?{query}", timeout=60)
                    if res.status_code == 200:
                        with open(target_path, "w", encoding="utf-8") as f_out:
                            f_out.write(res.text)
                        logger.info(f"✅ Split Clash Created: {target_path}")
                except Exception as e:
                    logger.error(f"❌ Error in Split Clash {collection_name}/{file}: {e}")

if __name__ == "__main__":
    sub_proc = None
    try:
        sub_proc = run_subconverter()
        generate_subs()
    finally:
        if sub_proc:
            sub_proc.terminate()
            logger.info("Generation finished.")
