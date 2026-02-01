import os
import datetime

def generate_web_page():
    sub_root = "sub"
    final_root = "sub/final"
    output_html = "index.html"
    repo_raw_url = "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main"
    
    client_icons = {
        "clash": "fa-circle-nodes", "v2ray": "fa-share-nodes", "ss": "fa-key",
        "surfboard": "fa-wind", "surge": "fa-bolt", "quan": "fa-gear", 
        "base64": "fa-code", "txt": "fa-file-lines", "yaml": "fa-file-code"
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VpnClashFa Panel</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700;900&display=swap');
            body {{ font-family: 'Vazirmatn', sans-serif; background: #0f172a; color: #f1f5f9; font-size: 18px; }}
            .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
            .accordion-content {{ max-height: 0; overflow: hidden; transition: max-height 0.6s ease; }}
            .open .accordion-content {{ max-height: 5000px; }}
            .proxy-box {{ font-family: monospace; background: #000; padding: 20px; border-radius: 15px; height: 280px; overflow-y: auto; direction: ltr; text-align: left; font-size: 15px; border: 1px solid #334155; }}
            .tab-active {{ border-bottom: 4px solid #3b82f6; color: #3b82f6; font-weight: 900; }}
            .file-row {{ background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; transition: all 0.3s; }}
            .file-row:hover {{ background: rgba(51, 65, 85, 0.6); border-color: #3b82f6; }}
            .btn-action {{ transition: all 0.2s; font-weight: 700; font-size: 13px; }}
        </style>
    </head>
    <body class="p-4 md:p-10 bg-slate-950">
        <div class="max-w-6xl mx-auto">
            <header class="text-center mb-14">
                <h1 class="text-4xl font-black text-blue-400 mb-4">VpnClashFa Collector</h1>
                <p class="text-slate-500 text-sm">آخرین بروزرسانی: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </header>

            <section class="mb-14 glass p-8 rounded-[2rem] border-t-4 border-sky-500 shadow-2xl">
                <h2 class="text-2xl font-black mb-6 flex items-center text-sky-400"><i class="fa-brands fa-telegram ml-3 text-3xl"></i> پروکسی‌های تلگرام</h2>
                <div class="flex gap-8 mb-6 border-b border-white/10 text-xl">
                    <button onclick="switchTG('android')" id="tab-android" class="pb-4 px-2 tab-active">اندروید</button>
                    <button onclick="switchTG('windows')" id="tab-windows" class="pb-4 px-2 text-slate-400">ویندوز</button>
                    <button onclick="switchTG('mixed')" id="tab-mixed" class="pb-4 px-2 text-slate-400">میکس</button>
                </div>
                <div id="proxy-display" class="proxy-box mb-8 shadow-inner">در حال بارگذاری...</div>
                <button onclick="copyCurrentProxy()" class="w-full bg-sky-600 hover:bg-sky-500 py-5 rounded-2xl text-xl font-black transition active:scale-[0.98]">
                    <i class="fa-solid fa-copy ml-2"></i> کپی تمام پروکسی‌ها
                </button>
            </section>

            <h2 class="text-2xl font-black mb-8 flex items-center text-blue-400"><i class="fa-solid fa-link-slash ml-3"></i> لینک‌های اشتراک و کلاینت‌ها</h2>
            <div class="space-y-8">
    """

    sources = set()
    if os.path.exists(sub_root):
        for d in os.listdir(sub_root):
            if os.path.isdir(os.path.join(sub_root, d)) and d != "final":
                sources.add(d)
    
    # اولویت‌بندی جدید: ابتدا Tested، سپس بقیه، و در نهایت All
    sorted_sources = sorted(list(sources), key=lambda x: (
        x.lower() == 'all',       # All بره آخر
        x.lower() != 'tested',    # Tested بیاد اول
        x.lower()                 # بقیه بر اساس الفبا
    ))

    for source_name in sorted_sources:
        files_to_show = []
        
        # ۱. فایل‌های اصلی
        orig_path = os.path.join(sub_root, source_name)
        if os.path.exists(orig_path):
            for f in os.listdir(orig_path):
                files_to_show.append((f, f"{repo_raw_url}/sub/{source_name}/{f}"))
        
        # ۲. فایل‌های تبدیل شده
        conv_path = os.path.join(final_root, source_name if source_name != "tested" else "tested_ping_passed")
        if os.path.exists(conv_path):
            for f in os.listdir(conv_path):
                files_to_show.append((f, f"{repo_raw_url}/sub/final/{source_name if source_name != 'tested' else 'tested_ping_passed'}/{f}"))

        if not files_to_show: continue

        # تغییر نام All به میکس همه کانفیگا
        display_title = "میکس همه کانفیگا" if source_name.lower() == "all" else (
            "تست شده (Ping & Speed)" if source_name.lower() == "tested" else source_name
        )
        
        is_tested = source_name.lower() == 'tested'
        border_color = "border-emerald-500" if is_tested else "border-slate-700"

        html_content += f"""
        <div class="glass rounded-[1.5rem] overflow-hidden accordion-item border-r-8 {border_color} shadow-lg">
            <button onclick="toggleAccordion(this)" class="w-full p-6 text-right flex justify-between items-center hover:bg-white/5 transition">
                <span class="text-2xl font-black {'text-emerald-400' if is_tested else 'text-slate-200'} italic">
                    <i class="fa-solid {'fa-bolt' if is_tested else 'fa-folder-open'} ml-4"></i>{display_title}
                </span>
                <i class="fa-solid fa-plus text-slate-500"></i>
            </button>
            <div class="accordion-content bg-slate-900/30">
                <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        """

        # مرتب‌سازی فایل‌ها (برای اینکه معمولی و بیس۶۴ کنار هم بیفتن)
        sorted_files = sorted(files_to_show, key=lambda x: x[0].replace('_base64', ''))

        for fname, furl in sorted_files:
            icon = next((v for k, v in client_icons.items() if k in fname.lower()), "fa-file-code")
            html_content += f"""
            <div class="file-row flex flex-col gap-4">
                <div class="flex items-center gap-3">
                    <i class="fa-solid {icon} text-blue-400 text-2xl"></i>
                    <span class="text-base font-bold truncate text-slate-200" title="{fname}">{fname}</span>
                </div>
                <div class="flex gap-2">
                    <button onclick="copyText('{furl}')" class="flex-1 bg-blue-600/20 text-blue-400 py-3 rounded-xl btn-action hover:bg-blue-600 hover:text-white">لینک</button>
                    <button onclick="copyContent('{furl}')" class="flex-1 bg-purple-600/20 text-purple-400 py-3 rounded-xl btn-action hover:bg-purple-600 hover:text-white">متن</button>
                    <button onclick="downloadFile('{furl}', '{fname}')" class="bg-slate-700 text-white px-5 py-3 rounded-xl btn-action hover:bg-emerald-600"><i class="fa-solid fa-download text-lg"></i></button>
                </div>
            </div>"""
        
        html_content += "</div></div></div>"

    html_content += """
        </div>
        <script>
            let tgData = { android: '', windows: '', mixed: '' };
            async function loadTGData() {
                try {
                    const [a, w, m] = await Promise.all([
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_android.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_windows.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg.txt').then(r => r.text())
                    ]);
                    tgData.android = a.trim(); tgData.windows = w.trim(); tgData.mixed = m.trim();
                    switchTG('android');
                } catch(e) { console.error(e); }
            }
            function switchTG(mode) {
                document.getElementById('proxy-display').innerText = tgData[mode].split('\\n').join('\\n\\n');
                ['android', 'windows', 'mixed'].forEach(m => {
                    document.getElementById('tab-' + m).className = 'pb-4 px-2 ' + (m === mode ? 'tab-active' : 'text-slate-400');
                });
                window.currentMode = mode;
            }
            function copyCurrentProxy() {
                navigator.clipboard.writeText(tgData[window.currentMode]);
                alert('کپی شد');
            }
            function toggleAccordion(btn) {
                const item = btn.parentElement;
                item.classList.toggle('open');
                btn.querySelector('.fa-solid:last-child').classList.toggle('fa-plus');
                btn.querySelector('.fa-solid:last-child').classList.toggle('fa-minus');
            }
            function copyText(t) { navigator.clipboard.writeText(t); alert('لینک کپی شد'); }
            async function copyContent(url) {
                const r = await fetch(url); const t = await r.text();
                navigator.clipboard.writeText(t); alert('محتوای فایل کپی شد');
            }
            async function downloadFile(url, name) {
                const r = await fetch(url); const b = await r.blob();
                const a = document.createElement('a'); a.href = URL.createObjectURL(b);
                a.download = name; a.click();
            }
            loadTGData();
        </script>
    </body>
    </html>
    """
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_web_page()
