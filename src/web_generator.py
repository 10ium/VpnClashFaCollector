import os
import datetime

def generate_web_page():
    base_dir = "sub/final"
    output_html = "index.html"
    repo_raw_url = "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main"
    
    client_icons = {
        "clash": "fa-circle-nodes", "v2ray": "fa-share-nodes", "ss": "fa-key",
        "surfboard": "fa-wind", "surge": "fa-bolt", "quan": "fa-gear", "base64": "fa-code"
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>پنل مدیریت VpnClashFa</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');
            body {{ font-family: 'Vazirmatn', sans-serif; background: #0f172a; color: #f1f5f9; }}
            .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
            .accordion-content {{ max-height: 0; overflow: hidden; transition: max-height 0.5s ease-in-out; }}
            .open .accordion-content {{ max-height: 2500px; }}
            .proxy-box {{ font-family: monospace; background: #000; padding: 15px; border-radius: 12px; height: 220px; overflow-y: auto; white-space: pre-wrap; }}
            .tab-active {{ border-bottom: 2px solid #3b82f6; color: #3b82f6; }}
        </style>
    </head>
    <body class="p-4 md:p-10 bg-slate-950">
        <div class="max-w-6xl mx-auto">
            <header class="text-center mb-10">
                <h1 class="text-3xl font-black text-blue-400 mb-2">VpnClashFa Collector</h1>
                <p class="text-slate-500 text-xs italic">آخرین بروزرسانی: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </header>

            <section class="mb-12">
                <h2 class="text-xl font-bold mb-6 flex items-center text-emerald-400"><i class="fa-solid fa-check-double ml-2"></i> منابع تست شده</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    """

    gold_links = [
        ("تست شده با پینگ (Normal)", f"{repo_raw_url}/sub/tested/ping_passed.txt"),
        ("تست شده با پینگ (Base64)", f"{repo_raw_url}/sub/tested/ping_passed_base64.txt"),
        ("تست شده با سرعت دانلود (Normal)", f"{repo_raw_url}/sub/tested/speed_passed.txt"),
        ("تست شده با سرعت دانلود (Base64)", f"{repo_raw_url}/sub/tested/speed_passed_base64.txt")
    ]
    for title, url in gold_links:
        html_content += f"""
                    <div class="glass p-4 rounded-2xl flex justify-between items-center border-r-4 border-emerald-500 hover:bg-emerald-500/5 transition cursor-default">
                        <span class="text-sm font-bold">{title}</span>
                        <div class="flex gap-2">
                            <button onclick="copyText('{url}')" class="bg-blue-600/20 text-blue-400 p-2 rounded-lg text-xs hover:bg-blue-600 hover:text-white transition">کپی لینک</button>
                            <button onclick="downloadFile('{url}', '{title}.txt')" class="bg-slate-700 text-white p-2 rounded-lg text-xs hover:bg-emerald-600 transition"><i class="fa-solid fa-download"></i></button>
                        </div>
                    </div>"""

    # بخش دوم: پروکسی تلگرام
    html_content += """
                </div>
            </section>

            <section class="mb-12 glass p-6 rounded-3xl border-t-4 border-sky-500 shadow-xl">
                <h2 class="text-xl font-bold mb-4 flex items-center text-sky-400"><i class="fa-brands fa-telegram ml-2"></i> پروکسی‌های تلگرام</h2>
                
                <div class="flex gap-4 mb-4 border-b border-white/10 text-sm">
                    <button onclick="switchTG('android')" id="tab-android" class="pb-2 px-2 tab-active transition-all">اندروید</button>
                    <button onclick="switchTG('windows')" id="tab-windows" class="pb-2 px-2 text-slate-400 transition-all">ویندوز</button>
                    <button onclick="switchTG('mixed')" id="tab-mixed" class="pb-2 px-2 text-slate-400 transition-all">میکس</button>
                </div>

                <div id="proxy-display" class="proxy-box text-[11px] text-sky-300 mb-4 italic">در حال بارگذاری...</div>
                
                <button onclick="copyCurrentProxy()" class="w-full bg-sky-600 hover:bg-sky-500 py-3 rounded-xl font-bold transition flex items-center justify-center shadow-lg active:scale-95">
                    <i class="fa-solid fa-copy ml-2"></i> کپی تمام پروکسی‌های این لیست
                </button>
            </section>

            <h2 class="text-xl font-bold mb-6 flex items-center text-blue-400"><i class="fa-solid fa-list-ul ml-2"></i> لینک‌های اشتراک منابع</h2>
            <div class="space-y-4">
    """

    if os.path.exists(base_dir):
        all_folders = sorted(os.listdir(base_dir))
        
        # --- منطق اولویت‌بندی جدید ---
        # جدا کردن پوشه‌هایی که با 'all' شروع می‌شوند برای نمایش در ابتدا
        priority_folders = [f for f in all_folders if f.lower().startswith('all')]
        other_folders = [f for f in all_folders if not f.lower().startswith('all')]
        
        final_list = priority_folders + other_folders

        for folder in final_list:
            folder_path = os.path.join(base_dir, folder)
            if not os.path.isdir(folder_path): continue

            # متمایز کردن ظاهر پوشه‌های ALL با رنگ آبی تیره‌تر
            is_priority = folder.lower().startswith('all')
            border_style = "border-l-4 border-blue-600 shadow-blue-900/10" if is_priority else "border-white/5"

            html_content += f"""
            <div class="glass rounded-2xl overflow-hidden accordion-item border {border_style}">
                <button onclick="toggleAccordion(this)" class="w-full p-5 text-right flex justify-between items-center hover:bg-white/5 transition">
                    <span class="text-sm font-bold {'text-blue-400' if is_priority else 'text-slate-300'} italic">
                        <i class="fa-solid {'fa-box-archive' if is_priority else 'fa-folder'} ml-3 {'text-blue-500' if is_priority else 'text-slate-500'}"></i>{folder}
                    </span>
                    <i class="fa-solid fa-chevron-down text-xs text-slate-500 transition-transform duration-300"></i>
                </button>
                <div class="accordion-content bg-black/20">
                    <div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            """

            for file in sorted(os.listdir(folder_path)):
                f_url = f"{repo_raw_url}/sub/final/{folder}/{file}"
                icon = next((v for k, v in client_icons.items() if k in file.lower()), "fa-link")
                
                html_content += f"""
                <div class="bg-slate-800/40 p-3 rounded-xl border border-white/5 flex flex-col gap-3 hover:border-blue-500/30 transition">
                    <div class="flex items-center text-[10px] font-bold text-slate-300 truncate">
                        <i class="fa-solid {icon} ml-2 text-blue-400"></i> {file}
                    </div>
                    <div class="flex gap-1">
                        <button onclick="copyText('{f_url}')" class="flex-1 bg-slate-700 hover:bg-blue-600 py-1 rounded text-[9px] transition">لینک</button>
                        <button onclick="copyContent('{f_url}')" class="flex-1 bg-slate-700 hover:bg-purple-600 py-1 rounded text-[9px] transition">متن</button>
                        <button onclick="downloadFile('{f_url}', '{file}')" class="flex-1 bg-slate-700 hover:bg-emerald-600 py-1 rounded text-[9px] transition">دانلود</button>
                    </div>
                </div>"""
            html_content += "</div></div></div>"

    # بخش جاوا اسکریپت (ثابت ماند)
    html_content += """
        </div>
        <script>
            let tgData = { android: '', windows: '', mixed: '' };
            let currentMode = 'android';

            async function loadTGData() {
                try {
                    const [a, w, m] = await Promise.all([
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_android.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_windows.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg.txt').then(r => r.text())
                    ]);
                    tgData.android = a.split('\\n').filter(l => l.trim()).join('\\n\\n');
                    tgData.windows = w.split('\\n').filter(l => l.trim()).join('\\n\\n');
                    tgData.mixed = m.split('\\n').filter(l => l.trim()).join('\\n\\n');
                    switchTG('android');
                } catch(e) { document.getElementById('proxy-display').innerText = 'خطا در بارگذاری اطلاعات'; }
            }

            function switchTG(mode) {
                currentMode = mode;
                document.getElementById('proxy-display').innerText = tgData[mode];
                ['android', 'windows', 'mixed'].forEach(m => {
                    document.getElementById('tab-' + m).className = 'pb-2 px-2 ' + (m === mode ? 'tab-active' : 'text-slate-400');
                });
            }

            function copyCurrentProxy() {
                navigator.clipboard.writeText(tgData[currentMode].replace(/\\n\\n/g, '\\n'));
                alert('کپی شد!');
            }

            function toggleAccordion(btn) {
                btn.parentElement.classList.toggle('open');
                btn.querySelector('.fa-chevron-down').classList.toggle('rotate-180');
            }

            function copyText(t) { navigator.clipboard.writeText(t); alert('لینک کپی شد'); }
            
            async function copyContent(url) {
                const res = await fetch(url);
                const text = await res.text();
                navigator.clipboard.writeText(text);
                alert('محتوای فایل کپی شد');
            }

            async function downloadFile(url, name) {
                const res = await fetch(url);
                const blob = await res.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = name;
                a.click();
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
