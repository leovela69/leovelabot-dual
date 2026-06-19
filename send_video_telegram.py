# -*- coding: utf-8 -*-
"""Envia el video de C8L Agency al admin via Telegram Bot API."""
import sys, io, os, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

TOKEN = "8557275735:AAFfSXMaxjnSOSJmu-QtN00sZUAwSwIK6Uo"
CHAT_ID = "1970956749"
VIDEO_PATH = r"C:\Users\User\Desktop\canal videos\C8L_10min_telegram.mp4"
VIDEO_ORIGINAL = r"C:\Users\User\Desktop\canal videos\C8L_Agency_Corazones_Locos_10min.mp4"

# Usar el comprimido si existe, sino el original
video_file = VIDEO_PATH if os.path.exists(VIDEO_PATH) else VIDEO_ORIGINAL

if not os.path.exists(video_file):
    print(f"ERROR: No se encontro el video en {video_file}")
    sys.exit(1)

size_mb = os.path.getsize(video_file) / (1024 * 1024)
print(f"Video: {os.path.basename(video_file)} ({size_mb:.1f} MB)")

if size_mb > 50:
    print("El video supera 50 MB. Enviando en partes...")
    # Dividir en 2 partes de 5 minutos
    import subprocess, uuid
    temp_dir = os.path.dirname(video_file)
    
    for i, start in enumerate(["00:00:00", "00:05:00"]):
        part_file = os.path.join(temp_dir, f"_part_{i+1}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", video_file,
            "-ss", start, "-t", "300",
            "-c:v", "libx264", "-preset", "fast", "-crf", "30",
            "-vf", "scale=1280:720",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            part_file
        ]
        subprocess.run(cmd, capture_output=True, timeout=180)
        
        if os.path.exists(part_file):
            part_size = os.path.getsize(part_file) / (1024 * 1024)
            print(f"  Parte {i+1}: {part_size:.1f} MB")
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
            with open(part_file, "rb") as f:
                r = requests.post(url, data={
                    "chat_id": CHAT_ID,
                    "caption": f"🦁 *C8L Agency - Corazones Locos StarMaker*\n📹 Parte {i+1}/2\n🎬 190 imagenes + 2 clips del equipo",
                    "parse_mode": "Markdown",
                    "supports_streaming": "true"
                }, files={"video": (f"C8L_parte_{i+1}.mp4", f, "video/mp4")}, timeout=300)
            
            result = r.json()
            if result.get("ok"):
                print(f"  Parte {i+1} ENVIADA OK")
            else:
                print(f"  ERROR parte {i+1}: {result.get('description', 'unknown')}")
            
            os.remove(part_file)
    
    print("\nTodas las partes enviadas!")
else:
    print(f"Enviando video completo ({size_mb:.1f} MB) a Telegram...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    
    with open(video_file, "rb") as f:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "caption": (
                "🦁 *C8L Agency - Corazones Locos StarMaker*\n\n"
                "📹 Video oficial de la agencia (10 minutos)\n"
                "👑 Leo Vela & Cookies al mando\n"
                "📸 190 imagenes del equipo\n"
                "🎬 2 clips de video incorporados\n\n"
                "🔥 _Generado por los agentes de @LeoVelaBot_"
            ),
            "parse_mode": "Markdown",
            "supports_streaming": "true"
        }, files={"video": ("C8L_Agency_10min.mp4", f, "video/mp4")}, timeout=600)
    
    result = r.json()
    if result.get("ok"):
        print("VIDEO ENVIADO CON EXITO a Telegram!")
        print(f"Message ID: {result['result'].get('message_id')}")
    else:
        print(f"ERROR: {result.get('description', 'unknown error')}")
        # Si falla por tamano, intentar en partes
        if "too big" in str(result).lower() or "413" in str(result):
            print("Video demasiado grande, reintentando en partes...")
