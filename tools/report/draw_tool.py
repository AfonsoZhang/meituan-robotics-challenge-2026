#!/usr/bin/env python3
"""Render the pinned, unmodified STEP as nominal CAD views (never a measurement).

Written with OpenAI Codex. Geometry source/version/license scope: the project
manifest's TEAMMATE-FIELD-20261015 and accompanying NOTICE; no source geometry
is edited or re-licensed. Python dependencies are listed beside this script.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SHA = "b21d2a54ce314b660066eafc1e020ba4dc66f7abb9d5c89973ad70dfe09588e9"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-path", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/assets/report-v0.4")
    args = parser.parse_args()
    if args.dependency_path:
        sys.path.insert(0, str(args.dependency_path))
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    # Match namespace extensions to matplotlib when both distro and user
    # installations are present; this changes only this export process.
    import mpl_toolkits
    matching_toolkits = Path(matplotlib.__file__).parent.parent / "mpl_toolkits"
    if matching_toolkits.is_dir():
        mpl_toolkits.__path__ = [str(matching_toolkits), *mpl_toolkits.__path__]
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.collections import PolyCollection
    from matplotlib.lines import Line2D
    from matplotlib.path import Path as MplPath
    from matplotlib.patches import PathPatch, Circle
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from shapely.geometry import Polygon
    from shapely import union_all
    from shapely.geometry.polygon import orient
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRep import BRep_Tool
    from OCP.BRepBndLib import BRepBndLib
    from OCP.Bnd import Bnd_Box
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS
    from OCP.TopLoc import TopLoc_Location

    step = ROOT / "materials/original/hook_v1_b8867f10.step"
    assert hashlib.sha256(step.read_bytes()).hexdigest() == SHA, "STEP source differs"
    reader = STEPControl_Reader()
    assert reader.ReadFile(str(step)) == IFSelect_RetDone
    reader.TransferRoots()
    shape = reader.OneShape()
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    bounds = np.array(box.Get())
    assert np.allclose(bounds[3:] - bounds[:3], [75, 120, 112.5], atol=0.01), bounds
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    assert abs(props.Mass() / 1000 - 122.858) < 0.002
    BRepMesh_IncrementalMesh(shape, 0.12, False, 0.12, True)
    triangles = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = TopoDS.Face_s(explorer.Current())
        loc = TopLoc_Location()
        mesh = BRep_Tool.Triangulation_s(face, loc)
        if mesh is not None:
            nodes = np.array([mesh.Node(i).Transformed(loc.Transformation()).Coord()
                              for i in range(1, mesh.NbNodes() + 1)])
            for i in range(1, mesh.NbTriangles() + 1):
                ids = np.array(mesh.Triangle(i).Get()) - 1
                if face.Orientation() == TopAbs_REVERSED:
                    ids = ids[::-1]
                triangles.append(nodes[ids])
        explorer.Next()
    triangles = np.array(triangles)

    # The four panels explain shape, insertion/lip direction, width, and mounting
    # geometry. These are complementary model views, not independent experiments.
    font = Path.home() / ".local/share/fonts/msyh.ttc"
    if font.exists():
        font_manager.fontManager.addfont(str(font))
    matplotlib.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "DejaVu Sans"],
        "font.size": 8.2, "axes.titlesize": 9.5, "axes.labelsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "svg.fonttype": "none", "pdf.fonttype": 42, "axes.unicode_minus": False,
        "axes.linewidth": 0.6, "text.color": "#20384A", "axes.labelcolor": "#20384A",
    })
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(6.692913386, 7.559055118), facecolor="white")  # 170 × 192 mm
    gs = fig.add_gridspec(2, 2, left=.085, right=.98, bottom=.11, top=.92,
                          wspace=.28, hspace=.39)
    a = fig.add_subplot(gs[0, 0], projection="3d")
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, 0])
    d = fig.add_subplot(gs[1, 1])
    axes = [a, b, c, d]
    # A square physical frame for each panel; units have equal scale in the
    # orthographic panels. The 3-D panel is an oblique model view.
    for ax in axes:
        ax.set_box_aspect(1 if ax is not a else (1, 1, 1))
    titles = ["立体结构", "侧视：穿入 +Z，上翘 −Y", "正视：舌板宽度", "安装方向：X–Z 投影"]
    for index, (ax, title) in enumerate(zip(axes, titles)):
        if ax is a:
            ax.text2D(0, 1.06, "a  " + title, transform=ax.transAxes, fontsize=9.5, fontweight="bold")
        else:
            ax.set_title(chr(97 + index) + "  " + title, loc="left", pad=11, fontweight="bold")

    surface = Poly3DCollection(triangles, facecolors="#6FAAC6",
                               linewidth=0, alpha=1, shade=True, antialiased=False)
    surface.set_edgecolor("none")
    a.add_collection3d(surface)
    a.set(xlim=(-65, 65), ylim=(-15, 125), zlim=(-45, 85))
    a.view_init(elev=24, azim=-57)
    a.set_axis_off()
    for end, label in [((.19,.19),"X"), ((.15,.30),"Y"), ((.07,.37),"Z")]:
        a.annotate("",xy=end,xytext=(.07,.23),xycoords="axes fraction",
                   arrowprops={"arrowstyle":"->","color":"#425C6C","lw":.7})
        a.text2D(end[0],end[1]+.02,label,transform=a.transAxes,fontsize=8)
    a.text2D(.02, .02, "原始 STEP 实体\n安装盘尚未削平", transform=a.transAxes,
             fontsize=8, va="bottom")

    def projection(ax, dims, limits):
        projected = triangles[:, :, dims]
        polygons = [Polygon(t) for t in projected]
        # Union all projected faces, retaining openings. Do not invent 2-D
        # outlines or draw over geometrically inconvenient portions.
        # Micrometre-of-a-millimetre numerical stitching removes floating-point
        # cracks between projected triangles, not any feature of the STEP.
        silhouette = union_all([p for p in polygons if p.area > 1e-9], grid_size=1e-6)
        geoms = [silhouette] if silhouette.geom_type == "Polygon" else silhouette.geoms
        for poly in geoms:
            poly = orient(poly, sign=1)
            vertices, codes = [], []
            for ring in [poly.exterior, *poly.interiors]:
                coords = list(ring.coords)
                vertices.extend(coords)
                codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(coords)-2) + [MplPath.CLOSEPOLY])
            ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor="#D5E7EF",
                                   edgecolor="#447A96", linewidth=.8))
        ax.set_xlim(*limits[0]); ax.set_ylim(*limits[1])
        ax.set_aspect("equal", adjustable="box")
        ax.grid(False)
        ax.set_axisbelow(True)
        ax.tick_params(length=2.5, pad=2)
        for spine in ax.spines.values():
            spine.set_color("#8899A4")

    projection(b, [2, 1], [(-45, 100), (-15, 130)])
    projection(c, [0, 1], [(-72.5, 72.5), (-15, 130)])
    projection(d, [0, 2], [(-72.5, 72.5), (-48, 97)])
    b.set(xlabel="CAD Z / mm", ylabel="CAD Y / mm")
    c.set(xlabel="CAD X / mm", ylabel="CAD Y / mm")
    d.set(xlabel="CAD X / mm", ylabel="CAD Z / mm")
    tcp = np.array([0, 110, 45.0])
    floor = np.array([0, -0.5, 0])
    for ax, dims in [(b, [2, 1]), (c, [0, 1]), (d, [0, 2])]:
        ax.scatter(*tcp[dims], s=22, marker="o", c="#BE3847", edgecolors="white", linewidths=.35, zorder=8)
        ax.scatter(*floor[dims], s=20, marker="D", c="#233D4D", edgecolors="white", linewidths=.35, zorder=8)

    def note(ax, text, point, pos, **kwargs):
        ax.annotate(text, xy=point, xytext=pos, fontsize=8, ha=kwargs.pop("ha", "left"),
                    va="center", arrowprops={"arrowstyle": "->", "color": "#526877", "lw": .65}, **kwargs)
    note(b, "舌板厚 5 mm", (23, 112.5), (-40, 123))
    note(b, "上翘 5 mm\n（−Y 方向）", (74, 105), (95, 77), ha="right")
    note(b, "槽底 Y=−0.5", (0, -.5), (15, 17))
    b.text(18, 58, "Z=−10～75\n包络 85 mm", fontsize=8, va="center")
    c.annotate("", xy=(-22, 120), xytext=(22, 120),
               arrowprops={"arrowstyle": "<->", "color": "#526877", "lw": .65})
    c.text(0, 126, "宽 44 mm", ha="center", va="center", fontsize=8)
    note(c, "安装盘\nØ75 × 15 mm", (34, 2), (68, 30), ha="right")
    d.add_patch(Circle((0,0),31.5, fill=False, edgecolor="#6E8999", linewidth=.65))
    d.add_patch(Circle((0,0),25, fill=False, edgecolor="#9A7134", linewidth=.65, linestyle="--"))
    # The upper two drilled holes are occluded by the stem in this projection.
    # Their nominal outlines are dashed; no through-visibility is fabricated.
    for x in [-25 / np.sqrt(2), 25 / np.sqrt(2)]:
        d.add_patch(Circle((x,25 / np.sqrt(2)), 6.1 / 2, fill=False,
                           edgecolor="#447A96", linewidth=.65, linestyle="--"))
    note(d, "4 × Ø6.1\n孔中心圆 Ø50", (17.6777,17.6777), (68,43), ha="right")
    note(d, "凹槽 Ø63", (-28,-14), (-68,-33))
    fig.suptitle("舌规：削平前名义 CAD", x=.085, ha="left", y=.982,
                 fontsize=12, fontweight="bold")
    legend = [Line2D([],[],marker="o",ls="",color="#BE3847",markersize=4.5,label="规划参考 TCP"),
              Line2D([],[],marker="D",ls="",color="#233D4D",markersize=4,label="凹槽底面中心")]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(.5,.027), ncol=2,
               fontsize=8.3, frameon=False)
    fig.text(.085,.013,"单位：mm；CAD 参考位置与名义尺寸，不作为实物测量结果。", fontsize=8)
    fig.canvas.draw()
    qa_path = ROOT / ".agents/skills/nature-figure/scripts"
    sys.path.insert(0, str(qa_path))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    require_matplotlib_panel_alignment(fig, json_out=out / "v1-cad-views.alignment.json",
                                       axes=axes, panel_ids=["a","b","c","d"], strict=True)
    fig.savefig(out / "v1-cad-views.svg", facecolor="white")
    fig.savefig(out / "v1-cad-views.pdf", facecolor="white")
    fig.savefig(out / "v1-cad-views.png", dpi=300, facecolor="white")
    plt.close(fig)
    (out / "v1-cad-views.source.json").write_text(json.dumps({
        "source_id": "TEAMMATE-FIELD-20261015", "step": str(step.relative_to(ROOT)),
        "step_sha256": SHA, "bounds_mm": bounds.tolist(), "volume_mm3": props.Mass(),
        "triangles": len(triangles), "mesh_deflection_mm": .12, "mesh_angle_rad": .12,
        "projection_union_precision_mm": 1e-6,
        "cad_tcp_mm": tcp.tolist(), "recess_floor_center_mm": floor.tolist(),
        "units": "mm", "scope": "Unmodified nominal STEP before mounting-disc machining; not physical metrology",
        "original_user_image_sha256": "1733263817ae101d4e0b3f14823f2fa332ceace980585d966670cabba8152069",
        "ai_assistance": "OpenAI Codex wrote the plotting and export code; geometry is from the pinned STEP, not generated imagery",
    }, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(out), "triangles": len(triangles), "nominal_bounds_mm": bounds.tolist()}))


if __name__ == "__main__":
    main()
