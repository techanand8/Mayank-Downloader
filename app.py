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

# --- THE ULTRA-MODERN LIGHTNING UI ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAYANK ANAND | LUXE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=Syne:wght@400;800&family=Outfit:wght@100;400;900&display=swap" rel="stylesheet">
    <style>
        :root { --glow: #8b5cf6; --bg: #020205; --font-main: 'Outfit', sans-serif; }
        
        body { 
            background-color: var(--bg); 
            color: white; 
            font-family: var(--font-main);
            overflow-x: hidden;
            transition: all 0.5s ease;
        }

        /* Lightning Mesh Background */
        .lightning-bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
            background: radial-gradient(circle at 50% -20%, var(--glow) 0%, transparent 40%),
                        radial-gradient(circle at 0% 100%, #3b82f6 0%, transparent 30%);
            opacity: 0.5; filter: blur(80px);
        }

        .brand-name {
            font-size: clamp(3rem, 12vw, 9rem);
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: -0.05em;
            background: linear-gradient(to bottom, #fff, var(--glow));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 0.85;
            filter: drop-shadow(0 0 20px rgba(255,255,255,0.2));
        }

        .glass-panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(40px) saturate(150%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 3rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .neo-input {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        .neo-input:focus {
            border-color: var(--glow);
            box-shadow: 0 0 20px var(--glow);
            background: rgba(255,255,255,0.08);
        }

        .glow-btn {
            background: var(--glow);
            color: black;
            font-weight: 800;
            transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .glow-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 40px var(--glow);
        }

        /* Result Cards */
        .result-card {
            background: rgba(255,255,255,0.02);
            border-radius: 2rem;
            border: 1px solid rgba(255,255,255,0.05);
            transition: 0.4s;
        }
        .result-card:hover {
            border-color: var(--glow);
            transform: translateY(-8px);
            background: rgba(255,255,255,0.06);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--glow); border-radius: 10px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-12">
    <div class="lightning-bg"></div>

    <div class="fixed top-6 right-6 flex gap-3 z-50 glass-panel p-3 rounded-full">
        <button onclick="changeStyle('Space Grotesk', '#00ffcc')" class="w-6 h-6 rounded-full bg-[#00ffcc]"></button>
        <button onclick="changeStyle('Syne', '#ff00ff')" class="w-6 h-6 rounded-full bg-[#ff00ff]"></button>
        <button onclick="changeStyle('Outfit', '#8b5cf6')" class="w-6 h-6 rounded-full bg-[#8b5cf6]"></button>
    </div>

    <header class="max-w-7xl mx-auto text-center mt-12 mb-20">
        <div class="inline-block px-4 py-1 rounded-full border border-white/20 text-[10px] uppercase tracking-[0.5em] mb-6 backdrop-blur-xl">
            Powered by Advanced Logic
        </div>
        <h1 id="brand" class="brand-name">MAYANK<br>ANAND</h1>
        <p class="mt-8 text-gray-500 font-medium tracking-[0.2em] uppercase text-xs">Infinity Downloader &bull; 2025 Edition</p>
    </header>

    <div class="max-w-4xl mx-auto space-y-12 mb-20">
        <div class="flex justify-center gap-6">
            <button id="ytBtn" onclick="setSource('youtube')" class="relative group">
                <span id="ytText" class="text-xl font-black opacity-100 group-hover:opacity-100 transition">YOUTUBE</span>
                <div id="ytLine" class="h-1 w-full bg-white mt-1 rounded-full"></div>
            </button>
            <button id="igBtn" onclick="setSource('instagram')" class="relative group opacity-30">
                <span id="igText" class="text-xl font-black transition">INSTAGRAM</span>
                <div id="igLine" class="h-1 w-0 bg-white mt-1 rounded-full transition-all"></div>
            </button>
        </div>

        <div class="glass-panel p-3 flex items-center">
            <input id="searchInput" type="text" placeholder="Enter video link or music name..." 
                   class="flex-1 bg-transparent py-6 px-8 outline-none text-2xl font-bold placeholder:text-gray-700">
            <button onclick="initSearch(false)" class="glow-btn p-6 rounded-[2rem]">
                <i data-lucide="search" class="w-8 h-8"></i>
            </button>
        </div>
    </div>

    <div id="loader" class="hidden flex flex-col items-center py-20">
        <div class="w-16 h-16 border-4 border-white/5 border-t-[var(--glow)] rounded-full animate-spin"></div>
    </div>

    <div id="resultsGrid" class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 px-4"></div>

    <div id="loadMore" class="hidden text-center mt-20">
        <button onclick="initSearch(true)" class="px-12 py-5 rounded-full border border-white/10 hover:bg-white/5 transition font-bold tracking-widest text-xs">
            LOAD MORE DISCOVERIES
        </button>
    </div>

    <div id="modal" class="hidden fixed inset-0 bg-black/95 backdrop-blur-3xl flex items-center justify-center p-6 z-[60]">
        <div class="glass-panel max-w-2xl w-full p-12 relative overflow-hidden">
            <button onclick="closeModal()" class="absolute top-10 right-10 opacity-30 hover:opacity-100"><i data-lucide="x-circle"></i></button>
            
            <div class="flex flex-col md:flex-row gap-10">
                <img id="modalThumb" class="w-full md:w-64 h-64 object-cover rounded-[2.5rem] shadow-2xl">
                <div class="flex-1 flex flex-col justify-center">
                    <h2 id="modalTitle" class="text-3xl font-black mb-6 leading-tight"></h2>
                    
                    <div class="flex gap-4 mb-8">
                        <button id="modeVid" onclick="setMode('video')" class="flex-1 py-4 rounded-2xl bg-white/10 border border-white/10 font-bold">Video</button>
                        <button id="modeAud" onclick="setMode('audio')" class="flex-1 py-4 rounded-2xl border border-white/10 opacity-40 font-bold">MP3 Audio</button>
                    </div>

                    <select id="qualitySelect" class="w-full bg-white/5 border border-white/10 rounded-2xl p-5 mb-8 outline-none font-bold text-lg"></select>
                    
                    <button onclick="fireDownload()" class="glow-btn w-full py-6 rounded-2xl text-xl flex items-center justify-center gap-4">
                        <i data-lucide="zap"></i> INSTANT SAVE
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        lucide.createIcons();
        let source = 'youtube';
        let mode = 'video';
        let page = 1;
        let activeItem = null;
        let fetchedFormats = [];

        function changeStyle(font, color) {
            document.documentElement.style.setProperty('--glow', color);
            document.documentElement.style.setProperty('--font-main', font);
            document.body.style.fontFamily = font;
        }

        function setSource(s) {
            source = s;
            document.getElementById('ytBtn').style.opacity = s === 'youtube' ? '1' : '0.3';
            document.getElementById('igBtn').style.opacity = s === 'instagram' ? '1' : '0.3';
            document.getElementById('ytLine').style.width = s === 'youtube' ? '100%' : '0';
            document.getElementById('igLine').style.width = s === 'instagram' ? '100%' : '0';
        }

        function setMode(m) {
            mode = m;
            document.getElementById('modeVid').style.opacity = m === 'video' ? '1' : '0.4';
            document.getElementById('modeVid').style.background = m === 'video' ? 'rgba(255,255,255,0.1)' : 'transparent';
            document.getElementById('modeAud').style.opacity = m === 'audio' ? '1' : '0.4';
            document.getElementById('modeAud').style.background = m === 'audio' ? 'rgba(255,255,255,0.1)' : 'transparent';
            updateSelection();
        }

        async function initSearch(more) {
            const q = document.getElementById('searchInput').value;
            if(!q) return;
            if(!more) { page = 1; document.getElementById('resultsGrid').innerHTML = ''; } else { page++; }
            document.getElementById('loader').classList.remove('hidden');
            
            try {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}&source=${source}&page=${page}`);
                const data = await res.json();
                data.forEach(v => {
                    const card = document.createElement('div');
                    card.className = "result-card p-6 cursor-pointer";
                    card.onclick = () => openModal(v);
                    card.innerHTML = `
                        <div class="overflow-hidden rounded-2xl mb-6 h-40">
                            <img src="${v.thumbnail}" class="w-full h-full object-cover">
                        </div>
                        <h3 class="font-bold text-sm line-clamp-2">${v.title}</h3>
                        <p class="text-[9px] opacity-40 mt-4 tracking-widest uppercase font-black">${v.channel || 'Official'}</p>
                    `;
                    document.getElementById('resultsGrid').appendChild(card);
                });
                document.getElementById('loadMore').classList.remove('hidden');
            } catch(e) { alert("Search Error"); }
            finally { document.getElementById('loader').classList.add('hidden'); }
        }

        async function openModal(v) {
            activeItem = v;
            document.getElementById('modalTitle').innerText = v.title;
            document.getElementById('modalThumb').src = v.thumbnail;
            document.getElementById('modal').classList.remove('hidden');
            
            const res = await fetch(`/info?url=${encodeURIComponent(v.url)}`);
            fetchedFormats = await res.json();
            updateSelection();
        }

        function updateSelection() {
            const sel = document.getElementById('qualitySelect');
            sel.innerHTML = '';
            const list = mode === 'video' ? fetchedFormats.video : fetchedFormats.audio;
            list.forEach(f => {
                sel.innerHTML += `<option value="${f.id}">${f.res || f.note || 'Best Stream'}</option>`;
            });
        }

        function closeModal() { document.getElementById('modal').classList.add('hidden'); }

        function fireDownload() {
            const fmt = document.getElementById('qualitySelect').value;
            window.location.href = `/download?url=${encodeURIComponent(activeItem.url)}&format_id=${fmt}&mode=${mode}`;
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
    stype = f"ytsearch{count}:{q}" if "http" not in q else q
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(stype, download=False)
        entries = info.get('entries', [info])
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
        video, audio, seen_v = [], [], set()
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
    ydl_opts = {
        'format': f"{format_id}+bestaudio/best" if mode == 'video' else 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s"),
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}] if mode == 'audio' else []
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{info.get('title')}.{'mp3' if mode == 'audio' else 'mp4'}"
        actual_path = ""
        for f in os.listdir(DOWNLOAD_DIR):
            if file_id in f: actual_path = os.path.join(DOWNLOAD_DIR, f)
        return FileResponse(path=actual_path, filename=filename)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
