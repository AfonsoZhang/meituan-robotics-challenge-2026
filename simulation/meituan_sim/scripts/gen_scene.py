#!/usr/bin/env python3
"""按底图矢量坐标生成 Gazebo 场景（道具电池模型 + 底图模型 + 两个 world）。

坐标来源：materials/original/《2026年挑战赛任务底图》.pdf 的矢量图元 bbox（fitz get_drawings），
页面 700x540 mm，原点在页面左上、y 向下。世界系以机械臂底座参考圆圆心为原点：
    x_world = (mx - 393.0) / 1000
    y_world = -(my - 439.6) / 1000
z=0 取工作台面（本场景直接用 ground_plane 当台面，机器人底座固定在 z=0）。

电池几何来自 BATTERY-DRAWING 的名义标注（暂按 mm）：本体 70(x)x80(y)x50(z)，
提手横梁 70x26x10 顶面 z=80，两立柱各 10(x)x26(y)x20(z)，孔口净高 20。
颜色取 FAQ 示例出现的红/黄/绿/蓝，实物颜色待核（Q08）。
"""
import os
import argparse

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS, WORLDS = os.path.join(PKG, "models"), os.path.join(PKG, "worlds")
BASE_MX, BASE_MY = 393.0, 439.6          # 底座参考圆圆心（页面坐标 mm）


def w(mx, my):                            # 页面 mm -> 世界 m
    return round((mx - BASE_MX) / 1000.0, 6), round(-(my - BASE_MY) / 1000.0, 6)


LAYOUT = {
    "p1": {"batteries": {"A": (178.2, 94.1), "B": (257.4, 94.1),
                         "C": (178.2, 181.8), "D": (257.4, 181.8)},
           "targets": {"T0": (508.0, 139.8)}},
    "p2": {"batteries": {"A": (140.3, 94.1), "B": (219.5, 94.1),
                         "C": (140.3, 181.8), "D": (219.5, 181.8)},
           "targets": {"P1": (434.6, 75.7), "P2": (609.6, 75.7), "P3": (609.6, 250.7)}},
}
COLORS = {"red": "1 0 0 1", "yellow": "1 0.85 0 1",
          "green": "0 0.7 0.15 1", "blue": "0 0.25 1 1"}
# A/B/C/D 位的颜色分配是本项目自定，仅用于仿真区分；正式对应关系由比赛日口令决定
SLOT_COLOR = {"A": "red", "B": "yellow", "C": "green", "D": "blue"}

MASS = 0.225                              # FAQ p5 给 200-250 g，取中值
BODY = (0.070, 0.080, 0.050)
BAR = (0.070, 0.026, 0.010)               # 横梁，顶面 z=0.080
POST = (0.010, 0.026, 0.020)              # 立柱，z 从 0.050 到 0.070


def box_inertia(m, sx, sy, sz):
    return (m * (sy * sy + sz * sz) / 12, m * (sx * sx + sz * sz) / 12,
            m * (sx * sx + sy * sy) / 12)


def battery_sdf(name, rgba):
    ixx, iyy, izz = box_inertia(MASS, BODY[0], BODY[1], 0.080)
    parts = []
    for tag in ("collision", "visual"):
        for i, (size, z, xoff) in enumerate([
                (BODY, BODY[2] / 2, 0.0),
                (BAR, 0.080 - BAR[2] / 2, 0.0),
                (POST, 0.050 + POST[2] / 2, -0.030),
                (POST, 0.050 + POST[2] / 2, +0.030)]):
            sx, sy, sz = size
            mat = f"""
        <material>
          <ambient>{rgba}</ambient><diffuse>{rgba}</diffuse>
          <specular>0.1 0.1 0.1 1</specular>
        </material>""" if tag == "visual" else ""
            parts.append(f"""
      <{tag} name="{tag}_{i}">
        <pose>{xoff} 0 {z:.4f} 0 0 0</pose>
        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>{mat}
      </{tag}>""")
    return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <link name="link">
      <inertial>
        <mass>{MASS}</mass>
        <pose>0 0 0.030 0 0 0</pose>
        <inertia><ixx>{ixx:.6f}</ixx><iyy>{iyy:.6f}</iyy><izz>{izz:.6f}</izz>
                 <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia>
      </inertial>{''.join(parts)}
    </link>
  </model>
