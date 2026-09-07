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
COLORS = {'yellow': [[20,100,60,35,255,255]]}


def flange(kin, q):
    p, R = np.zeros(3), np.eye(3)
    for angle, (xyz, R0, axis) in zip(q, kin.chain):
        p += R @ xyz
        R = R @ R0 @ Rotation.from_rotvec(axis*angle).as_matrix()
    return p, R


def correction(detections):
    candidates = [d for d in detections if d['color'] == 'yellow']
    if len(candidates) != 1:
        raise ValueError(f'Expected exactly one yellow candidate, got {len(candidates)}')
    d = candidates[0]
    if not all(np.isfinite(d.get(k,float('nan'))) for k in
               ('depth_valid','n_body','body_top_z','handle_top_z','yaw_deg','long_mm','short_mm')):
        raise ValueError('Nonfinite or missing detection geometry')
    if (not d['size_ok'] or d['depth_valid'] < .9 or d['n_body'] < 300
        or abs(d['body_top_z']-.05) > .008
        or abs(d.get('handle_top_z', 0)-.08) > .008
        or abs((d['yaw_deg']-90+90)%180-90) > 3):
        raise ValueError('Yellow geometry/depth/yaw quality gate failed')
    delta = np.array(d['center_xy'])-NOMINAL_YELLOW
    if not np.all(np.isfinite(delta)) or np.linalg.norm(delta) > .010:
        raise ValueError('Correction exceeds the validated local 10 mm envelope')
    return delta


def translated_plan(kin, plan, delta):
    """Shift source approach/lift, blend transfer back to unchanged destination.

    Preserve each original flange orientation and joint branch; reject residuals
    or discontinuities. This is local IK, not a general collision planner.
    """
    result = copy.deepcopy(plan)
    worst = 0.
    for i, point in enumerate(result):
        if i <= 12: weight = i/12
        elif i < 54: weight = 1.
        elif i < 76: weight = (75-i)/22
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
