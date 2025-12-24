# CodinGame Bots

Paste-ready CodinGame bots (primarily contest AIs). Every bot is kept **single-file** so it can be copied directly into the CodinGame editor.

## Repo conventions

- **Submission files**: `bot.py` is always import-free beyond stdlib.
- **League separation**: variants live under `bots/<game>/<league>/`.
- **Notes live next to the bot**: each league folder has its own `README.md`.

## Structure

- `bots/<game>/README.md`: game index + league inventory.
- `bots/<game>/<league>/bot.py`: CodinGame submission (single-file).
- `bots/<game>/<league>/README.md`: league-specific notes.
- `tools/pack.py`: prints a single-file bot to stdout (useful for copy/paste workflows).

## Usage

- **Copy into CodinGame**: open `bots/<game>/<league>/bot.py`, paste into the CodinGame IDE.
- **Print to stdout**:

```bash
python3 tools/pack.py bots/mad_pod_racing/gold/bot.py
```

## Bots

- `bots/mad_pod_racing/gold`: Mad Pod Racing — Gold league


