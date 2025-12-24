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

    aimx = bx - pod.vx * corr
    aimy = by - pod.vy * corr

    desired = angle_to(pod.x, pod.y, aimx, aimy)
    diff = abs(angle_diff(desired, pod.ang))

    return aimx, aimy, dist, diff


def thrust_for_angle_and_dist(diff: float, dist: float, speed: float) -> int:
    t = 100

    if diff > 95:
        t = 0
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


def main() -> None:
    _laps = int(input())
    cp_count = int(input())
    cps = [tuple(map(int, input().split())) for _ in range(cp_count)]

    boost_used = False

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

        if progress_key(p1, my_prog[0], cps) >= progress_key(p2, my_prog[1], cps):
            racer, blocker = p1, p2
            racer_idx = 0
        else:
            racer, blocker = p2, p1
            racer_idx = 1

        if progress_key(o1, op_prog[0], cps) >= progress_key(o2, op_prog[1], cps):
            enemy_leader = o1
        else:
            enemy_leader = o2

        rtx, rty, rdist, rdiff = projected_target_for_checkpoint(racer, cps, cp_count)
        rs = length(racer.vx, racer.vy)
        rthrust = thrust_for_angle_and_dist(rdiff, rdist, rs)

        if should_shield(racer, o1, o2) and rdist < 3500:
            rcmd = "SHIELD"
        else:
            if (not boost_used) and boost_ok(racer, cps, cp_count, rdist, rdiff):
                rcmd = "BOOST"
                boost_used = True
            else:
                rcmd = str(rthrust)

        btx, bty = blocker_intercept_target(blocker, enemy_leader, cps)
        bdist = math.sqrt(dist2(blocker.x, blocker.y, btx, bty))
        bdiff = abs(angle_diff(angle_to(blocker.x, blocker.y, btx, bty), blocker.ang))
        bs = length(blocker.vx, blocker.vy)
        bthrust = thrust_for_angle_and_dist(bdiff, bdist, bs)

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


if __name__ == "__main__":
    main()


