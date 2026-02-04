import os
import requests
import time
import subprocess
import yaml
import json
import logging
import shutil
from urllib.parse import quote

# --- بارگذاری تنظیمات سیستمی از YAML ---
def load_yaml_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- بارگذاری تنظیمات کلاینت‌ها از JSON ---
def load_client_config(path):
    if not os.path.exists(path):
        logger.error(f"Client config JSON not found at {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# لود کردن تنظیمات در ابتدای برنامه
CONFIG = load_yaml_config()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Converter_Factory")

def run_subconverter():
    """مدیریت دانلود و اجرای سرویس ساب‌کانورتر"""
    sub_bin = CONFIG['paths']['subconverter_bin']
    if not os.path.exists(sub_bin):
        logger.info("Downloading Subconverter binary...")
        url = CONFIG['subconverter']['download_url']
        try:
            subprocess.run(["wget", url, "-O", "subconverter.tar.gz"], check=True)
            subprocess.run(["tar", "-xvf", "subconverter.tar.gz"], check=True)
            os.chmod(sub_bin, 0o755)
            if os.path.exists("subconverter.tar.gz"): os.remove("subconverter.tar.gz")
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            exit(1)
    
    proc = subprocess.Popen([sub_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Waiting {CONFIG['subconverter']['startup_delay']}s for service...")
    time.sleep(CONFIG['subconverter']['startup_delay'])
    return proc

def generate_subs():
    base_sub_dir = CONFIG['paths']['output_sub']
    base_output_dir = CONFIG['paths']['final_dir']
    base_api = CONFIG['subconverter']['api_url']
    special_folders = CONFIG['subconverter']['special_folders']
    
    # لود کردن تنظیمات کلاینت‌ها از فایل JSON معرفی شده در YAML
    client_configs = load_client_config(CONFIG['paths']['client_params_json'])

    if not client_configs:
        logger.warning("No client configurations found. Exiting.")
        return

    for root, dirs, files in os.walk(base_sub_dir):
        if base_output_dir in root or "final" in root: continue

        parent_folder = os.path.basename(root)
        is_special = parent_folder in special_folders

        for file in files:
            if not file.endswith("base64.txt"): continue
            if not is_special and "mixed" not in file: continue

            source_path = os.path.abspath(os.path.join(root, file))
            file_clean_name = file.replace(".txt", "").replace("_base64", "")
            
            dest_folder_name = f"{parent_folder}_{file_clean_name}" if is_special else parent_folder
            dest_dir = os.path.join(base_output_dir, dest_folder_name)
            os.makedirs(dest_dir, exist_ok=True)

            logger.info(f"🔄 Processing: {parent_folder}/{file}")

            for client_name, params in client_configs.items():
                # ساخت کپی از پارامترهای JSON کلاینت
                current_params = params.copy()
                target_filename = current_params.pop("filename", f"{client_name}.txt")
                current_params["url"] = source_path
                
                # تبدیل دیکشنری به Query String
                query = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in current_params.items() if v])
                final_url = f"{base_api}?{query}"

                try:
                    response = requests.get(final_url, timeout=CONFIG['subconverter']['request_timeout'])
                    if response.status_code == 200:
                        with open(os.path.join(dest_dir, target_filename), "w", encoding="utf-8") as f:
                            f.write(response.text)
                    else:
                        logger.error(f"  ❌ {client_name} failed (HTTP {response.status_code})")
                except Exception as e:
                    logger.error(f"  ❌ Error {client_name}: {e}")

if __name__ == "__main__":
    sub_proc = None
    try:
        sub_proc = run_subconverter()
        generate_subs()
    finally:
        if sub_proc:
            sub_proc.terminate()
            logger.info("Process finished and Subconverter closed.")
