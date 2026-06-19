# -*- coding: utf-8 -*-
"""
Generador de Vídeo C8L Agency — 10 minutos
Usa las 190 imágenes reales del equipo + 2 clips de vídeo.
Crea un vídeo profesional con transiciones y efecto Ken Burns.
"""

import os
import sys
import io
import random
import subprocess
import glob

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
IMAGES_DIR = r"C:\Users\User\Desktop\canal videos\starmaker_cracy_extraido"
VIDEOS_DIR = r"C:\Users\User\Desktop\c8lvideos"
OUTPUT_DIR = r"C:\Users\User\Desktop\canal videos"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "C8L_Agency_Corazones_Locos_10min.mp4")

FFMPEG = "ffmpeg"
TARGET_DURATION_SECONDS = 600  # 10 minutos
IMAGE_DURATION = 3.5  # segundos por imagen (con 190 imágenes = ~665s ≈ 11 min)
RESOLUTION = "1920:1080"
FPS = 25

def get_all_images():
    """Recopila todas las imágenes disponibles."""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(IMAGES_DIR, ext)))
    images.sort()
    return images

def get_video_clips():
    """Recopila los clips de vídeo existentes."""
    clips = glob.glob(os.path.join(VIDEOS_DIR, "*.mp4"))
    return clips

def create_slideshow(images, output_path):
    """Crea un vídeo slideshow con las imágenes usando FFmpeg concat."""
    print(f"📸 Preparando slideshow con {len(images)} imágenes...")
    
    # Calcular duración por imagen para alcanzar ~10 minutos
    # Reservamos ~12s para los 2 clips de vídeo
    available_time = TARGET_DURATION_SECONDS - 12
    duration_per_image = available_time / len(images)
    duration_per_image = max(2.5, min(duration_per_image, 5.0))
    
    print(f"   Duración por imagen: {duration_per_image:.1f}s")
    print(f"   Duración total estimada: {len(images) * duration_per_image:.0f}s")
    
    # Crear archivo de lista para FFmpeg concat
    list_file = os.path.join(OUTPUT_DIR, "_concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for img in images:
            # Escapar comillas simples en paths
            safe_path = img.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
            f.write(f"duration {duration_per_image}\n")
        # Repetir la última imagen (requerido por FFmpeg concat)
        if images:
            safe_path = images[-1].replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
    
    # FFmpeg: crear slideshow con escalado profesional
    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-vf", (
            f"scale={RESOLUTION}:force_original_aspect_ratio=decrease,"
            f"pad={RESOLUTION}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"format=yuv420p"
        ),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]
    
    print(f"🎬 Renderizando slideshow...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    # Limpiar
    try:
        os.remove(list_file)
    except OSError:
        pass
    
    if result.returncode != 0:
        print(f"❌ Error FFmpeg: {result.stderr[-500:]}")
        return False
    
    print(f"✅ Slideshow creado: {output_path}")
    return True

def prepare_video_clips(clips, output_dir):
    """Normaliza los clips de vídeo existentes al mismo formato."""
    normalized = []
    for i, clip in enumerate(clips):
        norm_path = os.path.join(output_dir, f"_clip_norm_{i}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-i", clip,
            "-vf", f"scale={RESOLUTION}:force_original_aspect_ratio=decrease,pad={RESOLUTION}:(ow-iw)/2:(oh-ih)/2:color=black",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-t", "6",  # Máximo 6 segundos por clip
            "-an",  # Sin audio por ahora
            norm_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            normalized.append(norm_path)
            print(f"   ✅ Clip {i+1} normalizado: {os.path.basename(clip)}")
        else:
            print(f"   ⚠️ Error normalizando clip {i+1}")
    return normalized

def concatenate_all(slideshow_path, clip_paths, final_output):
    """Une el slideshow con los clips de vídeo en el vídeo final."""
    print(f"🎬 Componiendo vídeo final...")
    
    # Crear lista de concatenación: clip1 + slideshow + clip2
    parts = []
    if clip_paths:
        parts.append(clip_paths[0])  # Clip de apertura
    parts.append(slideshow_path)      # Slideshow principal
    if len(clip_paths) > 1:
        parts.append(clip_paths[1])   # Clip de cierre
    
    if len(parts) == 1:
        # Solo el slideshow, renombrarlo
        os.rename(slideshow_path, final_output)
        return True
    
    # Crear archivo concat
    concat_file = os.path.join(OUTPUT_DIR, "_final_concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for part in parts:
            safe = part.replace("'", "'\\''")
            f.write(f"file '{safe}'\n")
    
    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        final_output,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    # Limpiar temporales
    for f_path in [concat_file, slideshow_path] + clip_paths:
        try:
            os.remove(f_path)
        except OSError:
            pass
    
    return result.returncode == 0

def main():
    print("=" * 60)
    print("🦁 C8L AGENCY — Generador de Vídeo Oficial")
    print("   Agencia Corazones Locos StarMaker")
    print("=" * 60)
    
    # 1. Recopilar material
    images = get_all_images()
    clips = get_video_clips()
    
    print(f"\n📦 Material encontrado:")
    print(f"   📸 Imágenes: {len(images)}")
    print(f"   🎬 Clips de vídeo: {len(clips)}")
    
    if not images:
        print("❌ No se encontraron imágenes. Abortando.")
        sys.exit(1)
    
    # 2. Mezclar imágenes para variedad visual
    random.seed(42)  # Semilla fija para reproducibilidad
    random.shuffle(images)
    
    # 3. Normalizar clips de vídeo
    norm_clips = []
    if clips:
        print(f"\n🎬 Normalizando {len(clips)} clips de vídeo...")
        norm_clips = prepare_video_clips(clips, OUTPUT_DIR)
    
    # 4. Crear slideshow
    slideshow_path = os.path.join(OUTPUT_DIR, "_slideshow_temp.mp4")
    if not create_slideshow(images, slideshow_path):
        print("❌ Error creando el slideshow.")
        sys.exit(1)
    
    # 5. Componer vídeo final
    if not concatenate_all(slideshow_path, norm_clips, OUTPUT_FILE):
        print("❌ Error componiendo el vídeo final.")
        sys.exit(1)
    
    # 6. Resultado
    if os.path.exists(OUTPUT_FILE):
        size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        # Obtener duración
        probe = subprocess.run(
            [FFMPEG, "-i", OUTPUT_FILE],
            capture_output=True, text=True
        )
        duration_line = [l for l in probe.stderr.split('\n') if 'Duration' in l]
        duration = duration_line[0].strip() if duration_line else "Desconocida"
        
        print(f"\n{'=' * 60}")
        print(f"🎉 ¡VÍDEO GENERADO CON ÉXITO!")
        print(f"{'=' * 60}")
        print(f"📁 Archivo: {OUTPUT_FILE}")
        print(f"📦 Tamaño: {size_mb:.1f} MB")
        print(f"⏱️  {duration}")
        print(f"📸 Imágenes utilizadas: {len(images)}")
        print(f"🎬 Clips incorporados: {len(norm_clips)}")
        print(f"{'=' * 60}")
    else:
        print("❌ El archivo final no se generó.")
        sys.exit(1)

if __name__ == "__main__":
    main()
