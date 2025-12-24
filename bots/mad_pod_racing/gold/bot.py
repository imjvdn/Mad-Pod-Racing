import math


def dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


def length(vx: float, vy: float) -> float:
    return math.hypot(vx, vy)


def angle_to(ax: float, ay: float, bx: float, by: float) -> float:
    return math.degrees(math.atan2(by - ay, bx - ax))


def angle_diff(a: float, b: float) -> float:
    d = (a - b) % 360.0
    if d > 180.0:
        d -= 360.0
    return d


def clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


class Pod:
    __slots__ = ("x", "y", "vx", "vy", "ang", "ncp")

    def __init__(self, x: int, y: int, vx: int, vy: int, ang: int, ncp: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ang = ang
        self.ncp = ncp


def read_pod() -> Pod:
    x, y, vx, vy, ang, ncp = map(int, input().split())
    return Pod(x, y, vx, vy, ang, ncp)


class Prog:
    __slots__ = ("passed", "last_ncp", "init")

    def __init__(self) -> None:
        self.passed = 0
        self.last_ncp = 0
        self.init = False


def update_progress(st: Prog, pod: Pod, cp_count: int) -> None:
    if not st.init:
        st.last_ncp = pod.ncp
        st.passed = 0
        st.init = True
        return

    if pod.ncp == st.last_ncp:
        return

    delta = (pod.ncp - st.last_ncp) % cp_count
    if delta == 0:
        delta = 1
    st.passed += delta
    st.last_ncp = pod.ncp


def progress_key(pod: Pod, st: Prog, cps: list[tuple[int, int]]) -> tuple[int, float, float]:
    cx, cy = cps[pod.ncp]
    d = math.sqrt(dist2(pod.x, pod.y, cx, cy))
    s = length(pod.vx, pod.vy)
    return (st.passed, -d, s)


def projected_target_for_checkpoint(
    pod: Pod, cps: list[tuple[int, int]], cp_count: int
) -> tuple[float, float, float, float]:
    cx, cy = cps[pod.ncp]
    nx, ny = cps[(pod.ncp + 1) % cp_count]

    segx = nx - cx
    segy = ny - cy
    seglen = math.hypot(segx, segy)
    if seglen < 1.0:
        ux, uy = 0.0, 0.0
    else:
        ux, uy = segx / seglen, segy / seglen

    d2 = dist2(pod.x, pod.y, cx, cy)
    dist = math.sqrt(d2)
    speed = length(pod.vx, pod.vy)

    look = 450.0
    if dist > 6500:
        look = 1100.0
    elif speed > 900.0:
        look = 900.0
    elif speed > 650.0:
        look = 700.0

    if dist < 5000:
        tx = cx + ux * look
        ty = cy + uy * look
        apex = clamp((dist - 900.0) / 3000.0, 0.10, 0.70)
        bx = tx * apex + cx * (1.0 - apex)
        by = ty * apex + cy * (1.0 - apex)
    else:
        bx, by = cx, cy

    corr = 0.40
    if dist > 7000:
        corr = 1.00
    elif dist > 4500:
        corr = 0.75
    elif dist > 2500:
        corr = 0.55

    # Velocity compensation: clamp so we don't aim *behind* ourselves and stall (diff>95 -> thrust 0).
    sx = pod.vx * corr
    sy = pod.vy * corr
    sl = math.hypot(sx, sy)
    max_shift = max(300.0, dist * 0.55)
    if sl > max_shift:
        k = max_shift / sl
        sx *= k
        sy *= k

    aimx = bx - sx
    aimy = by - sy

    desired = angle_to(pod.x, pod.y, aimx, aimy)
    diff = abs(angle_diff(desired, pod.ang))

    return aimx, aimy, dist, diff


def thrust_for_angle_and_dist(diff: float, dist: float, speed: float) -> int:
    t = 100

    # Avoid "0-thrust spiral" when our target ends up behind us.
    # NOTE: "0" is almost always wrong when you're far away; it kills repositioning.
    # Only allow hard 0 when you're close and massively misaligned.
    if diff > 140:
        t = 0 if dist < 900 else 20
    elif diff > 95:
        t = 15 if dist > 900 else 0
    elif diff > 70:
        t = 35
    elif diff > 45:
        t = 65
    elif diff > 25:
        t = 85

    if dist < 850:
        t = min(t, 25)
    elif dist < 1300:
        t = min(t, 55)
    elif dist < 2200 and speed > 900 and diff > 35:
        t = min(t, 70)

    return int(t)


def simulate_step(
    x: float,
    y: float,
    vx: float,
    vy: float,
    ang: float,
    tx: float,
    ty: float,
    thrust: float,
    *,
    first_turn: bool,
) -> tuple[float, float, float, float, float]:
    desired = angle_to(x, y, tx, ty)
    d = angle_diff(desired, ang)
    if not first_turn:
        d = clamp(d, -18.0, 18.0)
    ang2 = (ang + d) % 360.0

    rad = math.radians(ang2)
    vx2 = vx + math.cos(rad) * thrust
    vy2 = vy + math.sin(rad) * thrust

    x2 = x + vx2
    y2 = y + vy2

    vx2 *= 0.85
    vy2 *= 0.85

    vx2 = float(math.trunc(vx2))
    vy2 = float(math.trunc(vy2))
    x2 = float(int(round(x2)))
    y2 = float(int(round(y2)))

    return x2, y2, vx2, vy2, ang2


def racer_candidates(pod: Pod, cps: list[tuple[int, int]], cp_count: int) -> tuple[list[tuple[float, float]], float, float]:
    cx, cy = cps[pod.ncp]
    nx, ny = cps[(pod.ncp + 1) % cp_count]

    segx = nx - cx
    segy = ny - cy
    seglen = math.hypot(segx, segy)
    if seglen < 1.0:
        ux, uy = 0.0, 0.0
    else:
        ux, uy = segx / seglen, segy / seglen

    dist = math.sqrt(dist2(pod.x, pod.y, cx, cy))
    speed = length(pod.vx, pod.vy)

    look = 450.0
    if dist > 6500:
        look = 1100.0
    elif speed > 900.0:
        look = 900.0
    elif speed > 650.0:
        look = 700.0

    # "Exit" point and blended apex point.
    tx = cx + ux * look
    ty = cy + uy * look
    if dist < 5000:
        apex = clamp((dist - 900.0) / 3000.0, 0.10, 0.70)
        bx = tx * apex + cx * (1.0 - apex)
        by = ty * apex + cy * (1.0 - apex)
    else:
        bx, by = cx, cy

    # Two levels of velocity compensation (clamped).
    def compensated(px: float, py: float, k: float) -> tuple[float, float]:
        sx = pod.vx * k
        sy = pod.vy * k
        sl = math.hypot(sx, sy)
        max_shift = max(250.0, dist * 0.50)
        if sl > max_shift:
            kk = max_shift / sl
            sx *= kk
            sy *= kk
        return px - sx, py - sy

    aim1 = compensated(bx, by, 0.55 if dist > 2500 else 0.40)
    aim2 = compensated(cx, cy, 0.35)

    # Keep candidate set small for speed.
    cands = [(cx, cy), (bx, by), aim1, aim2, (tx, ty)]
    return cands, dist, speed


def pick_racer_action(
    pod: Pod,
    cps: list[tuple[int, int]],
    cp_count: int,
    *,
    turn: int,
    boost_used: bool,
) -> tuple[float, float, str, bool, float]:
    cands, dist, speed = racer_candidates(pod, cps, cp_count)
    cx, cy = cps[pod.ncp]
    nx, ny = cps[(pod.ncp + 1) % cp_count]

    segx = nx - cx
    segy = ny - cy
    seglen = math.hypot(segx, segy)
    if seglen < 1.0:
        ux, uy = 0.0, 0.0
    else:
        ux, uy = segx / seglen, segy / seglen

    first_turn = turn == 0

    best_score = 10**18
    best_tx, best_ty = cx, cy
    best_cmd = "100"
    used_boost = False

    # Don't consider "0 thrust" unless we're already very close (otherwise we lose huge time).
    if dist < 1200:
        thrusts = (0.0, 35.0, 65.0, 85.0, 100.0)
    elif dist < 3500:
        thrusts = (35.0, 65.0, 85.0, 100.0)
    else:
        thrusts = (65.0, 85.0, 100.0)
    for tx, ty in cands:
        desired = angle_to(pod.x, pod.y, tx, ty)
        diff = abs(angle_diff(desired, pod.ang))

        # Exit-speed matters in Gold: reward velocity along the checkpoint->next segment.
        exit_weight = 0.18 if dist < 5000 else 0.10

        # Consider BOOST as a candidate action.
        if (not boost_used) and diff < (2.8 if first_turn else 2.2) and dist > 6000:
            x2, y2, vx2, vy2, ang2 = simulate_step(
                float(pod.x),
                float(pod.y),
                float(pod.vx),
                float(pod.vy),
                float(pod.ang),
                tx,
                ty,
                650.0,
                first_turn=first_turn,
            )
            d2 = math.sqrt(dist2(x2, y2, cx, cy))
            sp2 = math.hypot(vx2, vy2)
            aerr = abs(angle_diff(angle_to(x2, y2, cx, cy), ang2))
            exit_v = vx2 * ux + vy2 * uy
            score = d2 + aerr * 6.0 - sp2 * 0.04 - exit_v * exit_weight
            if d2 < 600.0:
                score -= 2500.0
            if score < best_score:
                best_score = score
                best_tx, best_ty = tx, ty
                best_cmd = "BOOST"
                used_boost = True

        for thrust in thrusts:
            x2, y2, vx2, vy2, ang2 = simulate_step(
                float(pod.x),
                float(pod.y),
                float(pod.vx),
                float(pod.vy),
                float(pod.ang),
                tx,
                ty,
                thrust,
                first_turn=first_turn,
            )
            d2 = math.sqrt(dist2(x2, y2, cx, cy))
            sp2 = math.hypot(vx2, vy2)
            aerr = abs(angle_diff(angle_to(x2, y2, cx, cy), ang2))
            exit_v = vx2 * ux + vy2 * uy

            score = d2 + aerr * 5.2 - sp2 * 0.04 - exit_v * exit_weight
            if d2 < 600.0:
                score -= 2500.0
            # Strongly discourage low thrust far from checkpoint.
            if dist > 3500 and thrust < 65.0:
                score += 2500.0
            elif dist > 2000 and thrust < 35.0:
                score += 2500.0

            if score < best_score:
                best_score = score
                best_tx, best_ty = tx, ty
                best_cmd = str(int(thrust))
                used_boost = False

    return best_tx, best_ty, best_cmd, used_boost, dist


def blocker_thrust(diff: float, dist: float) -> int:
    # Blocker should basically never stop. It needs momentum to get to collision points.
    if dist < 700 and diff > 150:
        return 0
    if diff > 150:
        return 40
    if diff > 110:
        return 70
    return 100


def imminent_collision(p: Pod, e: Pod) -> tuple[bool, float]:
    rx = e.x - p.x
    ry = e.y - p.y
    rvx = e.vx - p.vx
    rvy = e.vy - p.vy

    vv = rvx * rvx + rvy * rvy
    if vv < 1.0:
        return (False, 0.0)

    t = -((rx * rvx + ry * rvy) / vv)
    if t < 0.0 or t > 1.2:
        return (False, 0.0)

    cx = rx + rvx * t
    cy = ry + rvy * t
    d2 = cx * cx + cy * cy

    rels = math.sqrt(vv)
    return (d2 < 860.0 * 860.0 and rels > 420.0, rels)


def should_shield(pod: Pod, e1: Pod, e2: Pod) -> bool:
    hit1, s1 = imminent_collision(pod, e1)
    if hit1 and s1 > 500.0:
        return True
    hit2, s2 = imminent_collision(pod, e2)
    if hit2 and s2 > 500.0:
        return True
    return False


def blocker_intercept_target(blocker: Pod, enemy: Pod, cps: list[tuple[int, int]]) -> tuple[float, float]:
    bs = max(1.0, length(blocker.vx, blocker.vy))
    ex, ey = enemy.x, enemy.y
    evx, evy = enemy.vx, enemy.vy

    d = math.sqrt(dist2(blocker.x, blocker.y, ex, ey))

    # If we're in reasonable range, prioritize a direct bump: aim at where they'll be next turn.
    if d < 4200:
        tx = ex + evx * 1.0
        ty = ey + evy * 1.0
        tx -= blocker.vx * 0.15
        ty -= blocker.vy * 0.15
        return tx, ty

    t = clamp(d / bs, 1.0, 6.0)

    fx = ex + evx * t
    fy = ey + evy * t

    cpx, cpy = cps[enemy.ncp]
    w = clamp(d / 9000.0, 0.15, 0.55)
    tx = fx * (1.0 - w) + cpx * w
    ty = fy * (1.0 - w) + cpy * w

    tx -= blocker.vx * 0.25
    ty -= blocker.vy * 0.25

    return tx, ty


def boost_ok(
    pod: Pod,
    cps: list[tuple[int, int]],
    cp_count: int,
    dist: float,
    diff: float,
) -> bool:
    if diff > 3.0 or dist < 6500:
        return False

    cx, cy = cps[pod.ncp]
    nx, ny = cps[(pod.ncp + 1) % cp_count]
    approach = angle_to(pod.x, pod.y, cx, cy)
    exit_ang = angle_to(cx, cy, nx, ny)
    if abs(angle_diff(approach, exit_ang)) > 18.0:
        return False

    sp = length(pod.vx, pod.vy)
    return sp < 1350.0


def choose_racer_idx(
    p1: Pod,
    p2: Pod,
    st1: Prog,
    st2: Prog,
    cps: list[tuple[int, int]],
    prev_idx: int,
) -> int:
    # Primary: who has passed more checkpoints in total.
    if st1.passed != st2.passed:
        return 0 if st1.passed > st2.passed else 1

    # Secondary: who is closer to next checkpoint.
    c1x, c1y = cps[p1.ncp]
    c2x, c2y = cps[p2.ncp]
    d1 = math.sqrt(dist2(p1.x, p1.y, c1x, c1y))
    d2 = math.sqrt(dist2(p2.x, p2.y, c2x, c2y))

    # Tertiary: speed.
    s1 = length(p1.vx, p1.vy)
    s2 = length(p2.vx, p2.vy)

    # Hysteresis to stop role thrash (kills opening acceleration).
    # If they're basically tied, keep the previous racer.
    if abs(d1 - d2) < 450.0 and abs(s1 - s2) < 250.0:
        return prev_idx

    # Otherwise pick the pod that is effectively "ahead".
    score1 = d1 - s1 * 5.5
    score2 = d2 - s2 * 5.5
    return 0 if score1 <= score2 else 1


def main() -> None:
    _laps = int(input())
    cp_count = int(input())
    cps = [tuple(map(int, input().split())) for _ in range(cp_count)]

    boost_used = False
    turn = 0
    prev_racer_idx = 0

    my_prog = [Prog(), Prog()]
    op_prog = [Prog(), Prog()]

    while True:
        try:
            p1 = read_pod()
            p2 = read_pod()
            o1 = read_pod()
            o2 = read_pod()
        except EOFError:
            return

        update_progress(my_prog[0], p1, cp_count)
        update_progress(my_prog[1], p2, cp_count)
        update_progress(op_prog[0], o1, cp_count)
        update_progress(op_prog[1], o2, cp_count)

        racer_idx = choose_racer_idx(p1, p2, my_prog[0], my_prog[1], cps, prev_racer_idx)
        prev_racer_idx = racer_idx
        racer, blocker = (p1, p2) if racer_idx == 0 else (p2, p1)

        if progress_key(o1, op_prog[0], cps) >= progress_key(o2, op_prog[1], cps):
            enemy_leader = o1
        else:
            enemy_leader = o2

        rtx, rty, rcmd, picked_boost, rdist = pick_racer_action(
            racer, cps, cp_count, turn=turn, boost_used=boost_used
        )
        if should_shield(racer, o1, o2) and rdist < 3500:
            rcmd = "SHIELD"
        elif picked_boost:
            boost_used = True

        btx, bty = blocker_intercept_target(blocker, enemy_leader, cps)
        bdist = math.sqrt(dist2(blocker.x, blocker.y, btx, bty))
        bdiff = abs(angle_diff(angle_to(blocker.x, blocker.y, btx, bty), blocker.ang))
        bthrust = blocker_thrust(bdiff, bdist)

        if should_shield(blocker, o1, o2):
            bcmd = "SHIELD"
        else:
            bcmd = str(bthrust)

        rline = f"{int(rtx)} {int(rty)} {rcmd}"
        bline = f"{int(btx)} {int(bty)} {bcmd}"

        if racer_idx == 0:
            print(rline)
            print(bline)
        else:
            print(bline)
            print(rline)
        turn += 1


if __name__ == "__main__":
    main()


