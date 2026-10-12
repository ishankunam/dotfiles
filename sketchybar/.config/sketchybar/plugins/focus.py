"""Read the enabled Focus without writing the protected macOS database.

Private schema reference: https://github.com/eugenehp/macos-focus/blob/main/src/macos/database.rs
Apple can change this schema. Unreadable data is distinct from Focus being off.
"""
import json
import os
from pathlib import Path
import subprocess


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


def mode_name(document, identifier):
    for store in document['data']:
        configuration = store['modeConfigurations'].get(identifier)
        if configuration:
            name = configuration['mode']['name']
            if isinstance(name, str) and name.strip():
                return name.strip()
    raise ValueError('Missing configured Focus name')


def read_focus(folder):
    try:
        identifier = active_identifier(json.loads((folder / 'Assertions.json').read_text()))
        if identifier is None:
            return {'state': 'off', 'name': None}
        name = mode_name(json.loads((folder / 'ModeConfigurations.json').read_text()), identifier)
        return {'state': 'on', 'name': name}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {'state': 'unavailable', 'name': None}


def main():
    focus = read_focus(Path.home() / 'Library/DoNotDisturb/DB')
    name = focus['name'] if focus['state'] == 'on' else 'Focus unavailable'
    subprocess.run(['sketchybar', '--set', os.environ.get('NAME', 'focus'),
                    'drawing=' + ('off' if focus['state'] == 'off' else 'on'),
                    'label=' + name], check=True, timeout=3)


if __name__ == '__main__':
    main()
