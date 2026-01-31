import os
import yaml
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageService, MessageMediaPoll

# ۱. بارگذاری تنظیمات از فایل YAML
def load_settings():
    if not os.path.exists('config/settings.yaml'):
        # مقادیر پیش‌فرض در صورت عدم وجود فایل
        return {'scraping': {'lookback_days': 7, 'max_messages_per_channel': 500}, 'storage': {'base_path': 'src/telegram'}}
    
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ۲. بارگذاری لیست کانال‌ها
def load_channels():
    if not os.path.exists('config/channels.txt'):
        print("خطا: فایل config/channels.txt یافت نشد.")
        return []
    with open('config/channels.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# ۳. تمیز کردن نام برای پوشه‌ها
def get_safe_name(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_')]).rstrip()

async def main():
    # بارگذاری کانفیگ‌ها
    settings = load_settings()
    channels = load_channels()
    
    # دریافت اطلاعات حساس از محیط (Environment Variables / GitHub Secrets)
    api_id = os.getenv('TG_API_ID')
    api_hash = os.getenv('TG_API_HASH')
    session_string = os.getenv('TG_SESSION_STRING')
    
    if not api_id or not api_hash or not session_string:
        print("خطا: متغیرهای محیطی TG_API_ID، TG_API_HASH یا TG_SESSION_STRING تنظیم نشده‌اند.")
        return

    lookback_days = settings['scraping'].get('lookback_days', 7)
    max_msgs = settings['scraping'].get('max_messages_per_channel', 500)
    base_path = settings['storage'].get('base_path', 'src/telegram')
    
    # تعیین بازه زمانی (پیام‌های چند روز گذشته)
    time_threshold = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    # مقداردهی کلاینت تلگرام (استفاده از StringSession برای GitHub Actions)
    client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("خطا: نشست (Session) معتبر نیست.")
            return

        for channel_url in channels:
            try:
                print(f"در حال پردازش: {channel_url}")
                entity = await client.get_entity(channel_url)
                channel_title = get_safe_name(entity.title)
                
                # ایجاد مسیر پوشه‌بندی برای هر کانال
                channel_dir = os.path.join(base_path, channel_title)
                os.makedirs(channel_dir, exist_ok=True)
                
                md_path = os.path.join(channel_dir, "messages.md")
                
                # خواندن پیام‌ها
                with open(md_path, "w", encoding="utf-8") as md_file:
                    md_file.write(f"# آرشیو متنی: {entity.title}\n")
                    md_file.write(f"بروزرسانی شده در: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
                    md_file.write("---\n\n")

                    # دریافت پیام‌ها (Telethon به صورت خودکار Entities را به Markdown تبدیل می‌کند)
                    async for message in client.iter_messages(entity, limit=max_msgs):
                        # بررسی بازه زمانی
                        if message.date < time_threshold:
                            break
                        
                        # نادیده گرفتن پیام‌های سیستمی و نظرسنجی‌ها
                        if isinstance(message, MessageService) or isinstance(message.media, MessageMediaPoll):
                            continue

                        timestamp = message.date.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # استخراج متن اصلی یا کپشن (شامل تمام استایل‌های Bold, Italic, Link و غیره)
                        # ویژگی message.text در Telethon محتوا را با حفظ Entities به فرمت Markdown برمی‌گرداند
                        content = message.text if message.text else ""

                        if content:
                            md_file.write(f"### 🕒 {timestamp}\n")
                            if message.forward:
                                md_file.write(f"> ↪️ **Forwarded Message**\n\n")
                            
                            md_file.write(f"{content}\n\n")
                            md_file.write("---\n\n")
                
                print(f"تکمیل شد: {entity.title}")

            except Exception as e:
                print(f"خطا در پردازش {channel_url}: {str(e)}")

    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
