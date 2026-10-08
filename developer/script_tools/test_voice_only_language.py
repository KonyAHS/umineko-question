"""Exercise the patched script's helpers using a real PONScripter executable."""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile
import wave

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--engine', type=Path, required=True)
parser.add_argument('--font', type=Path, default=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
s=(repo / 'InDevelopment/ManualUpdates/0.utf').read_text(encoding='utf-8-sig')
def body(label): return s.split('*'+label+'\n',1)[1].split('\nreturn',1)[0]+'\nreturn\n'
workspace = tempfile.TemporaryDirectory(prefix='umineko-language-smoke-')
root = Path(workspace.name)
(root / 'sav').mkdir()
with wave.open(str(root/'test.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(22050);w.writeframes(b'\0\0'*2205)
code='''*define
caption "Japanese voice helper regression"
numalias cur_language,3900
numalias cur_read_lang,3901
numalias r_last_language,3902
numalias r_for_title,3903
numalias stage,3904
numalias witchh1,1
numalias witchh6,6
numalias witchh7,7
numalias witchh11,11
numalias last_voice_play_time,12
numalias VOICE_DELAY_PADDING,0
defsub dwave_jp
defsub dwave_eng
defsub changeLanguage
defsub toggleLanguage
defsub voicedelay
defsub voicewait
defsub applyTipsLanguage
loadgosub *restore_language
globalon
game
*start
resettimer
delay 20
changeLanguage 0
mov %last_voice_play_time,-1
dwave_jp 0,"test.wav"
if %last_voice_play_time != -1 goto *failure
dwave_eng 0,"test.wav"
if %last_voice_play_time < 0 goto *failure
toggleLanguage
if %cur_language != 1 goto *failure
mov %last_voice_play_time,-1
dwave_eng 0,"test.wav"
if %last_voice_play_time != -1 goto *failure
dwave_jp 0,"test.wav"
if %last_voice_play_time < 0 goto *failure
langen
gettimer %20
voicedelay 5000
voicewait 5000
gettimer %21
if %21-%20 > 1000 goto *failure
toggleLanguage
if %cur_language != 0 goto *failure
; Title-screen TIPS must not attempt to reload a story.
mov %r_for_title,1
mov %r_last_language,1
applyTipsLanguage
if %cur_language != 0 goto *failure
; Emulate the cached save taken before a story text wait.
mov %r_for_title,0
mov %stage,0
saveon
savegame 15
if %stage = 1 goto *after_tips
mov %stage,1
saveoff
mov %r_last_language,1
applyTipsLanguage
goto *failure
*after_tips
if %cur_language != 1 goto *failure
mov %last_voice_play_time,-1
dwave_jp 0,"test.wav"
if %last_voice_play_time < 0 goto *failure
saveon
savegame 1
end
*restore_language
changeLanguage %cur_language
return
*failure
THIS_IS_A_REGRESSION_FAILURE
end
'''
for label in ('dwave_jp','dwave_eng','changeLanguage','toggleLanguage','voicedelay','voicewait','applyTipsLanguage'): code+='\n*'+label+'\n'+body(label)
(root/'0.utf').write_text(code,encoding='utf-8-sig')
import shutil
shutil.copy(args.font, root / 'default.ttf')
result = subprocess.run(
    ['xvfb-run', '-a', str(args.engine.resolve()), '--root', str(root), '--save', str(root)],
    cwd=root, env={**os.environ, 'SDL_AUDIODRIVER': 'dummy'},
    capture_output=True, text=True, timeout=20)
assert result.returncode == 0, result.stdout + result.stderr
assert (root / 'sav/save1.dat').exists(), result.stdout + result.stderr
assert 'THIS_IS_A_REGRESSION_FAILURE' not in result.stdout + result.stderr
print('PASS: PONScripter executes EN→JP→EN toggles, language-specific voice playback, '
      'skips hidden dialogue delays, and applies TIPS language through save/load.')
workspace.cleanup()
