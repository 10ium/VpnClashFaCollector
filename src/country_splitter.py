import base64
import csv
import logging
import os
import re
import shutil
from collections import defaultdict
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("CountrySplitter")

RAW_RESULTS_DIR = "sub/tested/raw_results"
FALLBACK_FILES = (
    "sub/tested/speed_passed.txt",
    "sub/tested/ping_passed.txt",
    "sub/all/mixed.txt",
)
OUTPUT_DIR = "sub/country"
MAX_DELAY_MS = 5000
MAX_CONFIGS_PER_COUNTRY_IN_MIX = 50

# اولویت کشورها طبق اطلاعات ارائه‌شده توسط کاربر:
# 1) کمترین پینگ معمول از ایران: ۱۰ کشور اصلی، سپس گزینه‌های خوب بعدی.
IRAN_PING_COUNTRY_PRIORITY = (
    "TR", "AE", "QA", "BH", "KW", "OM", "SA", "AM", "GE", "DE",
    "NL", "FR", "RO", "BG",
)

# 2) کمترین احتمال محدودیت/احراز هویت: اول کشورهایی که برای احراز سن گزینه‌های بهترند،
# سپس کشورهای با امتیاز آزادی اینترنت بالا برای پر کردن لیست در صورت نبود کانفیگ کافی.
OPEN_INTERNET_COUNTRY_PRIORITY = (
    "NL", "DE", "IS", "EE", "CA", "CH", "CZ", "AT", "ES", "PT",
    "TW", "JP", "FR", "AU", "CL", "CR", "AR", "ZA", "AM",
)

COUNTRY_TAG_RE = re.compile(r"(?:^|\|)\s*([A-Z]{2})\s*(?:\||$)")
DELAY_TAG_RE = re.compile(r"(\d{1,5})\s*ms", re.IGNORECASE)


