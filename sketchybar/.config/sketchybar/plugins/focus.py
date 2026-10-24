"""Display cached Focus state. A Focus automation publishes changes, without polling."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


# Exact PNG fingerprints of this setup's five verified Shortcuts glyphs.
# Unknown or changed glyphs retain their supplied image instead of guessing a mode.
NATIVE_FOCUS_IMAGES = {
    '6354eeab8f80155083e2ad1c5b1840aaa76ca6ec24a28b15c54b640f1e17aa18': 'moon.fill',
    'be5f7311b627b73d5ed78b886017764886d1d9b7ca0857c707d128e7ab663891': 'building.2.fill',
    '99f9220449cb9d270ac2853a9b823ea3e79d5415851799ee4f888bbc606ab41d': 'curlybraces',
    '8e1e3427300cf3ebb4a9cd635ebc63a05488a3cc71d402e85d79af061e5d17a0': 'sunset.fill',
    '2cbc3ac6f29e10388b159b3e4b81e5c75798737ed7f7a348d5f6d914520d484b': 'books.vertical.fill',
}


def cache_folder():
    folder = Path.home() / 'Library/Caches/sketchybar-focus'
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


def native_image(image):
    try:
        symbol = NATIVE_FOCUS_IMAGES.get(hashlib.sha256(image.read_bytes()).hexdigest())
    except OSError:
        return image
    return (render_symbol(symbol) or image) if symbol else image


def read_focus():
    try:
        saved = json.loads((cache_folder() / 'state.json').read_text())
        if saved['version'] != 1 or saved['state'] not in ('on', 'off', 'unavailable'):
            raise ValueError('Unsupported Focus state.')
        image = None
        if saved['state'] == 'on':
            image = Path(saved['image'])
            if image.parent != cache_folder() or image.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                raise ValueError('Missing or invalid cached Focus icon.')
        return {'state': saved['state'], 'image': image}
    except (OSError, ValueError, KeyError, TypeError):
        return {'state': 'unavailable', 'image': None}


def publish_focus(raw=None):
    """Persist first, then notify the bar. A stopped bar can restore this state later."""
    folder = cache_folder()
    with (folder / 'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        focus = {'version': 1, 'state': 'off', 'image': None}
        if raw is not None:
            try:
                if raw.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError('The Focus automation did not provide PNG data.')
                image = render_image(raw)
                if image is None:
                    raise ValueError('Focus icon conversion failed.')
                focus.update(state='on', image=str(image))
            except (OSError, ValueError) as error:
                message = str(error) if isinstance(error, ValueError) else 'Cannot read the Focus icon input.'
                focus.update(state='unavailable', error=message)
        with tempfile.NamedTemporaryFile(mode='w', dir=folder, delete=False) as temporary:
            json.dump(focus, temporary)
        try:
            os.replace(temporary.name, folder / 'state.json')
        finally:
            Path(temporary.name).unlink(missing_ok=True)
        try:
            subprocess.run([os.environ.get('BAR_NAME', 'sketchybar'), '--trigger', 'focus_changed'],
                           check=True, capture_output=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            pass  # Keep the state even when SketchyBar is stopped or restarting.


def publish_image_bytes(data):
    """Read binary PNG input from Shortcuts, rather than interpreting it as a path."""
    with tempfile.TemporaryDirectory(prefix='input-', dir=cache_folder()) as temporary:
        raw = Path(temporary) / 'focus.png'
        raw.write_bytes(data)
        publish_focus(raw)


def display_arguments(focus, image):
    visible = focus['state'] == 'on' and image is not None
    arguments = ['drawing=' + ('on' if visible else 'off'), 'label.drawing=off']
    if not visible:
        arguments += ['popup.drawing=off']
    if image:
        arguments += ['icon.drawing=off', 'background.drawing=on', 'background.image=' + str(image),
                      'background.image.drawing=on']
    else:
        arguments += ['icon=?', 'icon.drawing=on', 'background.drawing=off', 'background.image.drawing=off']
    return arguments


def main(name='focus'):
    # A popup click's inherited NAME must never redirect bar state to a mode row.
    focus = read_focus()
    image = native_image(focus['image']) if focus['state'] == 'on' else None
    subprocess.run([os.environ.get('BAR_NAME', 'sketchybar'), '--set', name,
                    *display_arguments(focus, image)], check=True, timeout=3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    publish = parser.add_mutually_exclusive_group()
    publish.add_argument('--image', type=Path, help='Publish the PNG from the Focus automation.')
    publish.add_argument('--stdin', action='store_true', help='Publish PNG bytes from standard input.')
    publish.add_argument('--off', action='store_true', help='Publish that no Focus is enabled.')
    arguments = parser.parse_args()
    if arguments.stdin:
        publish_image_bytes(sys.stdin.buffer.read())
    elif arguments.image is not None or arguments.off:
        publish_focus(arguments.image)
    else:
        main()
