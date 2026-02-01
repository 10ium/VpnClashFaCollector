import os
import requests
import time
import subprocess
import json
import logging
from urllib.parse import quote

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SubGenerator_Pro")

def run_subconverter():
    """دانلود و اجرای ساب‌کانورتر در پس‌زمینه"""
    if not os.path.exists("subconverter/subconverter"):
        logger.info("Downloading Subconverter binary...")
        url = "https://github.com/MetaCubeX/subconverter/releases/latest/download/subconverter_linux64.tar.gz"
        subprocess.run(["wget", url, "-O", "subconverter.tar.gz"], check=True)
        subprocess.run(["tar", "-xvf", "subconverter.tar.gz"], check=True)
        os.chmod("subconverter/subconverter", 0o755)
    
    # اجرای سرویس روی پورت 25500
    proc = subprocess.Popen(
        ["./subconverter/subconverter"], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    time.sleep(5) # زمان کافی برای لود شدن کامل دیتابیس‌ها و تمپلیت‌ها
    return proc

def generate_all_subs():
    # ۱. آدرس‌دهی فایل‌ها
    # استفاده از abspath برای جلوگیری از خطای 414 و "Link Not Found" در ساب‌کانورتر
    source_file = os.path.abspath("sub/tested/speed_passed_base64.txt")
    config_path = "config/sub_params.json"
    output_dir = "sub/final"
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(source_file):
        logger.error(f"فایل منبع لینک‌ها یافت نشد: {source_file}")
        return

    # ۲. خواندن تنظیمات کلاینت‌ها
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            client_configs = json.load(f)
    except Exception as e:
        logger.error(f"خطا در خواندن فایل تنظیمات JSON: {e}")
        return

    base_api = "http://127.0.0.1:25500/sub"

    for client_name, params in client_configs.items():
        logger.info(f"Generating for: {client_name}")
        
        # جدا کردن پارامترهای سیستمی از پارامترهای API
        target_filename = params.pop("filename", f"{client_name}.txt")
        
        # کپی پارامترها برای ساخت Query
        api_params = params.copy()
        
        # تکنیک اصلی: بجای ارسال 1000 خط لینک، آدرس فایل محلی را به API می‌دهیم
        # ساب‌کانورتر اجازه دارد فایل‌های محلی را اگر با مسیر مستقیم باشند بخواند
        api_params["url"] = source_file
        
        # ساخت Query String
        query_parts = []
        for key, value in api_params.items():
            if value is not None and value != "":
                # انکود کردن مقادیر (مخصوصاً لینک‌های تمپلیت در پارامتر config)
                encoded_val = quote(str(value), safe="")
                query_parts.append(f"{key}={encoded_val}")
        
        final_url = f"{base_api}?{'&'.join(query_parts)}"

        try:
            # ارسال درخواست GET (حالا طول URL به دلیل استفاده از مسیر فایل بسیار کوتاه است)
            response = requests.get(final_url, timeout=120)
            
            if response.status_code == 200:
                output_path = os.path.join(output_dir, target_filename)
                with open(output_path, "w", encoding="utf-8") as out:
                    out.write(response.text)
                logger.info(f"✅ Successfully created {target_filename}")
            else:
                logger.error(f"❌ Failed {client_name}: HTTP {response.status_code}")
                # اگر ساب‌کانورتر خطای داخلی بدهد، معمولاً در بدنه پاسخ دلیلش را می‌نویسد
                if response.text:
                    logger.debug(f"API Response Error: {response.text}")
                    
        except Exception as e:
            logger.error(f"Request error for {client_name}: {e}")

if __name__ == "__main__":
    sub_proc = None
    try:
        sub_proc = run_subconverter()
        generate_all_subs()
    except Exception as e:
        logger.error(f"Global error: {e}")
    finally:
        if sub_proc:
            logger.info("Shutting down Subconverter...")
            sub_proc.terminate()
            sub_proc.wait()
