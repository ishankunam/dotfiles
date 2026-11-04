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

BAR = os.environ.get('BAR_NAME', 'sketchybar')
SOURCE = Path(__file__).with_name('calendar_image.swift')
CACHE = Path.home() / 'Library/Caches/sketchybar-calendar'


def bar(*arguments):
    return subprocess.check_output([BAR, *arguments], text=True)


def query(name):
    return json.loads(bar('--query', name))


def render(year, month, renderer):
    today = datetime.date.today()
    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)
    model = {
        'title': f'{calendar.month_name[month]} {year}',
        'weeks': [[day.day if day.month == month else 0 for day in week] for week in weeks],
        'numbers': [week[4].isocalendar().week for week in weeks],
        'today': today.day if (year, month) == (today.year, today.month) else 0,
    }
    # A fresh path also invalidates SketchyBar's image cache.
    with tempfile.NamedTemporaryFile(dir=CACHE, suffix='.png', delete=False) as image:
        path = image.name
    try:
        subprocess.run([str(renderer), json.dumps(model), path], check=True)
        height = 78 + 28 * len(weeks)
        command = f'python3 {shlex.quote(str(Path(__file__).resolve()))} click {year} {month}'
        bar('--set', 'clock', f'popup.height={height}',
            '--set', 'calendar.month', f'background.image={path}',
            f'click_script={command}', '--set', 'clock', 'popup.drawing=on')
    finally:
        Path(path).unlink(missing_ok=True)


def main():
    action = sys.argv[1]
    if action == 'close':
        bar('--set', 'clock', 'popup.drawing=off')
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / 'lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if action == 'toggle' and query('clock')['popup']['drawing'] == 'on':
            bar('--set', 'clock', 'popup.drawing=off')
            return
        renderer = CACHE / 'calendar-image'
        if not renderer.exists() or renderer.stat().st_mtime < SOURCE.stat().st_mtime:
            subprocess.run(['swiftc', str(SOURCE), '-o', str(renderer)], check=True)
        today = datetime.date.today()
        year, month = today.year, today.month
        if action == 'click':
            year, month = map(int, sys.argv[2:4])
            x, y = map(float, subprocess.check_output([str(renderer), 'pointer'], text=True).split())
            rectangles = query('calendar.month')['bounding_rects'].values()
            for rect in rectangles:
                left, top = rect['origin']
                width, height = rect['size']
                if left <= x < left + width and top <= y < top + height:
                    local_x = x - left - (width - 280) / 2
                    local_y = y - top
                    if not 8 <= local_y <= 42:
                        return
                    if local_x < 42:
                        offset = year * 12 + month - 2
                    elif local_x > 238:
                        offset = year * 12 + month
                    else:
                        offset = today.year * 12 + today.month - 1
                    year, month = offset // 12, offset % 12 + 1
                    break
            else:
                return
        if 2 <= year <= 9998:
            render(year, month, renderer)


if __name__ == '__main__':
    main()
