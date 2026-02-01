import os
import requests
import time
import subprocess
import json
import logging
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Smart_Filter_Generator")

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

def generate_smart_subs():
    base_sub_dir = "sub"
    base_output_dir = "sub/final"
    config_path = "config/sub_params.json"
    base_api = "http://127.0.0.1:25500/sub"

    with open(config_path, "r", encoding="utf-8") as f:
        client_configs = json.load(f)

    for root, dirs, files in os.walk(base_sub_dir):
        if "final" in root: continue

        for file in files:
            if file.endswith("base64.txt"):
                source_path = os.path.abspath(os.path.join(root, file))
                parent_folder = os.path.basename(root)
                file_name = file.replace(".txt", "")

                # تعیین نام پوشه مقصد
                dest_folder_name = parent_folder if "mixed" in file else f"{parent_folder}_{file_name}"
                dest_dir = os.path.join(base_output_dir, dest_folder_name)
                os.makedirs(dest_dir, exist_ok=True)

                # --- منطق فیلترینگ شما ---
                # اگر فایل در پوشه all یا tested باشد -> همه کلاینت‌ها (12 تا)
                # در غیر این صورت -> فقط کلاینت‌هایی که نامشان شامل mixed یا v2ray یا clash است (بسته به نیاز شما)
                # طبق درخواست شما: برای بقیه فقط "میکس" ساخته شود. 
                
                is_full_scan = (parent_folder in ["all", "tested"])
                
                logger.info(f"📂 Processing: {source_path} (Full Scan: {is_full_scan})")

                for client_name, params in client_configs.items():
                    # اگر فول اسکن نباشد، فقط کلاینت‌های اصلی (مثلاً v2ray و clash یا هرچی که مد نظرت هست) را بساز
                    # اینجا من طبق گفته شما فقط 'v2ray' یا 'clash' رو به عنوان نماینده میکس در نظر می‌گیرم
                    # یا می‌توانید یک کلاینت خاص به نام mixed در json داشته باشید
                    if not is_full_scan and client_name not in ["v2ray", "clash"]:
                        continue

                    current_params = params.copy()
                    target_filename = current_params.pop("filename", f"{client_name}.txt")
                    current_params["url"] = source_path
                    
                    query = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in current_params.items() if v])
                    final_url = f"{base_api}?{query}"

                    try:
                        response = requests.get(final_url, timeout=60)
                        if response.status_code == 200:
                            with open(os.path.join(dest_dir, target_filename), "w", encoding="utf-8") as f:
                                f.write(response.text)
                    except Exception as e:
                        logger.error(f"  ❌ Error {client_name}: {e}")

if __name__ == "__main__":
    sub_proc = None
    try:
        sub_proc = run_subconverter()
        generate_smart_subs()
    finally:
        if sub_proc:
            sub_proc.terminate()
            logger.info("Done.")
