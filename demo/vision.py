"""Simulation-only RGB-D snapshot gates and local translation IK.

Detector adapted from project meituan_vision (Claude Code); orchestration and
local correction by OpenAI Codex. No model-state inputs enter these functions.
"""
import copy
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

OBSERVER = np.array([2.601396586588973, .14741121175982763, 1.1057746982330148,
                     -.6131218224295513, -4.707210372114571, -4.128890581870104])
NOMINAL_YELLOW = np.array([-.1735, .3455])
COLORS = {'yellow': [[20,100,60,35,255,255]],
          'green': [[40,80,40,85,255,255]], 'blue': [[100,100,60,130,255,255]]}
NOMINAL_CENTERS = {'yellow': NOMINAL_YELLOW, 'green':np.array([-.2527,.2578]),
                   'blue':np.array([-.1735,.2578])}
SIDE_OBSERVER = np.array([2.5161729751199946,-.3316729568224258,.5645037362267181,
                          -.670400750662479,-4.70966690288651,.5400883461731194])


def flange(kin, q):
    p, R = np.zeros(3), np.eye(3)
    for angle, (xyz, R0, axis) in zip(q, kin.chain):
        p += R @ xyz
        R = R @ R0 @ Rotation.from_rotvec(axis*angle).as_matrix()
    return p, R


def correction(detections, color="yellow"):
    candidates = [d for d in detections if d['color'] == color]
    if len(candidates) != 1:
        raise ValueError(f'Expected exactly one {color} candidate, got {len(candidates)}')
    d = candidates[0]
    if not all(np.isfinite(d.get(k,float('nan'))) for k in
               ('depth_valid','n_body','body_top_z','handle_top_z','yaw_deg','long_mm','short_mm')):
        raise ValueError('Nonfinite or missing detection geometry')
    if (not d['size_ok'] or d['depth_valid'] < .9 or d['n_body'] < 300
        or abs(d['body_top_z']-.05) > .008
        or abs(d.get('handle_top_z', 0)-.08) > .008
        or abs((d['yaw_deg']-90+90)%180-90) > 3):
        raise ValueError('Target geometry/depth/yaw quality gate failed')
    delta = np.array(d['center_xy'])-NOMINAL_CENTERS[color]
    if not np.all(np.isfinite(delta)) or np.linalg.norm(delta) > .010:
        raise ValueError('Correction exceeds the validated local 10 mm envelope')
    return delta


def translated_plan(kin, plan, delta, transition_points=None):
    """Shift source approach/lift, blend transfer back to unchanged destination.

    Preserve each original flange orientation and joint branch; reject residuals
    or discontinuities. This is local IK, not a general collision planner.
    """
    result = copy.deepcopy(plan)
    worst = 0.
    approach, transfer, lower = 12, 54, 76
    if all('name' in p for p in plan):
        approach = next(i for i,p in enumerate(plan) if p['name'].split(':')[-1].startswith('0_'))
        transfer = next(i for i,p in enumerate(plan) if p['name'].split(':')[-1].startswith('4_'))
        lower = next(i for i,p in enumerate(plan) if p['name'].split(':')[-1].startswith('5_'))
    for i, point in enumerate(result):
        if i <= approach:
            span = approach if transition_points is None else min(approach,transition_points)
            weight = max(0.,(i-(approach-span))/span)
        elif i < transfer: weight = 1.
        elif i < lower: weight = (lower-1-i)/(lower-transfer)
        else: weight = 0.
        if not weight: continue
        original = np.array(plan[i]['q'])
        p, R = flange(kin, original)
        target = p + np.r_[delta*weight, 0.]
        def residual(q):
            pos, rot = flange(kin,q)
            return np.r_[pos-target, .1*Rotation.from_matrix(R.T@rot).as_rotvec()]
        fit = least_squares(residual, original, bounds=(np.maximum(original-.15,np.array(kin.limits)[:,0]),
                                    np.minimum(original+.15,np.array(kin.limits)[:,1])),
                            xtol=1e-11,ftol=1e-11,gtol=1e-11,max_nfev=100)
        error = float(np.linalg.norm(residual(fit.x)))
        if not fit.success or error > 1e-5: raise ValueError(f'Local IK rejected waypoint {i}: {error}')
        for key in ('col','pe','ae'):
            if key in point: point['nominal_'+key] = point.pop(key)
        point['ik_weighted_residual'] = error
        point['collision_check'] = 'Not recomputed; local bounded perturbation of nominal trajectory'
        point['q'] = fit.x.tolist()
        point['tcp'] = kin.tcp(fit.x).tolist()
        point['vision_translation_weight'] = weight
        worst = max(worst,error)
    for a,b,oa,ob in zip(result,result[1:],plan,plan[1:]):
        if np.max(np.abs(np.subtract(b['q'],a['q']))) > np.max(np.abs(np.subtract(ob['q'],oa['q'])))+.04:
            raise ValueError('Correction introduced a joint discontinuity')
    return result, worst
