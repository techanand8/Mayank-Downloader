import os
import uuid
import webbrowser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# --- THE HEART-TOUCHING PREMIUM UI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAYANK ANAND | Infinity</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,700;1,900&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #8b5cf6; --bg: #030712; }
        body { background: var(--bg); font-family: 'DM Sans', sans-serif; color: #f8fafc; scroll-behavior: smooth; }
        
        .hero-text { 
            font-size: clamp(3rem, 10vw, 8rem);
            line-height: 0.8;
            background: linear-gradient(to bottom, #fff 30%, var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 30px rgba(139, 92, 246, 0.3));
        }
        
        .glass { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.05); border-radius: 2rem; }
        .tab-active { background: var(--primary); color: white; box-shadow: 0 0 20px var(--primary); }
        
        .card-anim { transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1); }
        .card-anim:hover { transform: translateY(-10px) scale(1.02); background: rgba(255,255,255,0.05); }
        
        .loader-ring { border: 4px solid rgba(255,255,255,0.05); border-top: 4px solid var(--primary); border-radius: 50%; width: 50px; height: 50px; animation: spin 1s cubic-bezier(0.5, 0, 0.5, 1) infinite; }
        @keyframes spin { 0% { transform: rotate(00deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="p-6 md:p-12">
    <div class="fixed inset-0 -z-10 overflow-hidden">
        <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 blur-[120px] rounded-full"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/20 blur-[120px] rounded-full"></div>
    </div>

    <header class="max-w-7xl mx-auto text-center mb-20">
        <p class="text-[10px] tracking-[0.8em] uppercase opacity-40 mb-4 font-bold">Crafted with Heart</p>
        <h1 class="hero-text font-black italic mb-6">MAYANK<br>ANAND</h1>
        <div class="h-1 w-24 bg-purple-600 mx-auto rounded-full"></div>
    </header>

    <div class="max-w-4xl mx-auto space-y-8 mb-20">
        <div class="flex flex-wrap justify-center gap-4">
            <button id="ytBtn" onclick="setSource('youtube')" class="tab-active px-8 py-3 rounded-full font-bold transition flex items-center gap-2">
                <i data-lucide="youtube" class="w-4 h-4"></i> YouTube
            </button>
            <button id="igBtn" onclick="setSource('instagram')" class="px-8 py-3 rounded-full font-bold bg-white/5 border border-white/10 flex items-center gap-2">
                <i data-lucide="instagram" class="w-4 h-4"></i> Instagram
            </button>
        </div>

        <div class="glass p-2 flex items-center">
            <input id="searchInput" type="text" placeholder="Tell me what you want to hear..." 
                   class="flex-1 bg-transparent py-5 px-8 outline-none text-xl placeholder:opacity-20">
            <button onclick="search(false)" class="bg-white text-black p-5 rounded-2xl hover:bg-purple-500 hover:text-white transition-all">
                <i data-lucide="search" class="w-6 h-6"></i>
            </button>
        </div>
    </div>

    <div id="loader" class="hidden flex flex-col items-center py-20">
        <div class="loader-ring"></div>
    </div>

    <div id="resultsGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"></div>

    <div id="loadMore" class="hidden text-center mt-16">
        <button onclick="search(true)" class="glass px-12 py-4 hover:bg-white/5 font-bold tracking-widest text-xs uppercase">Load More Results</button>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/90 backdrop-blur-2xl flex items-center justify-center p-6 z-50">
        <div class="glass max-w-lg w-full p-10 relative">
            <button onclick="closeModal()" class="absolute top-6 right-6 opacity-30 hover:opacity-100"><i data-lucide="x"></i></button>
            <img id="modalThumb" class="w-full h-48 object-cover rounded-3xl mb-6">
            <h2 id="modalTitle" class="text-xl font-bold mb-6 line-clamp-1"></h2>
            
            <div class="grid grid-cols-2 gap-4 mb-8">
                <button id="modeVid" onclick="setMode('video')" class="py-3 rounded-xl border border-white/10 bg-white/10 font-bold">Video</button>
                <button id="modeAud" onclick="setMode('audio')" class="py-3 rounded-xl border border-white/10 opacity-50 font-bold">Audio (MP3)</button>
            </div>

            <select id="qualitySelect" class="w-full bg-white/5 border border-white/10 rounded-xl p-4 mb-8 outline-none"></select>
            
            <button onclick="startDownload()" class="w-full py-5 rounded-2xl bg-white text-black font-black text-lg hover:bg-purple-400 transition-colors">
                DOWNLOAD NOW
            </button>
        </div>
    </div>

    <script>
        lucide.createIcons();
        let source = 'youtube';
        let mode = 'video';
        let page = 1;
        let activeVid = null;

        function setSource(s) {
            source = s;
            document.getElementById('ytBtn').className = s==='youtube' ? 'tab-active px-8 py-3 rounded-full font-bold' : 'px-8 py-3 rounded-full font-bold bg-white/5 border border-white/10';
            document.getElementById('igBtn').className = s==='instagram' ? 'tab-active px-8 py-3 rounded-full font-bold' : 'px-8 py-3 rounded-full font-bold bg-white/5 border border-white/10';
        }

        function setMode(m) {
            mode = m;
            document.getElementById('modeVid').style.opacity = m==='video' ? '1' : '0.4';
            document.getElementById('modeVid').style.background = m==='video' ? 'rgba(255,255,255,0.1)' : 'transparent';
            document.getElementById('modeAud').style.opacity = m==='audio' ? '1' : '0.4';
            document.getElementById('modeAud').style.background = m==='audio' ? 'rgba(255,255,255,0.1)' : 'transparent';
            updateQualityOptions();
        }

        async function search(more) {
            const q = document.getElementById('searchInput').value;
            if(!q) return;
            if(!more) { page = 1; document.getElementById('resultsGrid').innerHTML = ''; }
            else { page++; }

            document.getElementById('loader').classList.remove('hidden');
            try {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}&source=${source}&page=${page}`);
                const data = await res.json();
                render(data);
                document.getElementById('loadMore').classList.remove('hidden');
            } catch(e) { alert("Error"); }
            finally { document.getElementById('loader').classList.add('hidden'); }
        }

        function render(items) {
            const grid = document.getElementById('resultsGrid');
            items.forEach((v, i) => {
                const div = document.createElement('div');
                div.className = "glass p-4 card-anim cursor-pointer";
                div.onclick = () => openModal(v);
                div.innerHTML = `
                    <img src="${v.thumbnail}" class="w-full h-40 object-cover rounded-2xl mb-4">
                    <h3 class="font-bold text-sm line-clamp-2">${v.title}</h3>
                    <p class="text-[10px] opacity-30 mt-2 uppercase tracking-tighter">${v.channel || 'Content'}</p>
                `;
                grid.appendChild(div);
            });
            lucide.createIcons();
        }

        let fetchedFormats = [];
        async function openModal(v) {
            activeVid = v;
            document.getElementById('modalTitle').innerText = v.title;
            document.getElementById('modalThumb').src = v.thumbnail;
            document.getElementById('modal').classList.remove('hidden');
            
            const res = await fetch(`/info?url=${encodeURIComponent(v.url)}`);
            fetchedFormats = await res.json();
            updateQualityOptions();
        }

        function updateQualityOptions() {
            const sel = document.getElementById('qualitySelect');
            sel.innerHTML = '';
            const list = mode === 'video' ? fetchedFormats.video : fetchedFormats.audio;
            list.forEach(f => {
                sel.innerHTML += `<option value="${f.id}">${f.res || f.note || 'Original'}</option>`;
            });
        }

        function closeModal() { document.getElementById('modal').classList.add('hidden'); }

        function startDownload() {
            const fmt = document.getElementById('qualitySelect').value;
            window.location.href = `/download?url=${encodeURIComponent(activeVid.url)}&format_id=${fmt}&mode=${mode}`;
        }
    </script>
</body>
</html>
"""

# --- BACKEND ---
@app.get("/", response_class=HTMLResponse)
def home(): return HTML_CONTENT

@app.get("/search")
def search(q: str, source: str, page: int = 1):
    count = page * 8
    # Modified search to get more results for "next option" requirement
    search_query = f"ytsearch{count}:{q}" if "http" not in q else q
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get('entries', [info])
        # Return only the new set based on page
        start = (page-1)*8
        return [{
            "title": e.get("title"),
            "url": e.get("url") or e.get("webpage_url"),
            "thumbnail": e.get("thumbnails")[0]['url'] if e.get("thumbnails") else "",
            "channel": e.get("uploader"),
            "duration": e.get("duration_string")
        } for e in entries if e][start:start+8]

@app.get("/info")
def get_info(url: str):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        video = []
        audio = []
        seen_v = set()
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none':
                res = f.get('height')
                if res and res not in seen_v:
                    video.append({"id": f['format_id'], "res": f"{res}p", "ext": f['ext']})
                    seen_v.add(res)
            elif f.get('acodec') != 'none':
                audio.append({"id": f['format_id'], "note": f.get('format_note') or f.get('abr'), "ext": f['ext']})
        return {"video": sorted(video, key=lambda x: int(x['res'][:-1]), reverse=True), "audio": audio[:3]}

@app.get("/download")
def download(url: str, format_id: str, mode: str):
    file_id = str(uuid.uuid4())
    # Audio mode uses best audio only
    ydl_opts = {
        'format': f"{format_id}+bestaudio/best" if mode == 'video' else 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if mode == 'audio' else []
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Find the path of the downloaded file
        ext = 'mp3' if mode == 'audio' else 'mp4'
        filename = f"{info.get('title')}.{ext}"
        # We find the actual file in the folder by file_id
        actual_path = ""
        for f in os.listdir(DOWNLOAD_DIR):
            if file_id in f: actual_path = os.path.join(DOWNLOAD_DIR, f)
        return FileResponse(path=actual_path, filename=filename)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
