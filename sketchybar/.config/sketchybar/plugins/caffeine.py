"""Show a mug while caffeinate runs. Listen for power events and process exits."""
import argparse
from contextlib import closing
import errno
import fcntl
import hashlib
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys


BAR = os.environ.get('BAR_NAME', 'sketchybar')
ITEM = 'caffeine'


def cache_folder():
    key = hashlib.sha256(BAR.encode()).hexdigest()[:16]
    folder = Path.home() / 'Library/Caches/sketchybar-caffeine' / key
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    return folder


def process_ids(name, oldest=False):
    command = ['/usr/bin/pgrep', '-x']
    if oldest:
        command.append('-o')
    result = subprocess.run([*command, name], capture_output=True,
                            text=True, timeout=3)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or 'Cannot read process list.')
    return {int(value) for value in result.stdout.split()}


def render_mug():
    source = Path(__file__).with_name('focus_symbol.swift')
    key = hashlib.sha256(source.read_bytes() + b'mug').hexdigest()
    image = cache_folder() / (key + '.png')
    if not image.exists():
        subprocess.run(['/usr/bin/swift', str(source), 'mug', str(image)],
                       capture_output=True, check=True, timeout=30)
    return image


def refresh():
    # Serialize startup/wake readers with the listener. Read inside the lock.
    with (cache_folder() / 'update.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pids = process_ids('caffeinate')
        arguments = ['drawing=' + ('on' if pids else 'off')]
        if pids:
            arguments += ['background.drawing=on', 'background.image=' + str(render_mug()),
                          'background.image.drawing=on']
        subprocess.run([BAR, '--set', ITEM, *arguments], check=True,
                       capture_output=True, timeout=3)
        return pids


def watch_process(queue, pid):
    try:
        queue.control([select.kevent(pid, filter=select.KQ_FILTER_PROC,
                                    flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                    fflags=select.KQ_NOTE_EXIT)], 0, 0)
        return True
    except ProcessLookupError:
        return False


def reconcile(queue, watched):
    try:
        reconcile_processes(queue, watched)
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as error:
        # Reload briefly removes the item. Keep listening through failed reads
        # or bar commands so the next event can recover without a timer.
        print('Caffeine refresh unavailable: ' + str(error), file=sys.stderr)


def reconcile_processes(queue, watched):
    # Watch process exits as well as assertion releases. Timed sessions can
    # release their assertions just before the caffeinate process exits.
    for _ in range(3):
        pids = refresh()
        missing = False
        for pid in pids - watched:
            if watch_process(queue, pid):
                watched.add(pid)
            else:
                missing = True
        if not missing:
            return
    refresh()


def listen():
    with (cache_folder() / 'listener.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        # Command clients have the same name. The server started first.
        bar_pids = process_ids(Path(BAR).name, oldest=True)
        if len(bar_pids) != 1:
            raise RuntimeError('Expected one process for bar ' + BAR)
        bar_pid = bar_pids.pop()
        master, slave = pty.openpty()
        stream = None
        try:
            with closing(select.kqueue()) as queue:
                if not watch_process(queue, bar_pid):
                    return 0
                # A PTY makes pmset flush each event instead of buffering a pipe.
                stream = subprocess.Popen(['/usr/bin/pmset', '-g', 'assertionslog'],
                                          stdin=subprocess.DEVNULL, stdout=slave,
                                          stderr=slave, close_fds=True)
                os.close(slave)
                slave = None
                queue.control([select.kevent(master, filter=select.KQ_FILTER_READ,
                                             flags=select.KQ_EV_ADD)], 0, 0)
                watched = set()
                reconcile(queue, watched)
                pending = ''
                while True:
                    # No timeout and no timer. Sleep until data or a process exit.
                    events = queue.control(None, 16, None)
                    if any(event.filter == select.KQ_FILTER_PROC and
                           event.ident == bar_pid for event in events):
                        return 0
                    changed = False
                    for event in events:
                        if event.filter == select.KQ_FILTER_PROC:
                            watched.discard(event.ident)
                            changed = True
                        elif event.filter == select.KQ_FILTER_READ:
                            try:
                                data = os.read(master, 65536)
                            except OSError as error:
                                if error.errno != errno.EIO:
                                    raise
                                data = b''
                            if not data:
                                raise RuntimeError('The power-event stream stopped. Reload the bar to restart it.')
                            pending += data.decode(errors='replace')
                            lines = pending.split('\n')
                            pending = lines.pop()
                            # The initial marker closes the subscribe/snapshot race.
                            changed |= any('caffeinate command-line tool' in line or
                                           'Showing assertion changes' in line for line in lines)
                    if changed:
                        reconcile(queue, watched)
        finally:
            if slave is not None:
                os.close(slave)
            os.close(master)
            if stream is not None:
                stream.terminate()
                try:
                    stream.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    stream.kill()
                    stream.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listen', action='store_true')
    arguments = parser.parse_args()
    try:
        if arguments.listen:
            # Exit the event loop through finally so pmset is always reaped.
            def stop(signum, frame):
                raise SystemExit(0)
            signal.signal(signal.SIGTERM, stop)
            return listen()
        # Warm the icon even when off so the first start needs no compilation.
        render_mug()
        refresh()
        with (cache_folder() / 'listener.log').open('a') as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--listen'],
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             start_new_session=True, close_fds=True)
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as error:
        # Preserve the last icon if a read fails. Never interpret failure as off.
        print('Caffeine refresh unavailable: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
