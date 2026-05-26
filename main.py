import subprocess
import sys
import os
import time
import shutil
from PIL import Image

ASCII_CHARS = '@#S%?*+;:,. '  # gelap ke terang, simpel tapi kontras
FRAME_WIDTH  = 80
FRAME_HEIGHT = 40
TEMP_DIR     = './ascii_frames_temp'
FPS          = 10
VIDEO_INPUT  = 'lv_7536120511777017141_20250810190439.mp4'

RESET  = '\x1b[0m'
BOLD   = '\x1b[1m'

# Warna ANSI 256 — works di semua terminal termasuk Termux
# Pake color cube 6x6x6 (kode 16-231)
def ansi256(r, g, b):
    ri = round(r / 255 * 5)
    gi = round(g / 255 * 5)
    bi = round(b / 255 * 5)
    code = 16 + 36 * ri + 6 * gi + bi
    return f'\x1b[38;5;{code}m'

def blood_red(i, total):
    t = i / max(total - 1, 1)
    ri = round((0.4 + t * 0.4) * 5)  # 2 → 4 (merah gelap ke medium)
    code = 16 + 36 * ri
    return f'\x1b[38;5;{code}m'

# ── CREDIT PIXEL FONT ─────────────────────────────────────────
GLYPHS = {
    'B': ['XXXX ','X   X','X   X','XXXX ','X   X','X   X','XXXX '],
    'Y': ['X   X','X   X',' X X ','  X  ','  X  ','  X  ','  X  '],
    ' ': ['     ','     ','     ','     ','     ','     ','     '],
    'D': ['XXXX ','X   X','X   X','X   X','X   X','X   X','XXXX '],
    'A': ['  X  ',' X X ','X   X','XXXXX','X   X','X   X','X   X'],
    'F': ['XXXXX','X    ','X    ','XXXX ','X    ','X    ','X    '],
}

def build_credit(text):
    rows = ['' for _ in range(7)]
    for ch in text:
        g = GLYPHS.get(ch, GLYPHS[' '])
        for r in range(7):
            for px in g[r]:
                rows[r] += '██' if px == 'X' else '  '
            rows[r] += ' '
    return rows

CREDIT_LINES = build_credit('BY DAFFA')

def sleep(ms):
    time.sleep(ms / 1000)

def print_credit():
    sys.stdout.write('\n' * 50)
    sys.stdout.flush()
    for i, line in enumerate(CREDIT_LINES):
        sys.stdout.write(BOLD + blood_red(i, len(CREDIT_LINES)) + line + RESET + '\n')
        sys.stdout.flush()
        sleep(80)
    sys.stdout.write('\n')
    sys.stdout.flush()
    sleep(900)

# ── PIXEL → ASCII ANSI 256 ────────────────────────────────────
def pixel_to_ascii(r, g, b):
    lum = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
    idx = int((lum / 255) * (len(ASCII_CHARS) - 1))
    char = ASCII_CHARS[idx]
    # Double char biar ga terlalu lebar-sempit
    return ansi256(r, g, b) + char + char

def image_to_ascii(img_path):
    img = Image.open(img_path).resize((FRAME_WIDTH, FRAME_HEIGHT)).convert('RGB')
    lines = []
    for y in range(FRAME_HEIGHT):
        row = ''
        for x in range(FRAME_WIDTH):
            r, g, b = img.getpixel((x, y))
            row += pixel_to_ascii(r, g, b)
        row += RESET
        lines.append(row)
    return lines

# ── EXTRACT FRAMES ────────────────────────────────────────────
def extract_frames(video_path):
    os.makedirs(TEMP_DIR, exist_ok=True)
    sys.stdout.write('\x1b[33m[*] extracting frames...\x1b[0m\n')
    sys.stdout.flush()
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f'fps={FPS},scale={FRAME_WIDTH * 2}:{FRAME_HEIGHT}',
        f'{TEMP_DIR}/frame-%04d.png',
        '-y', '-loglevel', 'quiet'
    ]
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.stdout.write('\x1b[31m[!] ffmpeg error\x1b[0m\n')
        sys.exit(1)
    sys.stdout.write('\x1b[32m[done]\x1b[0m\n')
    sys.stdout.flush()

