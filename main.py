import subprocess
import sys
import os
import time
import shutil
from PIL import Image

# ── CONFIG ────────────────────────────────────────────────────
ASCII_CHARS = ' `.\':;!|/\\(){}[]?-_+~<>i1lItzJYLCQ0OZmwqpdbkhao*#MW&8%B@$'
FRAME_WIDTH  = 120
FRAME_HEIGHT = 38
TEMP_DIR     = './ascii_frames_temp'
FPS          = 10

# ── ANSI ──────────────────────────────────────────────────────
RESET = '\x1b[0m'
BOLD  = '\x1b[1m'

def rgb(r, g, b):
    return f'\x1b[38;2;{r};{g};{b}m'

def cursor_up(n):
    return f'\x1b[{n}A'

def clear_line():
    return '\x1b[2K'

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

def blood_red(i, total):
    t = i / max(total - 1, 1)
    r = int(120 + t * 80)
    g = int(t * 10)
    return rgb(r, g, 0)

# ── PRINT CREDIT ──────────────────────────────────────────────
def print_credit():
    sys.stdout.write('\n' * 50)
    sys.stdout.flush()
    for i, line in enumerate(CREDIT_LINES):
        sys.stdout.write(BOLD + blood_red(i, len(CREDIT_LINES)) + line + RESET + '\n')
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write('\n')
    sys.stdout.flush()
    time.sleep(0.9)

# ── PIXEL → ASCII BERWARNA ────────────────────────────────────
def pixel_to_colored(r, g, b):
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    idx = int((lum / 255) * (len(ASCII_CHARS) - 1))
    return rgb(r, g, b) + ASCII_CHARS[idx]

def image_to_ascii_rows(img_path):
    img = Image.open(img_path).resize((FRAME_WIDTH, FRAME_HEIGHT))
    img = img.convert('RGB')
    rows = []
    for y in range(FRAME_HEIGHT):
        row = ''
        for x in range(FRAME_WIDTH):
            r, g, b = img.getpixel((x, y))
            row += pixel_to_colored(r, g, b)
        row += RESET
        rows.append(row)
    return rows

# ── EXTRACT FRAMES ────────────────────────────────────────────
def extract_frames(video_path):
    os.makedirs(TEMP_DIR, exist_ok=True)
    sys.stdout.write(rgb(255, 180, 0) + '[*] extracting frames...' + RESET + '\n')
    sys.stdout.flush()

    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f'fps={FPS},scale={FRAME_WIDTH * 6}:{FRAME_HEIGHT * 14}',
        f'{TEMP_DIR}/frame-%04d.png',
        '-y', '-loglevel', 'quiet'
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.stdout.write(rgb(255, 50, 50) + '[!] ffmpeg error' + RESET + '\n')
        sys.exit(1)

    sys.stdout.write(rgb(0, 220, 80) + '[done] frames extracted' + RESET + '\n')
    sys.stdout.flush()

def get_duration(video_path):
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'compact',
         '-show_entries', 'format=duration', video_path],
        capture_output=True, text=True
    )
    for line in result.stdout.split('\n'):
        if 'duration' in line:
            try:
                return float(line.split('=')[1])
            except:
                pass
    return 0

# ── PLAY FRAMES ───────────────────────────────────────────────
def play_ascii_frames():
    frames = sorted([
        f for f in os.listdir(TEMP_DIR) if f.endswith('.png')
    ])

    if not frames:
        sys.stdout.write(rgb(255, 50, 50) + '[!] tidak ada frame' + RESET + '\n')
        return

    delay = 1 / FPS
    total = len(frames)
    total_lines = FRAME_HEIGHT + 1  # header + rows

    # Pre-render semua frame
    sys.stdout.write(rgb(255, 180, 0) + '[*] pre-rendering...' + RESET + '\n')
    sys.stdout.flush()
    rendered = []
    for i, fname in enumerate(frames):
        rendered.append(image_to_ascii_rows(os.path.join(TEMP_DIR, fname)))
        if i % 10 == 0:
            sys.stdout.write(f'\r{rgb(80,80,80)}rendering {i+1}/{total}{RESET}')
            sys.stdout.flush()
    sys.stdout.write('\n' + rgb(0, 220, 80) + '[done] siap diputar' + RESET + '\n')
    sys.stdout.flush()
    time.sleep(0.5)

    # Frame pertama: print biasa
    sys.stdout.write(rgb(80, 80, 80) + f'frame 1/{total} | by daffa' + RESET + '\n')
    for row in rendered[0]:
        sys.stdout.write(row + '\n')
    sys.stdout.flush()

    time.sleep(0.3)

    # Frame berikutnya: overwrite dengan cursor up
    for i in range(1, len(rendered)):
        rows = rendered[i]

        buf = cursor_up(total_lines)
        buf += '\r' + clear_line() + rgb(80, 80, 80) + f'frame {i+1}/{total} | by daffa' + RESET + '\n'
        for row in rows:
            buf += '\r' + clear_line() + row + '\n'

        sys.stdout.write(buf)
        sys.stdout.flush()
        time.sleep(delay)

    # Credit akhir
    time.sleep(0.3)
    sys.stdout.write('\n' + rgb(80, 80, 80) + '-- end --' + RESET + '\n\n')
    for i, line in enumerate(CREDIT_LINES):
        sys.stdout.write(BOLD + blood_red(i, len(CREDIT_LINES)) + line + RESET + '\n')
    sys.stdout.write('\n')
    sys.stdout.flush()

# ── CLEANUP ───────────────────────────────────────────────────
def cleanup():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

# ── DOWNLOAD VIDEO ────────────────────────────────────────────
def download_video(url):
    if shutil.which('yt-dlp') is None:
        sys.stdout.write(rgb(255, 50, 50) + '[!] install yt-dlp: pip install yt-dlp' + RESET + '\n')
        sys.exit(1)
    out = './downloaded_video.mp4'
    sys.stdout.write(rgb(255, 180, 0) + '[*] downloading...' + RESET + '\n')
    sys.stdout.flush()
    subprocess.run(
        ['yt-dlp', '-f', 'best[ext=mp4]/best', '-o', out, url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    sys.stdout.write(rgb(0, 220, 80) + '[done]' + RESET + '\n')
    sys.stdout.flush()
    return out

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print_credit()

    if len(sys.argv) < 2:
        video_input = 'lv_7536120511777017141_20250810190439.mp4'
    else:
        video_input = sys.argv[1]
    video_path  = video_input

    try:
        if video_input.startswith('http://') or video_input.startswith('https://'):
            video_path = download_video(video_input)

        if not os.path.exists(video_path):
            sys.stdout.write(rgb(255, 50, 50) + f'[!] file tidak ada: {video_path}' + RESET + '\n')
            sys.exit(1)

        duration = get_duration(video_path)
        sys.stdout.write(rgb(0, 180, 255) + f'[i] durasi: {round(duration)}s | fps: {FPS}' + RESET + '\n')
        sys.stdout.flush()

        extract_frames(video_path)
        play_ascii_frames()
        cleanup()

    except KeyboardInterrupt:
        sys.stdout.write('\n' + rgb(255, 50, 50) + '[!] dihentikan' + RESET + '\n')
        cleanup()
    except Exception as e:
        sys.stdout.write(rgb(255, 50, 50) + f'[error] {e}' + RESET + '\n')
        cleanup()
        sys.exit(1)

if __name__ == '__main__':
    main()
