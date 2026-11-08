#!/usr/bin/env python3
"""Build and send commands to the native SketchyBar calendar panel."""
import fcntl
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time

SOURCE = Path(__file__).resolve().parent
BUILD = SOURCE / 'build' / 'SketchyBar Calendar.app' / 'Contents' / 'MacOS' / 'SketchyBarCalendar'
CACHE = Path.home() / 'Library/Caches/sketchybar-calendar/native'


def running():
    try:
        pid = int((CACHE / 'pid').read_text())
        command = subprocess.check_output(['/bin/ps', '-p', str(pid), '-o', 'command='], text=True).strip()
        return str(BUILD) in command
    except (OSError, ValueError, subprocess.CalledProcessError):
        return False


def main():
    action = sys.argv[1]
    if action not in ('open', 'toggle'):
        raise ValueError('unknown calendar action')
    queue = CACHE / 'commands'
    queue.mkdir(parents=True, exist_ok=True)
    with (CACHE / 'control.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sources = [SOURCE / name for name in ('EventStore.swift', 'main.swift', 'build.sh')]
        if not BUILD.exists() or any(path.stat().st_mtime_ns > BUILD.stat().st_mtime_ns for path in sources):
            # Stop the old helper before replacing its signed app bundle.
            if running():
                os.kill(int((CACHE / 'pid').read_text()), signal.SIGTERM)
                for _ in range(50):
                    if not running():
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError('Calendar helper did not stop for rebuild')
            subprocess.run([str(SOURCE / 'build.sh')], check=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=queue, prefix='.pending-', delete=False) as file:
            file.write(action)
            temp = Path(file.name)
        temp.rename(queue / f'{time.time_ns():020d}-{os.getpid()}.cmd')
        if not running():
            subprocess.Popen([str(BUILD)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            # Serialize startup with later commands until the process publishes its PID.
            for _ in range(100):
                if running():
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError('Calendar helper did not start')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'SketchyBar calendar: {error}', file=sys.stderr)
        sys.exit(1)
