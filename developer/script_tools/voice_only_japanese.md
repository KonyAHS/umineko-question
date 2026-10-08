# Japanese dialogue in the Question Arcs voice-only patch

The fix is on `fix/voice-only-japanese`, based on voice-only commit `75a4daa`.
The release workflow must package this script from the `voice_only` branch after
merging the fix there. It does not belong on the full patch's `master` branch.

## Changes

- Restore the existing initial English/Japanese selection instead of forcing English.
- Port Japanese dialogue voice cues and delays from full-patch commit
  `3890270578f6446375ec0a4c956d03b8d222e034`.
- Guard English and Japanese voices separately: the engine processes commands
  in both language streams even when their text is hidden.
- Enable Tab and add a direct To JP / To EN button to the right-click menu.
- Apply the existing TIPS language choice to gameplay when exiting any of its
  episode-specific menus. Title-screen TIPS do not reload a story.
- Restore the selected display language in the load callback and skip voice
  delays in hidden dialogue.

The port matches Japanese text in order, ignoring voice markup, text timing,
whitespace, and page markers. Paragraphs split differently in the full script
were handled separately, preserving original scene commands and `$Free1`
assignment boundaries. Full-only mixed voice aliases were mapped to the
voice-only aliases for the same audio paths. Missing voiced Japanese sentences
and numeric text were restored from the full script. Two full-script mistakes
(`sha_2e83` and `stufa4007`) used English guards in Japanese dialogue; those cues
use Japanese guards here.

English dialogue and its original voice assignments are unchanged. The original
background, sprite, effect, and other scene commands are unchanged.

## Checks

From the repository root:

```sh
python3 developer/script_tools/verify_voice_only_japanese.py
python3 developer/script_tools/test_voice_only_language.py --engine /path/to/ponscr
```

The audit compares all 45,450 Japanese voice paths and channels in order against
the full script, checks aliases, unchanged English lines and scene commands,
and language switch wiring. It needs the two source commits in local Git history.
The baseline script fails the audit.

The smoke test requires `xvfb-run` and a font (override its default with `--font`).
It runs the actual script helpers using synthetic audio in a temporary game
folder. Tested with the official PONScripter v4.0.0 Linux nodep executable:
EN→JP→EN, active/inactive voice guards, hidden dialogue delays, and TIPS language
application through a cached save/load all pass.

This workspace has no installed game assets, so a full game playthrough, actual
Tab/button interaction, font appearance, and ordinary user-save compatibility
have not been tested. In particular, `voice/99/stufa4007.ogg` and
`voice/99/comfa4011.ogg` occur in the full Japanese script but are not referenced
by the old voice-only script. Confirm they are present in the installed voice
archives. The rest of the port's audio paths already appear in the voice-only
script or its alias table.

## Try the patched script

Close the game. Back up its current script, then replace the voice-only patch's
`0.u` with `InDevelopment/ManualUpdates/0.utf` renamed to `0.u`. For installations
that use `0.utf`, replace that filename instead. Keep only the intended active
script. Start a new game or start at a chapter boundary for initial testing:
script line positions changed, so an old mid-scene save is not a reliable test.

Choose Japanese at initial setup, press Tab during dialogue, or use To JP in the
right-click menu. The TIPS menu's language selection also applies when returning
to gameplay. Check both directions, then check save/load, backlog, and the
opening/Tea Party/???? sections for each episode.

This repository and fix cover Question Arcs (episodes 1–4). Answer Arcs require a
separate port in `umineko-answer`.
