"""Read the actual Focus icon through Apple's read-only Shortcuts action.

Create SketchyBar Focus with Get Current Focus, then Stop and Output Current Focus.
The CLI converts the Focus object to its configured PNG icon. No output means off.
A fresh output directory prevents an earlier icon from becoming a false reading.
"""
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


def cache_folder():
    folder = Path(tempfile.gettempdir()) / ('sketchybar-focus-' + str(os.getuid()))
    folder.mkdir(mode=0o700, exist_ok=True)
    return folder


def render(source, value, key_bytes):
    try:
        key = hashlib.sha256(key_bytes + source.read_bytes()).hexdigest()
        image = cache_folder() / (key + '.png')
        if not image.exists():
            subprocess.run(['/usr/bin/swift', str(source), value, str(image)], check=True,
                           capture_output=True, timeout=30)
        return image
    except (OSError, subprocess.SubprocessError):
        return None


def render_symbol(symbol):
    return render(Path(__file__).with_name('focus_symbol.swift'), symbol, symbol.encode())


def render_image(image):
    return render(Path(__file__).with_name('focus_image.swift'), str(image), image.read_bytes())


def read_focus():
    try:
        with tempfile.TemporaryDirectory(prefix='sketchybar-focus-read-') as temporary:
            raw = Path(temporary) / 'focus.png'
            subprocess.run(['/usr/bin/shortcuts', 'run', os.environ.get('FOCUS_SHORTCUT', 'SketchyBar Focus'),
                            '--output-path', str(raw), '--output-type', 'public.png'],
                           check=True, capture_output=True, timeout=15)
            if not raw.exists():
                return {'state': 'off', 'image': None}
            if raw.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                raise ValueError('The Focus shortcut did not return a PNG icon.')
            image = render_image(raw)
            if image is None:
                raise ValueError('The configured Focus icon could not be rendered.')
            return {'state': 'on', 'image': image}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'state': 'unavailable', 'image': None}


def display_arguments(focus, image):
    arguments = ['drawing=' + ('off' if focus['state'] == 'off' else 'on'), 'label.drawing=off']
    if image:
        arguments += ['icon.drawing=off', 'background.drawing=on', 'background.image=' + str(image),
                      'background.image.drawing=on']
    else:
        arguments += ['icon=?', 'icon.drawing=on', 'background.drawing=off', 'background.image.drawing=off']
    return arguments


def main():
    focus = read_focus()
    image = focus['image'] if focus['state'] == 'on' else None
    if focus['state'] == 'unavailable':
        image = render_symbol('questionmark.circle')
    subprocess.run([os.environ.get('BAR_NAME', 'sketchybar'), '--set', os.environ.get('NAME', 'focus'),
                    *display_arguments(focus, image)], check=True, timeout=3)


if __name__ == '__main__':
    key = hashlib.sha256(os.environ.get('BAR_NAME', 'sketchybar').encode()).hexdigest()[:16]
    with (cache_folder() / ('poll-' + key + '.lock')).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)
        main()
