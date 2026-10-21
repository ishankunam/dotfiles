"""Event-driven Focus picker. Shortcuts performs the actual macOS Focus toggle."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

import focus


MODES = (
    ('dnd', 'do not disturb', 'moon.fill', '8e80ff'),
    ('silence', 'silence', 'curlybraces', '8b929e'),
    ('in-class', 'in class', 'building.2.fill', 'f39b45'),
    ('work', 'work', 'books.vertical.fill', '8879ff'),
    ('sleep', 'sleep', 'sunset.fill', '27a5ff'),
)
PREFIX = 'focus.mode.'
WHITE = '0xfff5f6f8'
PURPLE = '0xffbd93f9'


def bar(*arguments, query=False):
    result = subprocess.run([os.environ.get('BAR_NAME', 'sketchybar'), *arguments],
                            check=True, capture_output=True, text=True, timeout=3)
    return json.loads(result.stdout) if query else None


def active_mode(saved):
    if saved['state'] != 'on' or saved['image'] is None:
        return None
    try:
        symbol = focus.NATIVE_FOCUS_IMAGES.get(hashlib.sha256(saved['image'].read_bytes()).hexdigest())
    except OSError:
        return None
    return next((mode[0] for mode in MODES if mode[2] == symbol), None)


def badge(symbol, selected_color=None):
    value = symbol + '\t' + (selected_color or '929aa56b')
    return focus.render(Path(__file__).with_name('focus_badge.swift'), value, value.encode())


def command(*arguments):
    return shlex.join([str(Path(__file__).with_name('focus_menu.sh')), *arguments])


def refresh():
    """Create missing popup rows after reload, then update only their icon badges."""
    with (focus.cache_folder() / 'menu.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing = set(bar('--query', 'bar', query=True)['items'])
        selected = active_mode(focus.read_focus())
        arguments = []
        for identifier, name, symbol, color in MODES:
            item = PREFIX + identifier
            image = badge(symbol, color if identifier == selected else None)
            if image is None:
                raise RuntimeError('Cannot render Focus mode: ' + name)
            if item not in existing:
                arguments += ['--add', 'item', item, 'popup.focus', '--set', item,
                              'width=236', 'padding_left=6', 'padding_right=6',
                              'icon=', 'icon.width=24', 'icon.drawing=on',
                              'icon.padding_left=7', 'icon.padding_right=0',
                              'icon.background.drawing=on', 'icon.background.color=0x00000000',
                              'icon.background.image.scale=0.5',
                              'label=' + name, 'label.drawing=on',
                              'label.font=SF Pro:Regular:13.0', 'label.color=' + WHITE,
                              'label.padding_left=8', 'label.padding_right=7',
                              'background.drawing=off', 'background.color=0x29bd93f9',
                              'background.height=24', 'background.corner_radius=5',
                              'background.border_width=0',
                              'background.padding_left=6', 'background.padding_right=6',
                              'update_freq=0', 'updates=on',
                              'script=' + command('hover'),
                              'click_script=' + command('select', identifier),
                              '--subscribe', item, 'mouse.entered', 'mouse.exited']
            arguments += ['--set', item, 'icon.background.image=' + str(image),
                          'icon.background.image.drawing=on']
        if arguments:
            bar(*arguments)


def close():
    arguments = ['--set', 'focus', 'popup.drawing=off']
    for mode in MODES:
        arguments += ['--set', PREFIX + mode[0], 'background.drawing=off', 'label.color=' + WHITE]
    bar(*arguments)


def toggle():
    saved = focus.read_focus()
    # A missing publication or an off state must never expose the picker.
    if saved['state'] != 'on' or saved['image'] is None:
        close()
        return
    refresh()
    arguments = ['--set', 'focus', 'popup.drawing=toggle']
    for mode in MODES:
        arguments += ['--set', PREFIX + mode[0], 'background.drawing=off', 'label.color=' + WHITE]
    bar(*arguments)


def hover():
    item = os.environ.get('NAME', '')
    if item not in {PREFIX + mode[0] for mode in MODES}:
        return
    entered = os.environ.get('SENDER') == 'mouse.entered'
    bar('--set', item, 'background.drawing=' + ('on' if entered else 'off'),
        'label.color=' + (PURPLE if entered else WHITE))


def select(identifier):
    mode = next((mode for mode in MODES if mode[0] == identifier), None)
    if mode is None:
        raise ValueError('Unknown Focus mode.')
    close()
    with (focus.cache_folder() / 'switch.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # Ignore repeated clicks while a previous toggle is running.
        try:
            subprocess.run(['/usr/bin/shortcuts', 'run', 'SketchyBar Focus: ' + mode[1]],
                           check=True, capture_output=True, timeout=30)
        finally:
            # Read the actual state. Never optimistically display the requested mode.
            subprocess.run(['/usr/bin/shortcuts', 'run', 'SketchyBar Focus'],
                           check=True, capture_output=True, timeout=30)
            focus.main('focus')
            refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('refresh', 'toggle', 'close', 'hover', 'select'))
    parser.add_argument('mode', nargs='?', choices=[mode[0] for mode in MODES])
    arguments = parser.parse_args()
    if arguments.action == 'select':
        if arguments.mode is None:
            parser.error('select requires a mode')
        select(arguments.mode)
    else:
        globals()[arguments.action]()
