"""道具电池的传统视觉识别与定位（纯 numpy/OpenCV，不依赖 ROS，便于离线回放与单测）。

管线：HSV 颜色分割 -> 形态学 -> 连通域 -> 深度反投影到基座系 -> 按高度分层 -> 拟合足迹与朝向。

关键点：
  * 深度与彩色是两个不同视场的相机。本模块按「两光心重合」做像素映射，
    这在仿真里成立（外参取 0），**实机不成立**：D435i 彩色与深度光心有基线，
    必须先做深度对齐（librealsense 的 align 或标定外参），见 RS-ALIGN。
  * 用高度分层区分本体顶面（约 0.050 m）与提手横梁顶面（约 0.080 m），
    对应 battery-geometry.md 里「模型包含两个明显的高度层」的做法。
  * 电池足迹 70x80 接近正方且 180° 对称，朝向只能定到 [0,180)。
"""
import numpy as np
import cv2

NOMINAL = dict(body_w=0.070, body_l=0.080, body_h=0.050, top_h=0.080)


def hsv_mask(bgr, ranges):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo_h, lo_s, lo_v, hi_h, hi_s, hi_v in ranges:
        m |= cv2.inRange(hsv, (lo_h, lo_s, lo_v), (hi_h, hi_s, hi_v))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)


def color_to_depth_px(uv, K_color, K_depth):
    """彩色像素 -> 深度像素。仅在两光心重合时成立（仿真）；实机须改用对齐后的深度。"""
    u, v = uv[:, 0], uv[:, 1]
    x = (u - K_color[0, 2]) / K_color[0, 0]
    y = (v - K_color[1, 2]) / K_color[1, 1]
    ud = np.round(x * K_depth[0, 0] + K_depth[0, 2]).astype(int)
    vd = np.round(y * K_depth[1, 1] + K_depth[1, 2]).astype(int)
    return ud, vd


def deproject(ud, vd, z, K_depth):
    x = (ud - K_depth[0, 2]) * z / K_depth[0, 0]
    y = (vd - K_depth[1, 2]) * z / K_depth[1, 1]
    return np.stack([x, y, z], 1)


def fit_footprint(xy_m):
    """对 xy 点集拟合最小外接矩形，返回中心、长短边(mm)、长轴方向(deg, [0,180))。"""
    pts = (xy_m * 1000.0).astype(np.float32)
    (cx, cy), (w, h), ang = cv2.minAreaRect(pts)
    if w < h:
        w, h, ang = h, w, ang + 90.0        # w 恒为长边
    return np.array([cx, cy]) / 1000.0, (w, h), ang % 180.0


def detect(bgr, depth, K_color, K_depth, T_base_cam, colors,
           min_pixels=300, body_band=(0.030, 0.066), handle_band=(0.066, 0.095)):
    """返回每个候选的字典列表。T_base_cam 为 4x4，把深度光学系点变到 base_link。"""
    R, t = T_base_cam[:3, :3], T_base_cam[:3, 3]
    H, W = depth.shape
    out = []
    for name, ranges in colors.items():
        mask = hsv_mask(bgr, ranges)
        # 内缩一圈，避开物体边缘的混合像素
        mask_in = cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        n, lab, stats, _ = cv2.connectedComponentsWithStats(mask_in, 8)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] < min_pixels:
                continue
            vs, us = np.nonzero(lab == i)
            uv = np.stack([us, vs], 1)
            ud, vd = color_to_depth_px(uv, K_color, K_depth)
            ok = (ud >= 0) & (ud < W) & (vd >= 0) & (vd < H)
            ud, vd = ud[ok], vd[ok]
            z = depth[vd, ud]
            good = np.isfinite(z) & (z > 0)
            if good.sum() < 50:
                continue
            P_cam = deproject(ud[good], vd[good], z[good], K_depth)
            P = P_cam @ R.T + t                      # -> base_link
            body = P[(P[:, 2] >= body_band[0]) & (P[:, 2] < body_band[1])]
            handle = P[(P[:, 2] >= handle_band[0]) & (P[:, 2] < handle_band[1])]
            if len(body) < 50:
                continue
            center, (long_mm, short_mm), yaw = fit_footprint(body[:, :2])
            det = dict(color=name, pixels=int(stats[i, cv2.CC_STAT_AREA]),
                       depth_valid=float(good.mean()),
                       center_xy=center, body_top_z=float(np.median(body[:, 2])),
                       long_mm=long_mm, short_mm=short_mm, yaw_deg=yaw,
                       n_body=int(len(body)), n_handle=int(len(handle)))
            if len(handle) >= 30:
                hc, (hl, hs), hyaw = fit_footprint(handle[:, :2])
                det.update(handle_top_z=float(np.median(handle[:, 2])),
                           handle_yaw_deg=hyaw, handle_long_mm=hl)
            # 尺寸合理性：与名义 70x80 比对，超差就标记
            det["size_ok"] = bool(abs(long_mm - NOMINAL["body_l"] * 1000) < 15
                                  and abs(short_mm - NOMINAL["body_w"] * 1000) < 15)
            out.append(det)
    return out
