"""Fixture checks. No native service calls or Focus database access."""
import contextlib
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


workspaces, focus = module('workspaces'), module('focus')


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
        self.assertIn(['--add', 'bracket', 'status', 'focus', 'clock'], [flat[i:i+5] for i in range(len(flat))])
        self.assertEqual(commands[-1], ['--update'])

    def test_workspace_creation_removal_and_selection(self):
        old = ['front_app', 'space.31', 'space.32', 'spaces']
        commands = workspaces.reconcile(['1', '3'], '3', old, ['background.height=32'])
        self.assertIn(['--remove', 'space.32'], [commands[i:i+2] for i in range(len(commands))])
        self.assertIn(['--clone', 'space.33', 'workspace_template'], [commands[i:i+3] for i in range(len(commands))])
        self.assertIn(['--set', 'space.33', 'background.drawing=on'], [commands[i:i+3] for i in range(len(commands))])
        moved = [commands[i+1] for i, value in enumerate(commands) if value == '--move']
        self.assertEqual(moved, ['space.31', 'space.33'])
        for i, value in enumerate(commands):
            if value == '--move':
                self.assertIn(commands[i+3], old)
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

    def test_focus_on_off_unknown_and_custom_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            self.assertEqual(focus.read_focus(folder)['state'], 'unavailable')
            assertions = folder / 'Assertions.json'
            assertions.write_text('{"data":[{"storeAssertionRecords":[]}]}')
            self.assertEqual(focus.read_focus(folder)['state'], 'off')
            assertions.write_text(json.dumps({'data': [{'storeAssertionRecords': [{'assertionDetails': {'assertionDetailsModeIdentifier': 'custom'}}]}]}))
            (folder / 'ModeConfigurations.json').write_text(json.dumps({'data': [{'modeConfigurations': {'custom': {'mode': {'name': 'Deep Research', 'symbolImageName': 'moon.fill'}}}}]}))
            self.assertEqual(focus.read_focus(folder), {'state': 'on', 'name': 'Deep Research', 'symbol': 'moon.fill'})
            assertions.write_text('{"data":[{"storeAssertionRecords":[{}]}]}')
            self.assertEqual(focus.read_focus(folder)['state'], 'unavailable')
            assertions.write_text('invalid JSON')
            self.assertEqual(focus.read_focus(folder)['state'], 'unavailable')
        with patch.object(Path, 'read_text', side_effect=PermissionError):
            self.assertEqual(focus.read_focus(Path('/fixture'))['state'], 'unavailable')

    def test_focus_rendering_preserves_unknown_state(self):
        for state, expected in [('off', 'drawing=off'), ('on', 'background.image=/fixture/logo.png'), ('unavailable', 'background.image=/fixture/logo.png')]:
            with patch.object(focus, 'read_focus', return_value={'state': state, 'name': 'Work' if state == 'on' else None, 'symbol': 'briefcase.fill' if state == 'on' else None}), patch.object(focus, 'render_symbol', return_value=Path('/fixture/logo.png')) as render, patch.object(focus.subprocess, 'run') as run:
                focus.main()
                self.assertIn(expected, run.call_args.args[0])
                self.assertIn('label.drawing=off', run.call_args.args[0])
                self.assertNotIn('label=Work', run.call_args.args[0])
                if state == 'off':
                    render.assert_not_called()
                else:
                    render.assert_called_once_with('briefcase.fill' if state == 'on' else 'questionmark.circle')

    def test_missing_symbol_never_becomes_a_different_focus_logo(self):
        arguments = focus.display_arguments({'state': 'on', 'name': 'Custom Focus'}, None)
        self.assertIn('icon=?', arguments)
        self.assertIn('background.image.drawing=off', arguments)
        self.assertNotIn('label=Custom Focus', arguments)

    @unittest.skipUnless(sys.platform == 'darwin', 'AppKit requires macOS')
    def test_real_symbol_render_and_cache_without_a_window(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(focus.tempfile, 'gettempdir', return_value=temporary), patch.object(focus.subprocess, 'run', wraps=subprocess.run) as run:
            image = focus.render_symbol('briefcase.fill')
            self.assertIsNotNone(image)
            png = image.read_bytes()
            self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', png[16:24]), (36, 36))
            self.assertEqual(focus.render_symbol('briefcase.fill'), image)
            self.assertEqual(run.call_count, 1)
            self.assertIsNone(focus.render_symbol('this.symbol.does.not.exist'))

    def test_clock_midnight_noon_and_evening(self):
        source = (PLUGINS / 'clock.sh').read_text()
        for value, expected in [('12:00 AM', '12:00 AM'), ('12:00 PM', '12:00 PM'), ('09:12 PM', '9:12 PM')]:
            script = 'date(){ printf "%s" "$CLOCK_FIXTURE"; }; sketchybar(){ printf "%s\\n" "$@"; }; ' + source
            result = subprocess.run(['/bin/sh', '-c', script], env={'CLOCK_FIXTURE': value, 'NAME': 'clock', 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ['--set', 'clock', 'label=' + expected])
            self.assertIn("date '+%I:%M %p'", source)


if __name__ == '__main__':
    unittest.main()
