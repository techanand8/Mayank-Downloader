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

# --- THE MEGA UI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamDrop Pro | Mayank Anand</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --accent: #6366f1; --bg: #050810; --glass: rgba(255, 255, 255, 0.03); }
        body { background: var(--bg); font-family: 'Plus Jakarta Sans', sans-serif; color: #f8fafc; transition: all 0.5s ease; }
        
        /* Themes */
        .theme-neon { --accent: #00f2ff; --bg: #020617; }
        .theme-sunset { --accent: #f43f5e; --bg: #180303; }
        .theme-emerald { --accent: #10b981; --bg: #020602; }

        .mesh { position: fixed; inset: 0; z-index: -1; opacity: 0.4;
                background: radial-gradient(circle at 20% 20%, var(--accent) 0%, transparent 40%),
                            radial-gradient(circle at 80% 80%, var(--accent) 0%, transparent 40%); }
        
        .glass { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); border-radius: 2rem; }
        .btn-accent { background: var(--accent); color: #000; font-weight: 800; transition: 0.3s; }
        .btn-accent:hover { transform: translateY(-3px); box-shadow: 0 10px 30px -5px var(--accent); }
        
        .source-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; }
        .source-btn.active { background: var(--accent); color: black; border-color: var(--accent); }
        
        .loader { border: 4px solid rgba(255,255,255,0.1); border-top-color: var(--accent); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body class="p-4 md:p-10 theme-neon">
    <div class="mesh"></div>

    <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-12 gap-6">
        <div>
            <h1 class="text-4xl font-black italic tracking-tighter">STREAM<span style="color: var(--accent)">DROP</span></h1>
            <p class="text-xs font-bold tracking-[0.3em] uppercase opacity-50">Developed by Mayank Anand</p>
        </div>
        
        <div class="flex gap-3 bg-white/5 p-2 rounded-2xl border border-white/10">
            <button onclick="setTheme('neon')" class="w-8 h-8 rounded-full bg-[#00f2ff]"></button>
            <button onclick="setTheme('sunset')" class="w-8 h-8 rounded-full bg-[#f43f5e]"></button>
            <button onclick="setTheme('emerald')" class="w-8 h-8 rounded-full bg-[#10b981]"></button>
        </div>
    </div>

    <div class="max-w-4xl mx-auto mb-16">
        <div class="flex justify-center gap-4 mb-6">
            <button id="ytBtn" onclick="setSource('youtube')" class="source-btn active px-8 py-3 rounded-xl flex items-center gap-2 font-bold">
                <i data-lucide="youtube"></i> YouTube
            </button>
            <button id="igBtn" onclick="setSource('instagram')" class="source-btn px-8 py-3 rounded-xl flex items-center gap-2 font-bold">
                <i data-lucide="instagram"></i> Instagram
            </button>
        </div>

        <div class="glass p-3 flex items-center shadow-2xl">
            <input id="searchInput" type="text" placeholder="Search or paste link here..." 
                   class="flex-1 bg-transparent py-4 px-6 outline-none text-xl placeholder:text-gray-600">
            <button onclick="performSearch()" class="btn-accent p-5 rounded-2xl">
                <i data-lucide="zap"></i>
            </button>
        </div>
    </div>

    <div id="loader" class="hidden flex flex-col items-center py-20">
        <div class="loader"></div>
        <p class="mt-6 font-bold animate-pulse uppercase tracking-widest text-sm">Scanning Servers...</p>
    </div>

    <div id="resultsGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-8"></div>

    <div id="modal" class="hidden fixed inset-0 bg-black/90 backdrop-blur-xl flex items-center justify-center p-6 z-50">
        <div class="glass max-w-lg w-full p-10 relative overflow-hidden">
            <div id="modalProgress" class="absolute top-0 left-0 h-1 bg-white transition-all duration-500" style="width: 0%"></div>
            <button onclick="closeModal()" class="absolute top-6 right-6 opacity-50 hover:opacity-100"><i data-lucide="x"></i></button>
            
            <img id="modalThumb" class="w-full h-56 object-cover rounded-3xl mb-6 shadow-2xl">
            <h2 id="modalTitle" class="text-2xl font-extrabold mb-2 line-clamp-2"></h2>
            <p id="modalSource" class="text-xs uppercase font-bold tracking-widest opacity-40 mb-8"></p>
            
            <div class="space-y-4">
                <label class="text-xs font-bold opacity-50 uppercase">Select Quality</label>
                <select id="qualitySelect" class="w-full bg-white/10 border border-white/10 rounded-2xl p-4 outline-none font-bold"></select>
                <button onclick="initDownload()" class="w-full btn-accent py-5 rounded-2xl flex items-center justify-center gap-3 text-lg">
                    <i data-lucide="download-cloud"></i> START DOWNLOAD
                </button>
            </div>
        </div>
    </div>

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
            document.getElementById('searchInput').placeholder = s === 'youtube' ? "Search YouTube..." : "Paste Instagram Link...";
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
            } catch (e) { alert("Search failed! Try a direct link."); }
            finally { document.getElementById('loader').classList.add('hidden'); }
        }

        function renderResults() {
            const grid = document.getElementById('resultsGrid');
            grid.innerHTML = searchData.map((v, i) => `
                <div onclick="openModal(${i})" class="glass p-5 group cursor-pointer hover:border-white/20 transition-all duration-500">
                    <div class="relative mb-4 overflow-hidden rounded-2xl">
                        <img src="${v.thumbnail}" class="w-full h-40 object-cover group-hover:scale-110 transition-transform duration-700">
                        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                            <i data-lucide="play-circle" class="w-12 h-12 text-white"></i>
                        </div>
                    </div>
                    <h3 class="font-bold text-sm line-clamp-2 mb-2 group-hover:text-[var(--accent)] transition-colors">${v.title}</h3>
                    <div class="flex justify-between items-center opacity-40 text-[10px] font-black uppercase">
                        <span>${currentSource}</span>
                        <span>${v.duration || ''}</span>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }

        async function openModal(i) {
            activeVideo = searchData[i];
            document.getElementById('modalTitle').innerText = activeVideo.title;
            document.getElementById('modalThumb').src = activeVideo.thumbnail;
            document.getElementById('modalSource').innerText = "Source: " + currentSource;
            document.getElementById('qualitySelect').innerHTML = '<option>Analyzing qualities...</option>';
            document.getElementById('modal').classList.remove('hidden');

            const res = await fetch(`/info?url=${encodeURIComponent(activeVideo.url)}`);
            const data = await res.json();
            
            document.getElementById('qualitySelect').innerHTML = data.formats.map(f => 
                `<option value="${f.id}">${f.res} - ${f.ext.toUpperCase()}</option>`
            ).join('');
        }

        function closeModal() { document.getElementById('modal').classList.add('hidden'); }

        function initDownload() {
            const fmt = document.getElementById('qualitySelect').value;
            document.getElementById('modalProgress').style.width = "100%";
            setTimeout(() => {
                window.location.href = `/download?url=${encodeURIComponent(activeVideo.url)}&format_id=${fmt}`;
                document.getElementById('modalProgress').style.width = "0%";
            }, 1000);
        }
    </script>
</body>
</html>
"""

# --- BACKEND WITH INSTA + YT SUPPORT ---

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_CONTENT

@app.get("/search")
def search(q: str, source: str):
    # Instagram usually needs a direct link, so we check that
    if source == "instagram" and "instagram.com" not in q:
        return [{"title": "Error: Paste an IG link", "thumbnail": "", "url": "", "duration": ""}]
    
    # YouTube handles search queries and links
    search_type = f"ytsearch10:{q}" if "http" not in q else q
    
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(search_type, download=False)
        entries = info.get('entries', [info])
        
        return [{
            "title": e.get("title", "No Title"),
            "url": e.get("url") or e.get("webpage_url"),
            "thumbnail": e.get("thumbnails")[0]['url'] if e.get("thumbnails") else "https://via.placeholder.com/300",
            "duration": e.get("duration_string")
        } for e in entries if e][:10]

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
    ydl_opts = {
        'format': f"{format_id}+bestaudio/best",
        'outtmpl': path,
        'merge_output_format': 'mp4',
        # Added cookie support for IG if needed
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".%(ext)s", ".mp4")
        return FileResponse(path=filename, filename=f"StreamDrop_{file_id}.mp4")

if __name__ == "__main__":
    print(f"🔥 StreamDrop Pro by Mayank Anand is starting...")
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
