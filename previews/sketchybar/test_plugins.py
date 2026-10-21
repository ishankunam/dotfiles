"""Fixture checks. No native service calls or Focus database access."""
import contextlib
import fcntl
import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

PLUGINS = Path(__file__).resolve().parents[2] / 'sketchybar/.config/sketchybar/plugins'


def module(name):
    spec = importlib.util.spec_from_file_location(name, PLUGINS / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


workspaces, focus, caffeine = module('workspaces'), module('focus'), module('caffeine')


class Plugins(unittest.TestCase):
    def test_config_commands_without_contacting_services(self):
        script = 'sketchybar(){ printf "%s\\0" "$@"; printf "\\1"; }; source "$1"'
        config = PLUGINS.parent / 'sketchybarrc'
        result = subprocess.run(['/bin/bash', '-c', script, 'fixture', str(config)], env={'CONFIG_DIR': '/fixture', 'PATH': '/usr/bin:/bin'}, capture_output=True, check=True)
        commands = [command.decode().split('\0')[:-1] for command in result.stdout.split(b'\1') if command]
        flat = [argument for command in commands for argument in command]
        self.assertNotIn('battery', flat)
        self.assertNotIn('volume', flat)
        self.assertNotIn('yabai', flat)
        self.assertNotIn('chevron', flat)
        self.assertIn('label.font=IBM Plex Mono:Medium:14.0', flat)
        self.assertIn(['--set', 'clock', 'update_freq=10', 'icon.drawing=off'], [flat[i:i+4] for i in range(len(flat))])
        self.assertIn(['--add', 'bracket', 'status', 'focus', 'caffeine', 'clock'], [flat[i:i+6] for i in range(len(flat))])
        self.assertIn(['--subscribe', 'caffeine', 'system_woke'], [flat[i:i+3] for i in range(len(flat))])
        self.assertIn('update_freq=0', flat)
        self.assertIn(['--subscribe', 'focus', 'focus_changed', 'system_woke'], [flat[i:i+4] for i in range(len(flat))])
        self.assertEqual(commands[-1], ['--update'])

    def test_workspace_creation_removal_and_selection(self):
        old = ['application_gap', 'front_app', 'space.31', 'space.32', 'spaces']
        commands = workspaces.reconcile(['1', '3'], '3', old, ['background.height=32'])
        self.assertIn(['--remove', 'space.32'], [commands[i:i+2] for i in range(len(commands))])
        self.assertIn(['--clone', 'space.33', 'workspace_template'], [commands[i:i+3] for i in range(len(commands))])
        self.assertIn(['--set', 'space.33', 'background.drawing=on'], [commands[i:i+3] for i in range(len(commands))])
        moved = [commands[i+1] for i, value in enumerate(commands) if value == '--move']
        self.assertEqual(moved, ['space.31', 'space.33'])
        for i, value in enumerate(commands):
            if value == '--move':
                self.assertEqual(commands[i+3], 'application_gap')
        self.assertIn(['--set', 'space.33', 'background.drawing=on', 'icon.highlight=on'], [commands[i:i+4] for i in range(len(commands))])
        self.assertIn(['--set', 'space.31', 'background.drawing=off', 'icon.highlight=off'], [commands[i:i+4] for i in range(len(commands))])
        stable = workspaces.reconcile(['1', '3'], '1', ['space.31', 'space.33', 'spaces'], [])
        self.assertNotIn('--clone', stable)
        self.assertNotIn('--remove', stable)

    def test_workspace_names_are_shell_quoted(self):
        name = "research ' $(touch /tmp/unwanted)"
        commands = workspaces.reconcile([name], name, [], [])
        click = next(value.split('=', 1)[1] for value in commands if value.startswith('click_script='))
        self.assertEqual(shlex.split(click), ['aerospace', 'workspace', name])
        self.assertRegex(workspaces.item_name(name), r'^space\.[0-9a-f]+$')

    def test_failed_workspace_query_never_mutates_the_bar(self):
        with patch.object(workspaces, 'output', side_effect=OSError('offline')) as output, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workspaces.main(), 1)
        output.assert_called_once_with('aerospace', 'list-workspaces', '--all')

    def test_focus_publication_restoration_and_off_without_shortcut_calls(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)), patch.object(focus.subprocess, 'run') as run:
            folder = Path(temporary)
            icon = folder / 'logo.png'
            icon.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
            with patch.object(focus, 'render_image', return_value=icon):
                focus.publish_focus(icon)
            self.assertEqual(focus.read_focus(), {'state': 'on', 'image': icon})
            run.assert_called_once_with(['sketchybar', '--trigger', 'focus_changed'], check=True, capture_output=True, timeout=3)
            focus.publish_focus()
            self.assertEqual(focus.read_focus(), {'state': 'off', 'image': None})
            self.assertTrue(icon.exists())
            self.assertNotIn('shortcuts', repr(run.call_args_list))

    def test_focus_invalid_missing_or_corrupt_state_never_claims_off(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)), patch.object(focus.subprocess, 'run'):
            folder = Path(temporary)
            self.assertEqual(focus.read_focus()['state'], 'unavailable')
            raw = folder / 'invalid.png'
            raw.write_bytes(b'invalid PNG')
            focus.publish_focus(raw)
            self.assertEqual(focus.read_focus()['state'], 'unavailable')
            for contents in ['{', '{"version":2,"state":"off"}', '{"version":1,"state":"on","image":"/missing.png"}', 'null']:
                (folder / 'state.json').write_text(contents)
                self.assertEqual(focus.read_focus()['state'], 'unavailable')

    def test_focus_binary_input_is_rendered_before_temporary_source_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)), patch.object(focus.subprocess, 'run') as run:
            folder = Path(temporary)
            png = b'\x89PNG\r\n\x1a\nfixture'
            sources = []
            def normalize(raw):
                self.assertEqual(raw.read_bytes(), png)
                sources.append(raw)
                image = folder / 'normalized.png'
                image.write_bytes(png)
                return image
            with patch.object(focus, 'render_image', side_effect=normalize):
                focus.publish_image_bytes(png)
            self.assertFalse(sources[0].exists())
            self.assertEqual(focus.read_focus(), {'state': 'on', 'image': folder / 'normalized.png'})
            self.assertEqual(run.call_args.args[0], ['sketchybar', '--trigger', 'focus_changed'])
            focus.publish_image_bytes(b'')
            self.assertEqual(focus.read_focus()['state'], 'unavailable')
            saved = json.loads((folder / 'state.json').read_text())
            self.assertEqual(saved['error'], 'The Focus automation did not provide PNG data.')

    def test_focus_state_survives_stopped_bar_and_restores_without_querying_macOS(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)):
            with patch.object(focus.subprocess, 'run', side_effect=OSError('bar stopped')):
                focus.publish_focus()
            self.assertEqual(focus.read_focus(), {'state': 'off', 'image': None})
            with patch.object(focus.subprocess, 'run') as run:
                focus.main()
                self.assertEqual(run.call_args.args[0], ['sketchybar', '--set', 'focus', 'drawing=off', 'label.drawing=off', 'icon=?', 'icon.drawing=on', 'background.drawing=off', 'background.image.drawing=off'])

    def test_focus_rendering_preserves_unknown_state(self):
        for state, expected in [('off', 'drawing=off'), ('on', 'background.image=/fixture/logo.png'), ('unavailable', 'background.image=/fixture/logo.png')]:
            with patch.object(focus, 'read_focus', return_value={'state': state, 'image': Path('/fixture/logo.png') if state == 'on' else None}), patch.object(focus, 'render_symbol', return_value=Path('/fixture/logo.png')) as render, patch.object(focus.subprocess, 'run') as run:
                focus.main()
                self.assertIn(expected, run.call_args.args[0])
                self.assertIn('label.drawing=off', run.call_args.args[0])
                self.assertNotIn('label=Work', run.call_args.args[0])
                if state == 'unavailable':
                    render.assert_called_once_with('questionmark.circle')
                else:
                    render.assert_not_called()

    def test_missing_symbol_never_becomes_a_different_focus_logo(self):
        arguments = focus.display_arguments({'state': 'on'}, None)
        self.assertIn('icon=?', arguments)
        self.assertIn('background.image.drawing=off', arguments)
        self.assertNotIn('label=Custom Focus', arguments)

    @unittest.skipUnless(sys.platform == 'darwin', 'AppKit requires macOS')
    def test_real_png_bytes_publish_a_normalized_icon_without_contacting_the_bar(self):
        actual_run = subprocess.run
        def run(command, **options):
            if command[0] == 'sketchybar':
                return subprocess.CompletedProcess(command, 0)
            return actual_run(command, **options)
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)), patch.object(focus.subprocess, 'run', side_effect=run):
            png = (Path(__file__).parent / 'assets/focus/work.png').read_bytes()
            focus.publish_image_bytes(png)
            saved = focus.read_focus()
            self.assertEqual(saved['state'], 'on')
            self.assertEqual(struct.unpack('>II', saved['image'].read_bytes()[16:24]), (36, 36))
            self.assertFalse(list(Path(temporary).glob('input-*')))

    @unittest.skipUnless(sys.platform == 'darwin', 'AppKit requires macOS')
    def test_real_symbol_render_and_cache_without_a_window(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus, 'cache_folder', return_value=Path(temporary)), patch.object(focus.subprocess, 'run', wraps=subprocess.run) as run:
            image = focus.render_symbol('briefcase.fill')
            self.assertIsNotNone(image)
            png = image.read_bytes()
            self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', png[16:24]), (36, 36))
            self.assertEqual(focus.render_symbol('briefcase.fill'), image)
            self.assertEqual(run.call_count, 1)
            self.assertIsNone(focus.render_symbol('this.symbol.does.not.exist'))
            with patch.object(focus.subprocess, 'run', wraps=subprocess.run) as normalize:
                normalized = focus.render_image(image)
                self.assertEqual(struct.unpack('>II', normalized.read_bytes()[16:24]), (36, 36))
                self.assertEqual(focus.render_image(image), normalized)
                self.assertEqual(normalize.call_count, 1)

    def test_clock_midnight_noon_and_evening(self):
        source = (PLUGINS / 'clock.sh').read_text()
        for value, expected in [('12:00 AM', '12:00 AM'), ('12:00 PM', '12:00 PM'), ('09:12 PM', '9:12 PM')]:
            script = 'date(){ printf "%s" "$CLOCK_FIXTURE"; }; sketchybar(){ printf "%s\\n" "$@"; }; ' + source
            result = subprocess.run(['/bin/sh', '-c', script], env={'CLOCK_FIXTURE': value, 'NAME': 'clock', 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ['--set', 'clock', 'label=' + expected])
            self.assertIn("date '+%I:%M %p'", source)

    def test_caffeine_overlapping_sessions_keep_mug_until_last_process_exits(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(caffeine, 'cache_folder', return_value=Path(temporary)), patch.object(caffeine, 'mug_image', return_value=Path('/fixture/mug.png')), patch.object(caffeine.subprocess, 'run') as run:
            for pids, expected in [({101, 102}, 'on'), ({102}, 'on'), (set(), 'off')]:
                with patch.object(caffeine, 'process_ids', return_value=pids):
                    self.assertEqual(caffeine.refresh(), pids)
                command = run.call_args.args[0]
                self.assertIn('drawing=' + expected, command)
                if pids:
                    self.assertIn('background.image=/fixture/mug.png', command)

    def test_caffeine_failed_process_query_never_hides_the_mug(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(caffeine, 'cache_folder', return_value=Path(temporary)), patch.object(caffeine.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 2, '', 'Cannot get process list')
            with self.assertRaisesRegex(RuntimeError, 'Cannot get process list'):
                caffeine.refresh()
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][0], '/usr/bin/pgrep')

    def test_caffeine_exit_between_snapshot_and_watch_rechecks_state(self):
        watched = set()
        with patch.object(caffeine, 'refresh', side_effect=[{101}, set()]) as refresh, patch.object(caffeine, 'watch_process', return_value=False):
            caffeine.reconcile(object(), watched)
        self.assertEqual(refresh.call_count, 2)
        self.assertEqual(watched, set())

    def test_caffeine_listener_survives_item_removal_during_reload(self):
        watched = {101}
        unavailable = subprocess.CalledProcessError(1, ['sketchybar', '--set', 'caffeine'])
        with patch.object(caffeine, 'refresh', side_effect=[unavailable, {101}]) as refresh, contextlib.redirect_stderr(io.StringIO()):
            caffeine.reconcile(object(), watched)
            caffeine.reconcile(object(), watched)
        self.assertEqual(refresh.call_count, 2)
        self.assertEqual(watched, {101})

    def test_caffeine_duplicate_listener_never_starts_another_stream(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(caffeine, 'cache_folder', return_value=Path(temporary)), patch.object(caffeine, 'process_ids') as processes:
            with (Path(temporary) / 'listener.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertEqual(caffeine.listen(), 0)
            processes.assert_not_called()

    def test_caffeine_bundled_mug_is_a_transparent_png(self):
        png = caffeine.mug_image().read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', png[16:24]), (36, 36))
        self.assertEqual(png[25], 6)  # Truecolor with alpha.


if __name__ == '__main__':
    unittest.main()
