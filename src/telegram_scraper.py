import os
import yaml
import requests
import logging
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

# --- تنظیمات لاگر ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("TelegramScraper")

# --- بارگذاری تنظیمات مرکزی ---
def load_central_config(path='config.yaml'):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"خطا در بارگذاری config.yaml: {e}")
        return {}

def load_channels(file_path):
    """خواندن لیست یوزرنیم کانال‌ها از فایل متنی"""
    if not os.path.exists(file_path):
        logger.error(f"فایل لیست کانال‌ها یافت نشد: {file_path}")
        return []
    usernames = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # استخراج یوزرنیم از لینک یا متن ساده
                username = line.split('/')[-1].replace('@', '').split('?')[0]
                usernames.append(username)
    return usernames

def html_to_md(element):
    """تبدیل المان‌های HTML تلگرام به Markdown ساده"""
    if not element: return ""
    try:
        for b in element.find_all('b'): b.replace_with(f"**{b.get_text()}**")
        for i in element.find_all('i'): i.replace_with(f"*{i.get_text()}*")
        for code in element.find_all('code'): code.replace_with(f"`{code.get_text()}`")
        for a in element.find_all('a'):
            href = a.get('href', '')
            a.replace_with(f"[{a.get_text()}]({href})")
        return element.get_text(separator='\n').strip()
    except Exception:
        return element.get_text().strip()

def scrape_channel(username, config, current_idx, total_channels):
    """اسکرپ کردن یک کانال خاص"""
    scraping_cfg = config.get('scraping', {})
    lookback_days = scraping_cfg.get('lookback_days', 2)
    max_pages = scraping_cfg.get('max_pages', 30)
    base_path = config.get('paths', {}).get('telegram_src', 'src/telegram')
    
    logger.info(f"[{current_idx}/{total_channels}] پردازش: @{username}")
    
    channel_dir = os.path.join(base_path, username)
    os.makedirs(channel_dir, exist_ok=True)
    
    time_threshold = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    all_messages = []
    last_msg_id = None
    reached_end = False
    pages_fetched = 0
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    while not reached_end and pages_fetched < max_pages:
        url = f"https://t.me/s/{username}"
        if last_msg_id: url += f"?before={last_msg_id}"
        
        try:
            pages_fetched += 1
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 429:
                delay = scraping_cfg.get('rate_limit_delay', 5)
                logger.warning(f"Rate Limit! انتظار برای {delay} ثانیه...")
                time.sleep(delay)
                pages_fetched -= 1
                continue
            elif response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, 'lxml')
            messages = soup.find_all('div', class_='tgme_widget_message')
            
            if not messages: break

            for msg in reversed(messages):
                msg_id_attr = msg.get('data-post')
                if msg_id_attr: last_msg_id = msg_id_attr.split('/')[-1]

                time_element = msg.find('time', class_='time')
                if not time_element: continue
                
                msg_date = datetime.fromisoformat(time_element.get('datetime').replace('Z', '+00:00'))
                
                if msg_date < time_threshold:
                    reached_end = True
                    break
                
                text_area = msg.find('div', class_='tgme_widget_message_text')
                content = html_to_md(text_area) if text_area else ""
                
                if content:
                    is_fwd = msg.find('div', class_='tgme_widget_message_forwarded_from')
                    all_messages.append({
                        'date': msg_date,
                        'content': content,
                        'forwarded': is_fwd is not None
                    })
            
            if not reached_end:
                time.sleep(scraping_cfg.get('page_delay', 1.5))

        except Exception as e:
            logger.error(f"خطا در صفحه: {e}")
            break

    if all_messages:
        # ذخیره در فایل Markdown
        output_file = os.path.join(channel_dir, "messages.md")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# @{username}\n\n")
                for m in all_messages:
                    f.write(f"### {m['date'].strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
                    if m['forwarded']: f.write(f"> Forwarded\n\n")
                    f.write(f"{m['content']}\n\n---\n\n")
            logger.info(f"✅ {len(all_messages)} پیام ذخیره شد.")
        except Exception as e:
            logger.error(f"خطا در ذخیره فایل: {e}")

def main():
    start_time = time.time()
    config = load_central_config()
    
    channels_path = config.get('paths', {}).get('channels_list', 'config/channels.txt')
    usernames = load_channels(channels_path)
    
    if not usernames:
        logger.error("لیست کانال‌ها خالی است.")
        return

    total = len(usernames)
    for idx, username in enumerate(usernames, 1):
        scrape_channel(username, config, idx, total)
        if idx < total:
            time.sleep(config.get('scraping', {}).get('channel_delay', 3))

    logger.info(f"🏁 پایان عملیات در {round(time.time() - start_time, 2)} ثانیه.")

if __name__ == "__main__":
    main()
