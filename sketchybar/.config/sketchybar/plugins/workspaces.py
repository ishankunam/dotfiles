"""Reconcile AeroSpace items without launching or reloading either service."""
import fcntl
import json
import os
import shlex
import subprocess
import sys
import tempfile


def output(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=3).stdout


def item_name(workspace):
    # Encode names so they cannot become item/regex syntax.
    return 'space.' + workspace.encode('utf-8').hex()


def reconcile(workspaces, focused, items, group):
    wanted = [item_name(workspace) for workspace in workspaces]
    existing = [item for item in items if item.startswith('space.')]
    changed = existing != wanted or ('spaces' not in items and bool(wanted))
    commands = []
    if changed and 'spaces' in items:
        commands += ['--remove', 'spaces']
    for item in existing:
        if item not in wanted:
            commands += ['--remove', item]
    for workspace, item in zip(workspaces, wanted):
        if item not in existing:
            commands += ['--clone', item, 'workspace_template', '--set', item,
                         'drawing=on', 'icon=' + workspace,
                         'click_script=aerospace workspace ' + shlex.quote(workspace)]
        if changed:
            commands += ['--move', item, 'before', 'front_app']
        selected = 'on' if workspace == focused else 'off'
        commands += ['--set', item, 'background.drawing=' + selected, 'icon.highlight=' + selected]
    if changed and wanted:
        commands += ['--add', 'bracket', 'spaces', *wanted, '--set', 'spaces', *group]
    return commands


def main():
    try:
        workspaces = list(dict.fromkeys(output('aerospace', 'list-workspaces', '--all').splitlines()))
        focused = output('aerospace', 'list-workspaces', '--focused').strip()
        bar = os.environ.get('BAR_NAME', 'sketchybar')
        items = json.loads(output(bar, '--query', 'bar'))['items']
        if not workspaces or focused not in workspaces or not isinstance(items, list):
            raise ValueError('Incomplete workspace snapshot')
        if not all(isinstance(item, str) for item in items):
            raise ValueError('Unexpected SketchyBar item list')
        commands = reconcile(workspaces, focused, items, sys.argv[1:])
        if commands:
            output(bar, *commands)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        # Keep the last contents while a service is unavailable or restarting.
        print('Workspace refresh unavailable: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    # Events and the fallback timer can arrive together. Reconcile once at a time.
    with open(os.path.join(tempfile.gettempdir(), 'sketchybar-workspaces-' + str(os.getuid()) + '.lock'), 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit(0)
        sys.exit(main())
