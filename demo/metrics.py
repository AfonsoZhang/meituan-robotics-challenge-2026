"""Offline geometry and recorded-state checks. Thresholds are demo checks, not scoring."""
import math
import xml.etree.ElementTree as ET

import numpy as np

JOINTS = ['shoulder_joint', 'upperArm_joint', 'foreArm_joint',
          'wrist1_joint', 'wrist2_joint', 'wrist3_joint']
MODELS = ['battery_A_red', 'battery_B_yellow', 'battery_C_green', 'battery_D_blue']
TARGET = np.array([0.0416, 0.3639])


def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr],
                     [sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr], [-sp, cp*sr, cp*cr]])


class Kinematics:
    def __init__(self, urdf):
        root = ET.parse(urdf).getroot()
        self.chain = []
        for name in JOINTS:
            j = root.find(f"joint[@name='{name}']")
            o = j.find('origin')
            xyz = np.fromstring(o.get('xyz', '0 0 0'), sep=' ')
            rpy = np.fromstring(o.get('rpy', '0 0 0'), sep=' ')
            axis = np.fromstring(j.find('axis').get('xyz'), sep=' ')
            axis /= np.linalg.norm(axis)
            self.chain.append((xyz, rpy_matrix(*rpy), axis))

    def points(self, q):
        p, R = np.zeros(3), np.eye(3)
        points = [p.copy()]
        for angle, (xyz, R0, a) in zip(q, self.chain):
            p += R @ xyz
            points.append(p.copy())
            K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
            R = R @ R0 @ (np.eye(3) + math.sin(angle)*K + (1-math.cos(angle))*(K@K))
        points.append(p + R @ np.array([0.030, 0, 0.145]))
        return np.array(points)

    def tcp(self, q):
        return self.points(q)[-1]

    def startup_clear(self, q, batteries):
        """Conservative discrete capsule check adapted from historical ik6.py.

        Used only for a small startup recovery above the work surface, not a
        general collision planner or continuous-collision safety guarantee.
        """
        pts = self.points(q)
        radii = [.055,.055,.050,.045,.045,.040,.022]
        for i in range(7):
            for j in range(i+2,7):
                u,v,r = pts[i+1]-pts[i],pts[j+1]-pts[j],pts[i]-pts[j]
                a,b,c,e,f = float(u@u),float(u@v),float(u@r),float(v@v),float(v@r)
                den = a*e-b*b
                s = float(np.clip((b*f-c*e)/den,0,1)) if den > 1e-12 else 0.
                t = float(np.clip((b*s+f)/max(e,1e-12),0,1))
                s = float(np.clip((b*t-c)/max(a,1e-12),0,1))
                if np.linalg.norm(pts[i]+s*u-pts[j]-t*v) < radii[i]+radii[j]: return False
        for k in range(1,7):
            if pts[k,2] < radii[k-1]+.010: return False
            for pose in batteries.values():
                if (abs(pts[k,0]-pose[0]) < .035+radii[k-1]
                    and abs(pts[k,1]-pose[1]) < .040+radii[k-1] and pts[k,2] < .16): return False
        return bool(pts[-1,2] > .20)


def schedule(plan):
    previous = np.zeros(6)
    elapsed, times = 0., []
    dwell = {'1_预备': 1.5, '2_穿钩': 1.5, '3_承托提升': 1., '5_落台': 1., '6_卸载': 1.}
    for i, point in enumerate(plan):
        q = np.array(point['q'])
        dt = max(.30, float(np.max(np.abs(q-previous)))/.55)
        name = point['name'].split(':')[-1]
        following = plan[i+1]['name'].split(':')[-1] if i+1 < len(plan) else None
        if following != name:
            dt += dwell.get(name, 0)
        elapsed += dt
        times.append(elapsed)
        previous = q
    return times


def quaternion_rpy(q):
    x, y, z, w = q
    return [math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)),
            math.asin(max(-1., min(1., 2*(w*y-z*x)))),
            math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))]


