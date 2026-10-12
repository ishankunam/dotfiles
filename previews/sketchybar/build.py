"""Build the browser fragment without executing the SketchyBar configuration."""
import argparse
import base64
import json
import re
import shlex
from pathlib import Path


def config_values(path):
    source = path.read_text().replace('\\\n', ' ')
    bar = re.search(r'^sketchybar --bar (.+)$', source, re.MULTILINE)
    defaults = re.search(r'default=\((.*?)\)', source, re.DOTALL)
    space = re.search(r'\bspace=\((.*?)\)', source, re.DOTALL)
    groups = re.search(r'group=\((.*?)\)', source, re.DOTALL)
    if not all((bar, defaults, space, groups)):
        raise ValueError('Expected the reviewed shell configuration format.')

    def properties(text):
        return dict(token.split('=', 1) for token in shlex.split(text, comments=True) if '=' in token)

    b, d, g = properties(bar[1]), properties(defaults[1]), properties(groups[1])
    if d['label.font'].split(':')[:2] != ['Hack Nerd Font', 'Bold']:
        raise ValueError('Create a matching browser font asset before changing the native font.')
    return {'height': int(b['height']), 'labelSize': float(d['label.font'].rsplit(':', 1)[1]),
            'iconSize': float(d['icon.font'].rsplit(':', 1)[1]), 'font': d['label.font'],
            'radius': int(g['background.corner_radius']),
            'barColor': b['color'], 'groupColor': g['background.color'],
            'groupHeight': int(g['background.height']), 'blur': int(b['blur_radius']),
            'borderColor': g['background.border_color'], 'textColor': d['label.color'],
            'spaceColor': properties(space[1])['background.color']}


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=folder / 'inline.html')
    args = parser.parse_args()
    data = json.loads((folder / 'desktop.json').read_text())
    data['config'] = config_values(folder.parents[1] / 'sketchybar/.config/sketchybar/sketchybarrc')
    data['focusImages'] = {name: 'data:image/png;base64,' + base64.b64encode((folder / 'assets/focus' / filename).read_bytes()).decode()
                           for name, filename in [('Work', 'work.png'), ('Do Not Disturb', 'do-not-disturb.png'), ('Unavailable', 'unavailable.png')]}
    source = (folder / 'desktop-preview.html').read_text()
    replacements = {
        '<!-- PREVIEW_DATA -->': json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'),
        '__HACK_FONT__': 'data:font/woff;base64,' + base64.b64encode((folder / 'assets/hack-nerd-bold-subset.woff').read_bytes()).decode(),
        '__FIRA_FONT__': 'data:font/woff;base64,' + base64.b64encode((folder / 'assets/fira-code-medium-subset.woff').read_bytes()).decode(),
        '__MONET_IMAGE__': 'data:image/jpeg;base64,' + base64.b64encode((folder / 'assets/monet.jpg').read_bytes()).decode(),
    }
    for placeholder, value in replacements.items():
        if source.count(placeholder) != 1:
            raise ValueError('Expected one placeholder: ' + placeholder)
        source = source.replace(placeholder, value)
    if len(source.encode()) > 1_000_000:
        raise ValueError('The inline preview must remain below 1 MB.')
    args.output.write_text(source)
    print(args.output)


if __name__ == '__main__':
    main()
