#!/usr/bin/env python3
"""Audit the Japanese voice port against the full script and voice-only baseline."""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = 'InDevelopment/ManualUpdates/0.utf'
FULL = '3890270578f6446375ec0a4c956d03b8d222e034'
BASE = '75a4daa'
VOICE = re.compile(r'\bdwave(?:_jp|_eng)?\s+(\d+),\s*(\w+|"[^"]+")')


def snapshot(ref):
    return subprocess.check_output(['git', 'show', f'{ref}:{SCRIPT}'], cwd=ROOT).decode('utf-8-sig')


def aliases(script):
    return {name.lower(): path for name, path in
            re.findall(r'^stralias\s+(\w+),\s*"([^"]+)"', script, re.M)}


def voice_paths(lines, table):
    result = []
    for line in lines:
        for channel, name in VOICE.findall(line):
            path = name[1:-1] if name.startswith('"') else table[name.lower()]
            result.append((channel, path))
    return result


def verify(script, full, base):
    jp = [line for line in script.splitlines() if line.startswith('langjp')]
    full_jp = [line for line in full.splitlines() if line.startswith('langjp')]
    actual = voice_paths(jp, aliases(script))
    expected = voice_paths(full_jp, aliases(full))
    assert actual == expected, 'Japanese voice paths/channels/order differ from the full patch'
    assert len(actual) == 45450, f'Unexpected Japanese voice cue count: {len(actual)}'
    base_paths = {path.lower() for path in aliases(base).values()}
    base_paths.update(path.lower() for _, path in voice_paths(base.splitlines(), aliases(base)))
    # These literal paths occur only in the full patch's Japanese dialogue.
    jp_only_literals = {'voice\\99\\stufa4007.ogg', 'voice\\99\\comfa4011.ogg'}
    assert {path.lower() for _, path in actual} - base_paths == jp_only_literals, (
        'Unexpected audio path absent from the voice-only baseline')
    assert not any('dwave_eng' in line for line in jp), 'English guard in Japanese dialogue'
    english = [line.replace('dwave_eng', 'dwave') for line in script.splitlines() if line.startswith('langen')]
    old_english = [line for line in base.splitlines() if line.startswith('langen')]
    assert english == old_english, 'English story text or voice cues changed'
    assert not any(re.search(r'\bdwave\s', line) for line in script.splitlines()
                   if line.startswith(('langjp', 'langen'))), 'Unguarded dialogue voice'
    # No ADV names, graphics, or effects from the full patch should enter the story.
    story = script.split('*umi1_opning', 1)[1].split('mov %0,3700', 1)[0]
    base_story = base.split('*umi1_opning', 1)[1].split('mov %0,3700', 1)[0]
    def scene_commands(text):
        return [line for line in text.splitlines() if line.strip()
                and not line.startswith(('langjp', 'langen'))]
    assert scene_commands(story) == scene_commands(base_story), 'Voice-only scene commands changed'
    assert script.count('\tapplyTipsLanguage\n') == 16, 'TIPS exits do not apply selected language'
    assert 'changeLanguage %r_last_language' in script
    assert 'gettab\n' in script.replace('\r\n', '\n')
    assert 'if %BtnRes = -20 toggleLanguage : savegame 15 : loadgame 15' in script
    assert 'if %BtnRes = r_language_lsp toggleLanguage : savegame 15 : loadgame 15' in script
    startup = script.split('\n*check_game\n', 1)[1].split('*postlangselect', 1)[0]
    assert 'changeLanguage 0' not in startup, 'Startup forces English'
    assert 'mov %shownlangselect, 1' not in startup, 'Startup disables language selection'
    assert 'changeLanguage %cur_language' in script.split('\n*Coll_system\n', 1)[1].split('return', 1)[0]
    for label in ('voicedelay', 'voicewait'):
        body = script.split(f'*{label}\n', 1)[1].split('\nreturn', 1)[0]
        assert 'if %cur_read_lang != %cur_language return' in body, f'{label} waits on hidden dialogue'
    print(f'PASS: {len(actual):,} Japanese cues match full-patch audio paths and order; '
          'English dialogue and voice-only scene commands preserved. '
          'Two Japanese-only literal audio paths require checking in an installed voice archive.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, default=ROOT / SCRIPT)
    parser.add_argument('--full-ref', default=FULL)
    parser.add_argument('--base-ref', default=BASE)
    args = parser.parse_args()
    verify(args.script.read_text(encoding='utf-8-sig'), snapshot(args.full_ref), snapshot(args.base_ref))
