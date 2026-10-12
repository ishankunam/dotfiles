"""Read the enabled Focus without writing the protected macOS database.

Private schema reference: https://github.com/eugenehp/macos-focus/blob/main/src/macos/database.rs
Apple can change this schema. Unreadable data is distinct from Focus being off.
"""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


def active_identifier(document):
    stores = document['data']
    if not isinstance(stores, list) or not stores:
        raise ValueError('Unexpected assertion stores')
    records = []
    for store in stores:
        if not isinstance(store, dict):
            raise ValueError('Unexpected assertion store')
        active = store.get('storeAssertionRecords', [])
        if not isinstance(active, list):
            raise ValueError('Unexpected assertions')
        records.extend(active)
    if not records:
        return None
    record = max(records, key=lambda entry: entry.get('assertionStartDateTimestamp', 0))
    identifier = record['assertionDetails']['assertionDetailsModeIdentifier']
    if not isinstance(identifier, str) or not identifier:
        raise ValueError('Missing Focus identifier')
    return identifier


def mode_details(document, identifier):
    for store in document['data']:
        configuration = store['modeConfigurations'].get(identifier)
        if configuration:
            name = configuration['mode']['name']
            if isinstance(name, str) and name.strip():
                symbol = configuration['mode'].get('symbolImageName')
                return {'name': name.strip(), 'symbol': symbol if isinstance(symbol, str) and symbol else None}
    raise ValueError('Missing configured Focus name')


def read_focus(folder):
    try:
        identifier = active_identifier(json.loads((folder / 'Assertions.json').read_text()))
        if identifier is None:
            return {'state': 'off', 'name': None, 'symbol': None}
        mode = mode_details(json.loads((folder / 'ModeConfigurations.json').read_text()), identifier)
        return {'state': 'on', **mode}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'state': 'unavailable', 'name': None, 'symbol': None}


def render_symbol(symbol):
    if not symbol:
        return None
    source = Path(__file__).with_name('focus_symbol.swift')
    try:
        # Cache one image per symbol and renderer revision. Do not launch a GUI.
        key = hashlib.sha256(symbol.encode() + source.read_bytes()).hexdigest()
        folder = Path(tempfile.gettempdir()) / ('sketchybar-focus-' + str(os.getuid()))
        folder.mkdir(mode=0o700, exist_ok=True)
        image = folder / (key + '.png')
        if not image.exists():
            subprocess.run(['/usr/bin/swift', str(source), symbol, str(image)], check=True,
                           capture_output=True, timeout=30)
        return image
    except (OSError, subprocess.SubprocessError):
        return None


def display_arguments(focus, image):
    arguments = ['drawing=' + ('off' if focus['state'] == 'off' else 'on'), 'label.drawing=off']
    if image:
        arguments += ['icon.drawing=off', 'background.drawing=on', 'background.image=' + str(image),
                      'background.image.drawing=on']
    else:
        # A question mark means the state or configured logo could not be read.
        arguments += ['icon=?', 'icon.drawing=on', 'background.drawing=off', 'background.image.drawing=off']
    return arguments


def main():
    focus = read_focus(Path.home() / 'Library/DoNotDisturb/DB')
    symbol = focus['symbol'] if focus['state'] == 'on' else 'questionmark.circle'
    image = render_symbol(symbol) if focus['state'] != 'off' else None
    subprocess.run(['sketchybar', '--set', os.environ.get('NAME', 'focus'),
                    *display_arguments(focus, image)], check=True, timeout=3)


if __name__ == '__main__':
    main()
