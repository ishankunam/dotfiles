#!/usr/bin/env python3
"""Render and navigate the clock's Sunday-first month calendar."""
import calendar
import datetime
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time

BAR = os.environ.get('BAR_NAME', 'sketchybar')
SOURCE = Path(__file__).with_name('calendar_image.swift')
CACHE = Path.home() / 'Library/Caches/sketchybar-calendar'


def bar(*arguments):
    return subprocess.check_output([BAR, *arguments], text=True)


def query(name):
    return json.loads(bar('--query', name))


def render(year, month, renderer, hover=0, pressed=False, opening=False):
    today = datetime.date.today()
    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    model = {
        'hover': hover,
        'pressed': pressed,
        'title': f'{calendar.month_name[month]} {year}',
        'weeks': [[day.day if day.month == month else 0 for day in week] for week in weeks],
        'numbers': [week[4].isocalendar().week for week in weeks],
        'today': today.day if (year, month) == (today.year, today.month) else 0,
    }
    # A fresh path also invalidates SketchyBar's image cache.
    with tempfile.NamedTemporaryFile(dir=CACHE, suffix='.png', delete=False) as image:
        path = image.name
    previous_image = query('calendar.month')['geometry']['background']['image']['value']
    try:
        subprocess.run([str(renderer), json.dumps(model), path], check=True)
        command = f'python3 {shlex.quote(str(Path(__file__).resolve()))} click {year} {month}'
        arguments = ['--set', 'calendar.month', f'background.image={path}',
                     f'click_script={command}', 'background.drawing=on']
        if opening:
            arguments += ['--set', 'clock', 'popup.drawing=on']
        bar(*arguments)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise
    # Retain the active image for redraws; remove only the image it replaced.
    previous_path = Path(previous_image)
    if previous_path.parent == CACHE and previous_path.suffix == '.png':
        previous_path.unlink(missing_ok=True)


def hit(rectangles, x, y, year, month):
    for rect in rectangles:
        left, top = rect['origin']
        x_local, y_local = x - left, y - top
        if not 0 <= x_local < 280:
            continue
        if 11 <= y_local < 39:
            if 12 <= x_local < 38:
                return 1
            if 42 <= x_local < 238:
                return 2
            if 242 <= x_local < 268:
                return 3
        if x_local >= 45 and y_local >= 72:
            row, vertical = divmod(int(y_local) - 72, 28)
            column, horizontal = divmod(int(x_local) - 45, 32)
            day = 1 + 7 * row + column - (datetime.date(year, month, 1).weekday() + 1) % 7
            if column < 7 and horizontal < 26 and vertical < 25 and 1 <= day <= calendar.monthrange(year, month)[1]:
                return day + 3
    return 0


def contains(rectangles, x, y):
    for rect in rectangles:
        left, top = rect['origin']
        width, height = rect['size']
        if left <= x < left + width and top <= y < top + height:
            return True
    return False


def track(renderer):
    # A single watcher survives rapid close/reopen cycles.
    with (CACHE / 'watcher').open('w') as watcher:
        try:
            fcntl.flock(watcher, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        pointer = subprocess.Popen([str(renderer), 'track'], stdout=subprocess.PIPE, text=True)
        previous = None
        last_sample = None
        last_check = 0
        outside_since = None
        try:
            with (CACHE / 'lock').open('w') as lock:
                for sample in pointer.stdout:
                    now = time.monotonic()
                    if sample == last_sample and now - last_check < 0.25:
                        continue
                    last_sample, last_check = sample, now
                    x, y, pressed = map(float, sample.split())
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    try:
                        clock = query('clock')
                        if clock.get('popup', {}).get('drawing') != 'on':
                            return
                        item = query('calendar.month')
                        inside = (contains(clock['bounding_rects'].values(), x, y)
                                  or contains(item['bounding_rects'].values(), x, y))
                        if inside:
                            outside_since = None
                        elif outside_since is None:
                            outside_since = now
                        elif now - outside_since >= 0.3:
                            bar('--set', 'clock', 'popup.drawing=off')
                            return
                        year, month = map(int, shlex.split(item['scripting']['click_script'])[-2:])
                        region = hit(item['bounding_rects'].values(), x, y, year, month)
                        state = (year, month, region, bool(pressed) and 1 <= region <= 3)
                        if state != previous:
                            render(year, month, renderer, *state[2:])
                            previous = state
                    finally:
                        fcntl.flock(lock, fcntl.LOCK_UN)
        finally:
            pointer.terminate()
            pointer.wait()


def main():
    action = sys.argv[1]
    CACHE.mkdir(parents=True, exist_ok=True)
    if action == 'track':
        track(CACHE / 'calendar-image')
        return
    with (CACHE / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == 'close':
            bar('--set', 'clock', 'popup.drawing=off')
            return
        if action == 'open' and query('clock')['popup']['drawing'] == 'on':
            return
        renderer = CACHE / 'calendar-image'
        if not renderer.exists() or renderer.stat().st_mtime < SOURCE.stat().st_mtime:
            subprocess.run(['swiftc', str(SOURCE), '-o', str(renderer)], check=True)
        if action == 'open':
            x, y = map(float, subprocess.check_output([str(renderer), 'pointer'], text=True).split())
            if not contains(query('clock')['bounding_rects'].values(), x, y):
                return
        today = datetime.date.today()
        year, month = today.year, today.month
        if action == 'click':
            year, month = map(int, sys.argv[2:4])
            x, y = map(float, subprocess.check_output([str(renderer), 'pointer'], text=True).split())
            if query('clock')['popup']['drawing'] != 'on':
                return
            item = query('calendar.month')
            if (year, month) != tuple(map(int, shlex.split(item['scripting']['click_script'])[-2:])):
                return
            region = hit(item['bounding_rects'].values(), x, y, year, month)
            if region == 2:
                year, month = today.year, today.month
            elif region in (1, 3):
                offset = year * 12 + month - 1 + (region - 2)
                year, month = offset // 12, offset % 12 + 1
            else:
                return
        if 2 <= year <= 9998:
            render(year, month, renderer, opening=action == 'open')
        if action == 'open':
            subprocess.Popen([sys.executable, __file__, 'track'], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