</sdf>
"""


# 底图区域（页面坐标 mm，直接取自 PDF 矢量图元 bbox），按页分别列出
MAP_ZONES = {
    "p1": {
        "batt_area":  ("rect", (67.8, 0.4, 367.8, 240.4)),
        "batt_slots": [("rect", (143.2, 54.1, 213.2, 134.1)), ("rect", (222.4, 54.1, 292.4, 134.1)),
                       ("rect", (143.2, 141.8, 213.2, 221.8)), ("rect", (222.4, 141.8, 292.4, 221.8))],
        "targets":    [("rect", (408.0, 89.8, 608.0, 189.8))],          # T0 200x100
        "inners":     [],
    },
    "p2": {
        "batt_area":  ("rect", (29.9, 0.4, 329.9, 240.4)),
        "batt_slots": [("rect", (105.3, 54.1, 175.3, 134.1)), ("rect", (184.5, 54.1, 254.5, 134.1)),
                       ("rect", (105.3, 141.8, 175.3, 221.8)), ("rect", (184.5, 141.8, 254.5, 221.8))],
        "targets":    [("rect", (359.6, 0.7, 509.6, 150.7)), ("rect", (534.6, 0.7, 684.6, 150.7)),
                       ("rect", (534.6, 175.7, 684.6, 325.7))],         # 外框 150x150
        "inners":     [("circ", (434.6, 75.7, 40.0)), ("circ", (609.6, 75.7, 40.0)),
                       ("circ", (609.6, 250.7, 40.0))],                 # 内框 直径 80
    },
}
BASE_CIRCLE = (393.0, 439.6, 100.0)     # 机械臂底座参考圆，直径 200


def _plate(name, page_rect, z, rgba):
    x0, y0, x1, y1 = page_rect
    cx, cy = w((x0 + x1) / 2, (y0 + y1) / 2)
    return f"""
      <visual name="{name}">
        <pose>{cx} {cy} {z} 0 0 0</pose>
        <geometry><box><size>{abs(x1-x0)/1000:.4f} {abs(y1-y0)/1000:.4f} 0.0004</size></box></geometry>
        <material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse></material>
      </visual>"""


def _disc(name, page_circ, z, rgba):
    mx, my, r = page_circ
    cx, cy = w(mx, my)
    return f"""
      <visual name="{name}">
        <pose>{cx} {cy} {z} 0 0 0</pose>
        <geometry><cylinder><radius>{r/1000:.4f}</radius><length>0.0004</length></cylinder></geometry>
        <material><ambient>{rgba}</ambient><diffuse>{rgba}</diffuse></material>
      </visual>"""


def map_sdf(page):
    """底图用几何体画，不用贴图。

    Gazebo Classic 对薄盒体的 UV 映射带镜像+旋转，贴图方式实测最大偏 454 mm，
    补偿后仍有 46-86 mm 残差。而 P1-P3 内框正是 70% 覆盖率的判定基准，
    印刷位置偏移会误导肉眼判断，故改为按 PDF 矢量坐标直接生成几何体——按构造即精确。
    代价是没有中文标注文字。
    """
    Z = MAP_ZONES[page]
    v = [_plate("plate", (0, 0, 700, 540), 0.0005, "0.93 0.93 0.90 1")]
    v.append(_plate("batt_area", Z["batt_area"][1], 0.0010, "0.86 0.86 0.83 1"))
    for i, (_, r) in enumerate(Z["batt_slots"]):
        v.append(_plate(f"slot_{i}", r, 0.0014, "0.72 0.72 0.70 1"))
    for i, (_, r) in enumerate(Z["targets"]):
        v.append(_plate(f"target_{i}", r, 0.0010, "0.80 0.84 0.88 1"))
    for i, (_, c) in enumerate(Z["inners"]):
        v.append(_disc(f"inner_{i}", c, 0.0014, "0.45 0.62 0.80 1"))
    v.append(_disc("base_circle", BASE_CIRCLE, 0.0010, "0.75 0.72 0.68 1"))
    return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="task_map_{page}">
    <static>true</static>
    <link name="link">{''.join(v)}
    </link>
  </model>
</sdf>
"""


def config(name):
    return f"""<?xml version="1.0"?>
<model><name>{name}</name><version>1.0</version><sdf version="1.6">model.sdf</sdf>
  <description>2026 美团挑战赛仿真场景资产（由 meituan_sim/scripts/gen_scene.py 生成）</description>
</model>
"""


def world(page):
    L = LAYOUT[page]
    items = [f"""
    <include><uri>model://task_map_{page}</uri>
      <pose>0 0 0 0 0 0</pose></include>"""]
    for slot, (mx, my) in L["batteries"].items():
        x, y = w(mx, my)
        c = SLOT_COLOR[slot]
        items.append(f"""
    <include><uri>model://battery_{c}</uri><name>battery_{slot}_{c}</name>
      <pose>{x} {y} 0 0 0 0</pose></include>""")
    marks = "".join(f"\n         {k} 页面({mx},{my}) -> 世界({w(mx, my)[0]}, {w(mx, my)[1]})"
                    for k, (mx, my) in L["targets"].items())
    return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="task_{page}">
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>
    <physics type="ode"><max_step_size>0.001</max_step_size>
      <real_time_update_rate>1000</real_time_update_rate></physics>{''.join(items)}
    <!-- 目标位（仅记录坐标，不建实体）：{marks}
    -->
  </world>
</sdf>
"""


def main():
    global MODELS, WORLDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default=PKG, help='Destination for generated models/ and worlds/')
    args = parser.parse_args()
    MODELS = os.path.join(os.path.abspath(args.output_dir), 'models')
    WORLDS = os.path.join(os.path.abspath(args.output_dir), 'worlds')
    for c, rgba in COLORS.items():
        d = os.path.join(MODELS, f"battery_{c}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "model.sdf"), "w").write(battery_sdf(f"battery_{c}", rgba))
        open(os.path.join(d, "model.config"), "w").write(config(f"battery_{c}"))
    os.makedirs(WORLDS, exist_ok=True)
    for page in ("p1", "p2"):
        d = os.path.join(MODELS, f"task_map_{page}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "model.sdf"), "w").write(map_sdf(page))
        open(os.path.join(d, "model.config"), "w").write(config(f"task_map_{page}"))
        open(os.path.join(WORLDS, f"task_{page}.world"), "w").write(world(page))
    print("各电池世界坐标 (m)：")
    for page in ("p1", "p2"):
        for slot, (mx, my) in LAYOUT[page]["batteries"].items():
            x, y = w(mx, my)
            print(f"  {page} {slot}({SLOT_COLOR[slot]:6s}) x={x:+.4f} y={y:+.4f}  "
                  f"距底座 {(x * x + y * y) ** 0.5 * 1000:6.1f} mm")
    print("\n目标位世界坐标 (m)：")
    for page in ("p1", "p2"):
        for k, (mx, my) in LAYOUT[page]["targets"].items():
            x, y = w(mx, my)
            print(f"  {page} {k:3s} x={x:+.4f} y={y:+.4f}  距底座 {(x * x + y * y) ** 0.5 * 1000:6.1f} mm")


if __name__ == "__main__":
    main()
