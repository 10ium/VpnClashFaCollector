import os
import datetime

def generate_web_page():
    sub_root = "sub"
    final_root = "sub/final"
    output_html = "index.html"
    repo_raw_url = "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main"
    favicon_url = "https://raw.githubusercontent.com/10ium/VpnClashFaCollector/refs/heads/main/config/favicon.ico"
    
    # ترتیب دقیق فایل‌ها برای بخش تست شده
    tested_file_order = [
        "speed_passed.txt", "speed_passed_base64.txt",
        "ping_passed.txt", "ping_passed_base64.txt",
        "clash.yaml", "clashr.yaml",
        "surfboard.conf", "v2ray.txt",
        "quantumult.conf", "surge4.conf",
        "ss_android.txt", "ss_sip002.txt",
        "loon.config", "ssr.txt",
        "ssd.txt", "" 
    ]

    # ترتیب دقیق فایل‌ها برای بقیه منابع
    source_file_order = [
        "mixed.txt", "mixed_base64.txt",
        "vless.txt", "vless_base64.txt",
        "vmess.txt", "vmess_base64.txt",
        "trojan.txt", "trojan_base64.txt",
        "ss.txt", "ss_base64.txt",
        "hysteria2.txt", "hysteria2_base64.txt",
        "anytls.txt", "anytls_base64.txt",
        "ssr.txt", "ssr_base64.txt",
        "ssh.txt", "ssh_base64.txt",
        "wireguard.txt", "wireguard_base64.txt",
        "warp.txt", "warp_base64.txt",
        "clash.yaml", "clashr.yaml",
        "tg_android.txt", "tg_windows.txt",
        "v2ray.txt", "surfboard.conf",
        "quantumult.conf", "surge4.conf",
        "ss_sip002.txt", "ss_android.txt",
        "loon.config", "quanx.conf"
    ]

    client_icons = {
        "clash": "fa-circle-nodes", "v2ray": "fa-share-nodes", "ss": "fa-key",
        "base64": "fa-code", "txt": "fa-file-lines", "yaml": "fa-file-code", "conf": "fa-gear"
    }

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl" class="scroll-smooth">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VpnClashFa Manager</title>
        <link rel="icon" type="image/x-icon" href="{favicon_url}">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700;900&display=swap');
            body {{ font-family: 'Vazirmatn', sans-serif; background: #0b0f1a; color: #e2e8f0; font-size: 18px; }}
            .glass {{ background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); }}
            .accordion-content {{ max-height: 0; overflow: hidden; transition: max-height 0.5s ease; }}
            .open .accordion-content {{ max-height: 5000px; }}
            .proxy-box {{ font-family: monospace; background: #000; padding: 20px; border-radius: 15px; height: 300px; overflow-y: auto; direction: ltr; text-align: left; font-size: 14px; border: 1px solid #1e293b; }}
            .tab-active {{ border-bottom: 4px solid #3b82f6; color: #3b82f6; font-weight: 900; }}
            .file-card {{ background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; }}
            .btn-action {{ transition: all 0.2s; font-size: 14px; font-weight: 700; }}
            .social-card {{ transition: all 0.3s; border: 1px solid rgba(255,255,255,0.05); }}
            .social-card:hover {{ background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.4); transform: translateY(-2px); }}
            #toast {{ visibility: hidden; min-width: 200px; background-color: #3b82f6; color: #fff; text-align: center; border-radius: 10px; padding: 12px; position: fixed; z-index: 100; left: 50%; bottom: 30px; transform: translateX(-50%); font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
            #toast.show {{ visibility: visible; animation: fadein 0.5s, fadeout 0.5s 1.5s; }}
            @keyframes fadein {{ from {{ bottom: 0; opacity: 0; }} to {{ bottom: 30px; opacity: 1; }} }}
            @keyframes fadeout {{ from {{ bottom: 30px; opacity: 1; }} to {{ bottom: 0; opacity: 0; }} }}
            .nav-btn {{ position: fixed; right: 20px; width: 45px; height: 45px; border-radius: 50%; display: flex; items-center: center; justify-content: center; z-index: 50; box-shadow: 0 4px 10px rgba(0,0,0,0.5); transition: 0.3s; }}
            .nav-btn:hover {{ transform: scale(1.1); }}
        </style>
    </head>
    <body class="p-4 md:p-10 relative">
        <!-- Toast Notification -->
        <div id="toast">کپی شد!</div>

        <!-- Scroll Buttons -->
        <button onclick="window.scrollTo(0,0)" class="nav-btn bottom-20 bg-blue-600 text-white" title="برو به بالا">
            <i class="fa-solid fa-arrow-up"></i>
        </button>
        <button onclick="window.scrollTo(0, document.body.scrollHeight)" class="nav-btn bottom-5 bg-slate-700 text-white" title="برو به پایین">
            <i class="fa-solid fa-arrow-down"></i>
        </button>

        <div class="max-w-6xl mx-auto">
            <header id="top" class="text-center mb-12">
                <h1 class="text-4xl font-black text-blue-500 mb-2">VpnClashFa Collector</h1>
                <p class="text-slate-500 text-sm italic">بروزرسانی: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </header>

            <section class="mb-12 glass p-6 rounded-3xl border-t-4 border-sky-500 shadow-2xl">
                <h2 class="text-2xl font-black mb-6 flex items-center text-sky-400"><i class="fa-brands fa-telegram ml-3 text-3xl"></i> پروکسی‌های تلگرام</h2>
                <div class="flex gap-6 mb-6 border-b border-white/10 text-lg">
                    <button onclick="switchTG('android')" id="tab-android" class="pb-3 px-2 tab-active transition-all">اندروید</button>
                    <button onclick="switchTG('windows')" id="tab-windows" class="pb-3 px-2 text-slate-400 transition-all">ویندوز</button>
                    <button onclick="switchTG('mixed')" id="tab-mixed" class="pb-3 px-2 text-slate-400 transition-all">میکس</button>
                </div>
                <div id="proxy-display" class="proxy-box mb-6 shadow-inner">در حال دریافت پروکسی‌ها...</div>
                <button onclick="copyCurrentProxy()" class="w-full bg-sky-600 hover:bg-sky-500 py-4 rounded-xl font-black transition flex items-center justify-center">
                    <i class="fa-solid fa-copy ml-2 text-xl"></i> کپی تمام پروکسی‌ها
                </button>
            </section>

            <h2 class="text-2xl font-black mb-8 flex items-center text-blue-400"><i class="fa-solid fa-server ml-3"></i> لینک‌های اشتراک</h2>
            <div class="space-y-6">
    """

    folders = [d for d in os.listdir(sub_root) if os.path.isdir(os.path.join(sub_root, d)) and d != "final"]
    
    def get_priority(name):
        n = name.lower()
        if n == 'tested': return 1 
        if n == 'all': return 2    
        return 3                   

    sorted_folders = sorted(folders, key=lambda x: (get_priority(x), x.lower()))

    for folder in sorted_folders:
        is_all = folder.lower() == 'all'
        is_tested = folder.lower() == 'tested'
        display_name = "تست شده (Ping & Speed)" if is_tested else ("میکس همه کانفیگا" if is_all else folder)
        border_class = "border-emerald-500" if is_tested else ("border-blue-600" if is_all else "border-slate-700")
        
        html_content += f"""
        <div class="glass rounded-3xl overflow-hidden accordion-item border-r-8 {border_class} shadow-lg">
            <button onclick="toggleAccordion(this)" class="w-full p-6 text-right flex justify-between items-center hover:bg-white/5 transition">
                <span class="text-xl font-black {'text-emerald-400' if is_tested else 'text-slate-200'} italic">
                    <i class="fa-solid {'fa-check-double' if is_tested else ('fa-layer-group' if is_all else 'fa-folder')} ml-3"></i>{display_name}
                </span>
                <i class="fa-solid fa-plus text-slate-500"></i>
            </button>
            <div class="accordion-content bg-black/20">
                <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        """

        current_order = tested_file_order if is_tested else source_file_order
        available_files = {}
        
        p1 = os.path.join(sub_root, folder)
        if os.path.exists(p1):
            for f in os.listdir(p1): available_files[f] = f"{repo_raw_url}/sub/{folder}/{f}"
        
        final_folder_name = "tested_ping_passed" if is_tested else folder
        p2 = os.path.join(final_root, final_folder_name)
        if os.path.exists(p2):
            for f in os.listdir(p2): available_files[f] = f"{repo_raw_url}/sub/final/{final_folder_name}/{f}"

        for target in current_order:
            if target == "raw_results": continue 
            if not target:
                html_content += '<div class="hidden md:block"></div>'
                continue
                
            if target in available_files:
                furl = available_files[target]
                icon = next((v for k, v in client_icons.items() if k in target.lower()), "fa-file-code")
                html_content += f"""
                <div class="file-card flex flex-col gap-4">
                    <div class="flex items-center gap-3">
                        <i class="fa-solid {icon} text-blue-400 text-xl"></i>
                        <span class="text-sm font-bold truncate text-slate-300">{target}</span>
                    </div>
                    <div class="flex gap-1">
                        <button onclick="copyText('{furl}')" class="flex-1 bg-blue-600/20 text-blue-400 py-2 rounded-lg btn-action hover:bg-blue-600 hover:text-white transition-all">لینک</button>
                        <button onclick="copyContent('{furl}')" class="flex-1 bg-purple-600/20 text-purple-400 py-2 rounded-lg btn-action hover:bg-purple-600 hover:text-white transition-all">متن</button>
                        <button onclick="downloadFile('{furl}', '{target}')" class="bg-slate-700 text-white px-4 py-2 rounded-lg btn-action hover:bg-emerald-600"><i class="fa-solid fa-download"></i></button>
                    </div>
                </div>"""
        
        html_content += "</div></div></div>"

    html_content += """
            </div>

            <footer id="bottom" class="mt-16 mb-8">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <a href="https://t.me/vpnclashfa" target="_blank" class="social-card glass rounded-2xl p-6 flex items-center justify-between group">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 bg-sky-500/20 rounded-full flex items-center justify-center text-sky-400 text-2xl group-hover:bg-sky-500 group-hover:text-white transition-all">
                                <i class="fa-brands fa-telegram"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-lg">کانال تلگرام</h3>
                                <p class="text-slate-500 text-sm">@vpnclashfa</p>
                            </div>
                        </div>
                        <i class="fa-solid fa-arrow-up-right-from-square text-slate-600 group-hover:text-sky-400 transition-all"></i>
                    </a>

                    <a href="https://x.com/coldwater_10" target="_blank" class="social-card glass rounded-2xl p-6 flex items-center justify-between group">
                        <div class="flex items-center gap-4">
                            <div class="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 text-2xl group-hover:bg-blue-500 group-hover:text-white transition-all">
                                <i class="fa-brands fa-x-twitter"></i>
                            </div>
                            <div>
                                <h3 class="font-bold text-lg">توییتر (X)</h3>
                                <p class="text-slate-500 text-sm">@coldwater_10</p>
                            </div>
                        </div>
                        <i class="fa-solid fa-arrow-up-right-from-square text-slate-600 group-hover:text-blue-400 transition-all"></i>
                    </a>
                </div>
                <p class="text-center mt-12 text-slate-600 text-xs font-bold uppercase tracking-widest">Powered by Gemini AI & Open Source Tools</p>
            </footer>
        </div>

        <script>
            let tgData = {{ android: '', windows: '', mixed: '' }};
            
            function showToast() {{
                const t = document.getElementById("toast");
                t.className = "show";
                setTimeout(() => {{ t.className = t.className.replace("show", ""); }}, 2000);
            }}

            async function loadTGData() {{
                try {{
                    const [a, w, m] = await Promise.all([
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_android.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg_windows.txt').then(r => r.text()),
                        fetch('https://raw.githubusercontent.com/10ium/VpnClashFaCollector/main/sub/all/tg.txt').then(r => r.text())
                    ]);
                    tgData.android = a.trim(); tgData.windows = w.trim(); tgData.mixed = m.trim();
                    switchTG('android');
                }} catch(e) {{ console.error(e); }}
            }}

            function switchTG(mode) {{
                document.getElementById('proxy-display').innerText = tgData[mode].split('\\n').join('\\n\\n');
                ['android', 'windows', 'mixed'].forEach(m => {{
                    document.getElementById('tab-' + m).className = 'pb-3 px-2 ' + (m === mode ? 'tab-active' : 'text-slate-400');
                }});
                window.currentMode = mode;
            }}

            function copyCurrentProxy() {{ 
                navigator.clipboard.writeText(tgData[window.currentMode]); 
                showToast();
            }}

            function toggleAccordion(btn) {{
                btn.parentElement.classList.toggle('open');
                btn.querySelector('.fa-solid:last-child').classList.toggle('fa-plus');
                btn.querySelector('.fa-solid:last-child').classList.toggle('fa-minus');
            }}

            function copyText(t) {{ 
                navigator.clipboard.writeText(t); 
                showToast();
            }}

            async function copyContent(url) {{
                try {{
                    const r = await fetch(url); const t = await r.text();
                    navigator.clipboard.writeText(t); 
                    showToast();
                }} catch(e) {{ console.error(e); }}
            }}

            async function downloadFile(url, name) {{
                const r = await fetch(url); const b = await r.blob();
                const a = document.createElement('a'); a.href = URL.createObjectURL(b);
                a.download = name; a.click();
            }}

            loadTGData();
        </script>
    </body>
    </html>
    """
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_web_page()