def to_base64(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def normalize_country_code(value):
    value = str(value or "").strip().upper()
    if len(value) == 2 and value.isalpha() and value not in {"UN", "ZZ"}:
        return value
    return ""


def normalize_link(link):
    return str(link or "").strip()


def get_field(row, *names, default=""):
    normalized = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
    for name in names:
        value = normalized.get(name.lower())
        if value not in (None, ""):
            return value
    return default


def parse_delay(value, default=MAX_DELAY_MS + 1):
    try:
        delay = int(float(str(value).strip()))
        return delay if delay > 0 else default
    except (TypeError, ValueError):
        return default


def is_passed(row):
    status = str(get_field(row, "status")).strip().lower()
    return status in ("", "passed", "pass", "ok", "true")


def decode_text(value):
    try:
        return unquote(str(value or ""))
    except Exception:
        return str(value or "")


def flag_to_country(text):
    chars = list(text)
    for i in range(len(chars) - 1):
        first = ord(chars[i])
        second = ord(chars[i + 1])
        if 0x1F1E6 <= first <= 0x1F1FF and 0x1F1E6 <= second <= 0x1F1FF:
            return chr(first - 0x1F1E6 + ord("A")) + chr(second - 0x1F1E6 + ord("A"))
    return ""


def country_from_link(link):
    decoded = decode_text(link)
    match = COUNTRY_TAG_RE.search(decoded)
    if match:
        return normalize_country_code(match.group(1))
    return normalize_country_code(flag_to_country(decoded))


def delay_from_link(link):
    match = DELAY_TAG_RE.search(decode_text(link))
    if match:
        return parse_delay(match.group(1))
    return MAX_DELAY_MS + 1


def rows_from_csv(path):
    rows = []
    if not os.path.exists(path):
        return rows

    with open(path, "r", encoding="utf-8-sig", errors="ignore") as file_obj:
        for row in csv.DictReader(file_obj):
            link = normalize_link(get_field(row, "link", "Config"))
            country = normalize_country_code(get_field(row, "location", "country", "cc"))
            delay = parse_delay(get_field(row, "delay", "Delay"))
            if not link or not country or not is_passed(row) or delay > MAX_DELAY_MS:
                continue
            rows.append({"link": link, "country": country, "delay": delay})
    logger.info("Loaded %s country-tagged configs from %s", len(rows), path)
    return rows


def rows_from_plain_file(path):
    rows = []
    if not os.path.exists(path):
        return rows

    with open(path, "r", encoding="utf-8", errors="ignore") as file_obj:
        for line in file_obj:
            link = normalize_link(line)
            country = country_from_link(link)
            if not link or not country:
                continue
            rows.append({"link": link, "country": country, "delay": delay_from_link(link)})
    logger.info("Loaded %s country-tagged configs from %s", len(rows), path)
    return rows


def collect_rows():
    rows = []
    for filename in ("speed_raw.csv", "ping_raw.csv"):
        rows.extend(rows_from_csv(os.path.join(RAW_RESULTS_DIR, filename)))

    if rows:
        return rows

    for path in FALLBACK_FILES:
        rows.extend(rows_from_plain_file(path))
        if rows:
            break
    return rows


def group_by_country(rows):
    grouped = defaultdict(list)
    seen = set()

    for row in sorted(rows, key=lambda item: (item["country"], item["delay"], item["link"])):
        key = (row["country"], row["link"])
        if key in seen:
            continue
        seen.add(key)
        grouped[row["country"]].append(row)

    for country_rows in grouped.values():
        country_rows.sort(key=lambda item: (item["delay"], item["link"]))
    return dict(sorted(grouped.items()))


def write_subscription(path, rows):
    text = "\n".join(row["link"] for row in rows)
    with open(path, "w", encoding="utf-8") as file_obj:
        file_obj.write(text)
    with open(path.replace(".txt", "_base64.txt"), "w", encoding="utf-8") as file_obj:
        file_obj.write(to_base64(text))


def select_countries(grouped, priority):
    return [country for country in priority if country in grouped][:10]


def mixed_rows_for_countries(grouped, countries):
    mixed = []
    for country in countries:
        mixed.extend(grouped[country][:MAX_CONFIGS_PER_COUNTRY_IN_MIX])
    mixed.sort(key=lambda item: (item["delay"], item["country"], item["link"]))
    return mixed


def write_country_outputs(grouped):
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for country, rows in grouped.items():
        write_subscription(os.path.join(OUTPUT_DIR, f"{country}.txt"), rows)

    iran_ping_countries = select_countries(grouped, IRAN_PING_COUNTRY_PRIORITY)
    open_internet_countries = select_countries(grouped, OPEN_INTERNET_COUNTRY_PRIORITY)

    write_subscription(
        os.path.join(OUTPUT_DIR, "iran_ping_top10.txt"),
        mixed_rows_for_countries(grouped, iran_ping_countries),
    )
    write_subscription(
        os.path.join(OUTPUT_DIR, "open_internet_top10.txt"),
        mixed_rows_for_countries(grouped, open_internet_countries),
    )

    with open(os.path.join(OUTPUT_DIR, "README.md"), "w", encoding="utf-8") as file_obj:
        file_obj.write("Country subscriptions generated from tested xray-knife results.\n")
        file_obj.write("Iran ping priority: TR, AE, QA, BH, KW, OM, SA, AM, GE, DE; next: NL, FR, RO, BG.\n")
        file_obj.write("Open internet priority: NL, DE, IS, EE, CA, CH, CZ, AT, ES, PT; freedom fallback: TW, JP, FR, AU, CL, CR, AR, ZA, AM.\n")
        file_obj.write("If fewer than 10 priority countries exist in the tested pool, the mix contains only the available priority countries.\n")
        file_obj.write(f"Iran ping mix countries: {', '.join(iran_ping_countries)}\n")
        file_obj.write(f"Open internet mix countries: {', '.join(open_internet_countries)}\n")

    logger.info("Created %s country files in %s", len(grouped), OUTPUT_DIR)
    logger.info("Iran ping mix countries: %s", ", ".join(iran_ping_countries))
    logger.info("Open internet mix countries: %s", ", ".join(open_internet_countries))


def main():
    rows = collect_rows()
    grouped = group_by_country(rows)
    if not grouped:
        logger.warning("No country-tagged configs found; nothing to write.")
        return
    write_country_outputs(grouped)


if __name__ == "__main__":
    main()
