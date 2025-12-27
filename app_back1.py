import os
import uuid
import webbrowser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- THE MAYANK ANAND EXCLUSIVE UI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAYANK ANAND | Digital Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --accent: #6366f1; --bg: #050810; }
        body { background: var(--bg); font-family: 'Plus Jakarta Sans', sans-serif; color: #f8fafc; transition: all 0.5s ease; }
        
        .theme-neon { --accent: #00f2ff; --bg: #020617; }
        .theme-sunset { --accent: #f43f5e; --bg: #180303; }
        .theme-emerald { --accent: #10b981; --bg: #020602; }

        .mesh { position: fixed; inset: 0; z-index: -1; opacity: 0.3;
                background: radial-gradient(circle at 10% 10%, var(--accent) 0%, transparent 40%),
                            radial-gradient(circle at 90% 90%, var(--accent) 0%, transparent 40%); }
        
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(25px); border: 1px solid rgba(255,255,255,0.08); border-radius: 2.5rem; }
        .btn-accent { background: var(--accent); color: #000; font-weight: 800; transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .btn-accent:hover { transform: scale(1.05); shadow: 0 15px 30px -10px var(--accent); }
        
        .source-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; }
        .source-btn.active { background: var(--accent); color: black; border-color: var(--accent); box-shadow: 0 0 20px -5px var(--accent); }
        
        .loader { border: 4px solid rgba(255,255,255,0.1); border-top-color: var(--accent); border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .brand-text { text-shadow: 0 0 30px var(--accent); letter-spacing: -0.05em; }
    </style>
</head>
<body class="p-4 md:p-10 theme-neon">
    <div class="mesh"></div>

    <div class="max-w-7xl mx-auto flex flex-col items-center mb-16 text-center">
        <div class="flex items-center gap-3 mb-2">
             <span class="bg-white/10 text-[var(--accent)] text-[10px] font-black px-3 py-1 rounded-full border border-[var(--accent)] tracking-widest uppercase">Premium Edition</span>
        </div>
        <h1 class="text-6xl md:text-8xl font-black brand-text italic uppercase">
            MAYANK<span style="color: var(--accent)">ANAND</span>
        </h1>
        <p class="text-gray-500 font-medium tracking-[0.4em] uppercase text-xs mt-4">Professional Media Engine</p>
        
        <div class="flex gap-4 mt-8 bg-white/5 p-3 rounded-full border border-white/10">
            <button onclick="setTheme('neon')" class="w-6 h-6 rounded-full bg-[#00f2ff] hover:scale-125 transition"></button>
            <button onclick="setTheme('sunset')" class="w-6 h-6 rounded-full bg-[#f43f5e] hover:scale-125 transition"></button>
            <button onclick="setTheme('emerald')" class="w-6 h-6 rounded-full bg-[#10b981] hover:scale-125 transition"></button>
        </div>
    </div>

    <div class="max-w-4xl mx-auto mb-20">
        <div class="flex justify-center gap-3 mb-8">
            <button id="ytBtn" onclick="setSource('youtube')" class="source-btn active px-10 py-4 rounded-2xl flex items-center gap-3 font-black text-sm uppercase">
                <i data-lucide="youtube" class="w-5 h-5"></i> YouTube
            </button>
            <button id="igBtn" onclick="setSource('instagram')" class="source-btn px-10 py-4 rounded-2xl flex items-center gap-3 font-black text-sm uppercase">
                <i data-lucide="instagram" class="w-5 h-5"></i> Instagram
            </button>
        </div>

        <div class="glass p-4 flex items-center shadow-inner">
            <input id="searchInput" type="text" placeholder="Search anything or paste link..." 
                   class="flex-1 bg-transparent py-4 px-8 outline-none text-2xl font-semibold placeholder:text-gray-700">
            <button onclick="performSearch()" class="btn-accent px-8 py-5 rounded-3xl">
                <i data-lucide="search" class="w-6 h-6"></i>
            </button>
        </div>
    </div>

    <div id="loader" class="hidden flex flex-col items-center py-20">
        <div class="loader"></div>
        <p class="mt-6 font-black uppercase tracking-[0.3em] text-[10px] text-[var(--accent)]">Processing Request</p>
    </div>

    <div id="resultsGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10"></div>

    <div id="modal" class="hidden fixed inset-0 bg-black/95 backdrop-blur-3xl flex items-center justify-center p-6 z-50">
        <div class="glass max-w-lg w-full p-12 relative border-t-4 border-t-[var(--accent)]">
            <button onclick="closeModal()" class="absolute top-8 right-8 opacity-30 hover:opacity-100 transition"><i data-lucide="circle-x"></i></button>
            
            <img id="modalThumb" class="w-full h-60 object-cover rounded-[2rem] mb-8 shadow-2xl border border-white/5">
            <h2 id="modalTitle" class="text-2xl font-black mb-6 leading-tight"></h2>
            
            <div class="space-y-6">
                <div>
                    <label class="text-[10px] font-black opacity-30 uppercase tracking-widest mb-3 block">Choose Quality</label>
                    <select id="qualitySelect" class="w-full bg-white/5 border border-white/10 rounded-2xl p-5 outline-none font-bold text-lg focus:border-[var(--accent)] transition"></select>
                </div>
                <button onclick="initDownload()" class="w-full btn-accent py-6 rounded-[1.5rem] flex items-center justify-center gap-4 text-xl tracking-tighter">
                    <i data-lucide="download"></i> SECURE DOWNLOAD
                </button>
            </div>
        </div>
    </div>

    <footer class="mt-32 pb-10 text-center opacity-20 hover:opacity-100 transition duration-500">
        <p class="text-[10px] font-black tracking-[0.5em] uppercase">Built from scratch by Mayank Anand &copy; 2025</p>
    </footer>

    <script>
        lucide.createIcons();
        let currentSource = 'youtube';
        let searchData = [];
        let activeVideo = null;

        function setTheme(t) { document.body.className = 'p-4 md:p-10 theme-' + t; }
        function setSource(s) {
            currentSource = s;
            document.getElementById('ytBtn').classList.toggle('active', s === 'youtube');
            document.getElementById('igBtn').classList.toggle('active', s === 'instagram');
            document.getElementById('searchInput').placeholder = s === 'youtube' ? "Search for video..." : "Paste IG Post Link...";
        }

        async function performSearch() {
            const query = document.getElementById('searchInput').value;
            if(!query) return;
            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('resultsGrid').innerHTML = '';
            try {
                const res = await fetch(`/search?q=${encodeURIComponent(query)}&source=${currentSource}`);
                searchData = await res.json();
                renderResults();
            } catch (e) { alert("Search failed."); }
            finally { document.getElementById('loader').classList.add('hidden'); }
        }

        function renderResults() {
            const grid = document.getElementById('resultsGrid');
            grid.innerHTML = searchData.map((v, i) => `
                <div onclick="openModal(${i})" class="glass p-6 group cursor-pointer hover:bg-white/5 transition-all duration-500 hover:-translate-y-2">
                    <div class="relative mb-6 overflow-hidden rounded-[1.5rem]">
                        <img src="${v.thumbnail}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-700">
                    </div>
                    <h3 class="font-bold text-base line-clamp-2 mb-4 group-hover:text-[var(--accent)] transition-colors">${v.title}</h3>
                    <div class="flex items-center gap-2 opacity-30 text-[9px] font-black uppercase tracking-widest">
                        <i data-lucide="clock" class="w-3 h-3"></i>
                        <span>${v.duration || 'Video'}</span>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }

        async function openModal(i) {
            activeVideo = searchData[i];
            document.getElementById('modalTitle').innerText = activeVideo.title;
            document.getElementById('modalThumb').src = activeVideo.thumbnail;
            document.getElementById('qualitySelect').innerHTML = '<option>Decoding stream...</option>';
            document.getElementById('modal').classList.remove('hidden');
            const res = await fetch(`/info?url=${encodeURIComponent(activeVideo.url)}`);
            const data = await res.json();
            document.getElementById('qualitySelect').innerHTML = data.formats.map(f => 
                `<option value="${f.id}">${f.res} Quality (${f.ext.toUpperCase()})</option>`
            ).join('');
        }

        function closeModal() { document.getElementById('modal').classList.add('hidden'); }
        function initDownload() {
            const fmt = document.getElementById('qualitySelect').value;
            window.location.href = `/download?url=${encodeURIComponent(activeVideo.url)}&format_id=${fmt}`;
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---
@app.get("/", response_class=HTMLResponse)
def home(): return HTML_CONTENT

@app.get("/search")
def search(q: str, source: str):
    if source == "instagram" and "instagram.com" not in q:
        return [{"title": "Please provide a valid Instagram link", "thumbnail": "https://img.icons8.com/ios-filled/100/ffffff/instagram-new.png", "url": "", "duration": ""}]
    
    stype = f"ytsearch8:{q}" if "http" not in q else q
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(stype, download=False)
        entries = info.get('entries', [info])
        return [{
            "title": e.get("title", "Mayank Anand Downloader"),
            "url": e.get("url") or e.get("webpage_url"),
            "thumbnail": e.get("thumbnails")[0]['url'] if e.get("thumbnails") else "https://via.placeholder.com/400",
            "duration": e.get("duration_string")
        } for e in entries if e][:8]

@app.get("/info")
def get_info(url: str):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        seen = set()
        for f in info.get('formats', []):
            res = f.get('height')
            if res and res not in seen:
                formats.append({"id": f['format_id'], "res": f"{res}p", "ext": f['ext'] or 'mp4'})
                seen.add(res)
        return {"formats": sorted(formats, key=lambda x: int(x['res'][:-1]), reverse=True)}

@app.get("/download")
def download(url: str, format_id: str):
    file_id = str(uuid.uuid4())
    path = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    ydl_opts = {'format': f"{format_id}+bestaudio/best", 'outtmpl': path, 'merge_output_format': 'mp4'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".%(ext)s", ".mp4")
        return FileResponse(path=filename, filename=f"MA_Downloader_{file_id}.mp4")

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