def get_duration(video_path):
    r = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'compact',
         '-show_entries', 'format=duration', video_path],
        capture_output=True, text=True
    )
    for line in r.stdout.split('\n'):
        if 'duration' in line:
            try: return float(line.split('=')[1])
            except: pass
    return 0

# ── PLAY ──────────────────────────────────────────────────────
def play_frames():
    frames = sorted([f for f in os.listdir(TEMP_DIR) if f.endswith('.png')])
    if not frames:
        sys.stdout.write('\x1b[31m[!] tidak ada frame\x1b[0m\n')
        return

    total = len(frames)
    delay = 1 / FPS

    # Pre-render
    sys.stdout.write('\x1b[33m[*] pre-rendering...\x1b[0m\n')
    sys.stdout.flush()
    rendered = []
    for i, f in enumerate(frames):
        rendered.append(image_to_ascii(os.path.join(TEMP_DIR, f)))
        if i % 20 == 0:
            sys.stdout.write(f'\r\x1b[90mrendering {i+1}/{total}\x1b[0m')
            sys.stdout.flush()
    sys.stdout.write(f'\n\x1b[32m[done] {total} frames siap\x1b[0m\n')
    sys.stdout.flush()
    sleep(500)

    TOTAL_LINES = FRAME_HEIGHT + 1

    # Frame pertama
    sys.stdout.write(f'\x1b[90mframe 1/{total} | by daffa\x1b[0m\n')
    for row in rendered[0]:
        sys.stdout.write(row + '\n')
    sys.stdout.flush()
    sleep(200)

    # Frame berikutnya: overwrite
    for i in range(1, total):
        # Naik ke atas
        buf = f'\x1b[{TOTAL_LINES}A'
        buf += f'\r\x1b[2K\x1b[90mframe {i+1}/{total} | by daffa\x1b[0m\n'
        for row in rendered[i]:
            buf += '\r\x1b[2K' + row + '\n'
        sys.stdout.write(buf)
        sys.stdout.flush()
        time.sleep(delay)

    # Credit akhir
    sleep(300)
    sys.stdout.write('\n\x1b[90m-- end --\x1b[0m\n\n')
    for i, line in enumerate(CREDIT_LINES):
        sys.stdout.write(BOLD + blood_red(i, len(CREDIT_LINES)) + line + RESET + '\n')
    sys.stdout.write('\n')
    sys.stdout.flush()

def cleanup():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

def download_video(url):
    if not shutil.which('yt-dlp'):
        sys.stdout.write('\x1b[31m[!] install yt-dlp: pip install yt-dlp\x1b[0m\n')
        sys.exit(1)
    out = './downloaded_video.mp4'
    sys.stdout.write('\x1b[33m[*] downloading...\x1b[0m\n')
    sys.stdout.flush()
    subprocess.run(['yt-dlp', '-f', 'best[ext=mp4]/best', '-o', out, url],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.stdout.write('\x1b[32m[done]\x1b[0m\n')
    sys.stdout.flush()
    return out

def main():
    print_credit()

    video_path = sys.argv[1] if len(sys.argv) >= 2 else VIDEO_INPUT

    try:
        if video_path.startswith('http://') or video_path.startswith('https://'):
            video_path = download_video(video_path)

        if not os.path.exists(video_path):
            sys.stdout.write(f'\x1b[31m[!] file tidak ada: {video_path}\x1b[0m\n')
            sys.exit(1)

        dur = get_duration(video_path)
        sys.stdout.write(f'\x1b[96m[i] durasi: {round(dur)}s | fps: {FPS}\x1b[0m\n')
        sys.stdout.flush()

        extract_frames(video_path)
        play_frames()
        cleanup()

    except KeyboardInterrupt:
        sys.stdout.write('\n\x1b[31m[stop]\x1b[0m\n')
        cleanup()
    except Exception as e:
        sys.stdout.write(f'\x1b[31m[error] {e}\x1b[0m\n')
        cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main()
