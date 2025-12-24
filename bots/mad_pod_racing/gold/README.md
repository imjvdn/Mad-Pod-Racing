# Mad Pod Racing — Gold League

## Submission

- CodinGame language: **Python 3**
- Copy/paste: `bot.py`
- Optional (stdout):

```bash
python3 tools/pack.py bots/mad_pod_racing/gold/bot.py
```

## Behavior summary

- **Racer**
  - Picks the lead pod using checkpoint progress + tie-break hysteresis (prevents role thrash).
  - Uses a small 1-step forward simulation to choose `(target, thrust/BOOST)` each turn.
  - Avoids “0-thrust stall” cases by clamping velocity compensation and limiting full braking.
- **Blocker**
  - Aims to intercept the opponent leader with a lead-time target biased toward their next checkpoint.
  - Uses SHIELD only on imminent, high-relative-speed collisions.