def footprint(pose):
    cx, cy = pose[:2]
    r, p, y = quaternion_rpy(pose[3:])
    # Only apply the upright rectangle approximation to near-upright batteries.
    if max(abs(r), abs(p)) > math.radians(5):
        return {'upright': False, 'coverage': None, 'inside_outer': False}
    R = np.array([[math.cos(y), -math.sin(y)], [math.sin(y), math.cos(y)]])
    n = 400
    x, yy = np.meshgrid((np.arange(n)+.5)/n*.070-.035, (np.arange(n)+.5)/n*.080-.040)
    pts = np.column_stack([x.ravel(), yy.ravel()]) @ R.T + [cx, cy]
    coverage = float(np.mean(np.sum((pts-TARGET)**2, axis=1) <= .040**2))
    corners = np.array([[-.035,-.040], [-.035,.040], [.035,-.040], [.035,.040]]) @ R.T + [cx, cy]
    return {'upright': True, 'coverage': coverage,
            'inside_outer': bool(np.all(np.abs(corners-TARGET) <= .075))}


def evaluate(samples, initial, end_time):
    """Require >=3 s of fresh post-motion observations; retain all bystander checks."""
    recent = [s for s in samples if s['t'] >= end_time]
    result = {'scope': 'Single yellow-to-P1 simulation checks; not full competition scoring',
              'contact_collision_check': 'not instrumented',
              'thresholds': {'stability_s': 3., 'stability_translation_m': .002,
                             'stability_rotation_deg': 2., 'bystander_translation_m': .002,
                             'bystander_rotation_deg': 2., 'upright_deg': 5.}}
    if len(recent) < 2 or recent[-1]['t']-recent[0]['t'] < 3.:
        return dict(result, passed=False, reason='Insufficient post-motion observations')
    if max(b['t']-a['t'] for a,b in zip(recent,recent[1:])) > .25:
        return dict(result, passed=False, reason='Gaps in post-motion state observations')
    final = recent[-1]['poses'][MODELS[1]]
    geo = footprint(final)
    positions = np.array([s['poses'][MODELS[1]][:3] for s in recent])
    translation = float(np.max(np.linalg.norm(positions-positions[-1], axis=1)))
    def rotation(a, b):
        a, b = np.array(a[3:]), np.array(b[3:])
        return math.degrees(2*math.acos(float(np.clip(abs(a@b)/(np.linalg.norm(a)*np.linalg.norm(b)), 0, 1))))
    rotation_span = max(rotation(s['poses'][MODELS[1]], final) for s in recent)
    bystanders = {}
    for name in (MODELS[0], MODELS[2], MODELS[3]):
        bystanders[name] = {'max_translation_m': max(float(np.linalg.norm(np.array(s['poses'][name][:3])-initial[name][:3])) for s in samples),
                            'max_rotation_deg': max(rotation(s['poses'][name], initial[name]) for s in samples)}
    run_start, longest, previous = None, 0., None
    for s in samples:
        lifted = s['poses'][MODELS[1]][2] > .02
        if previous is not None and s['t']-previous > .25:
            run_start = None
        if lifted:
            if run_start is None: run_start = s['t']
            longest = max(longest, s['t']-run_start)
        else:
            run_start = None
        previous = s['t']
    ok = (geo['upright'] and geo['coverage'] >= .70 and geo['inside_outer']
          and abs(final[2]) <= .005 and translation <= .002 and rotation_span <= 2.
          and longest >= 2. and all(v['max_translation_m'] <= .002 and v['max_rotation_deg'] <= 2. for v in bystanders.values()))
    return dict(result, passed=bool(ok), final_pose=final, footprint=geo,
                center_error_mm=float(np.linalg.norm(np.array(final[:2])-TARGET)*1000),
                stability_translation_m=translation, stability_rotation_deg=rotation_span,
                observed_lift_duration_s=longest, bystanders=bystanders)
