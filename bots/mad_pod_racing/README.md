# Mad Pod Racing

Two-pod racing AI (contest). This folder tracks separate bots per **league**.

## Leagues

- `gold/`: current Gold league bot

## Submitting

- Copy/paste: `gold/bot.py` into CodinGame (Python 3).
- Optional: print the submission to stdout:

```bash
python3 ../../tools/pack.py bots/mad_pod_racing/gold/bot.py
```

## High-level approach (Gold)

- **Role stability**: keep a consistent racer vs blocker by checkpoint progress + hysteresis.
- **Racer**: 1-step forward sim over a small candidate set (aim points + thrust/BOOST) to reduce overshoot/stalling.
- **Blocker**: intercept the enemy leader with a lead target biased toward their next checkpoint.


