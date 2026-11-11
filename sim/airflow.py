"""Airflow through the Mk I, driven by the fans' own curves.

Two steps, each talking to a running desktop app over its MCP bridge:

  python3 sim/airflow.py geometry SPACING            SolidCraft: build the airflow geometry
  python3 sim/airflow.py run SPACING CASE [END_TIME]  FieldCraft: solve one case

SPACING is the grid in mm (1 for results, 2 only to check a set-up is stable).
CASE is one of CASES below. SOLIDCRAFT_MCP and FIELDCRAFT_MCP hold the command
lines that start each bridge. Output goes to sim/out/.

The case stands on its feet on the floor of a closed box of air, so what
leaves the top comes back down the outside and in underneath. Each fan is a
zone carrying its pressure-flow curve, and the solver finds where the curves
meet the case's resistance. Open inlets and outlets would not stay stable in
the nova-reactor study, which this set-up follows.

Simplified against mechanical/mk1.py: sheet is two cells thick so the grid
cannot leak through it, the hex mesh is a pressure loss over each panel's
meshed area, the PSU is a solid block (its own fan and exhaust are not
modelled), and the heatsink is a base with coarse horizontal fins.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mechanical"))
import mk1 as M  # noqa: E402

OUT = os.path.join(M.REPO, "sim", "out")

# mm-t-s units: density in t/mm3, viscosity in MPa s, pressure in MPa
PA = 1e-6
M3H = 1e9 / 3600     # mm3/s
AIR_DENSITY, AIR_VISCOSITY = 1.16e-12, 1.85e-11

# Shut-off pressure (mm H2O) and free flow (m3/h) at full speed, from Noctua's
# specifications. Noctua publishes no curve between the two, so a straight line is assumed.
NF_A14 = (2.08, 140.2)       # 1500 rpm
NF_A12X15 = (1.53, 94.2)     # 1850 rpm

# Thin perforated plate at 70 % open (10.4 mm hexagons on a 12.45 x 10.375 pitch), Idelchik.
MESH_LOSS = 1.2

# Fan speeds as a fraction of full: bottom, top, CPU. None leaves the fan out (its frame stays).
CASES = {
    "all-100": (1.0, 1.0, 1.0),
    "all-50": (0.5, 0.5, 0.5),
    "cpu-only-100": (None, None, 1.0),
    "bottom-only-100": (1.0, None, 1.0),
}

X0, X1 = -M.T, M.SHELL_XF
Y0, Y1 = M.SHELL_Y0, M.SHELL_Y1
Z0, Z1 = M.SHELL_Z0, M.SHELL_Z1
FLOOR = -20.0
BOX_MIN, BOX_MAX = [-32, -34, FLOOR], [208, 238, 300]
MESH_X, MESH_Y = (10, M.LX - 10), (10, M.LY - 10)
FX, FY = M.CENTRE
HX, HZ = M.BOARD_X + 18.54, M.BOARD_Z + M.BOARD - 136.06
CX, CZ = HX + 63.1, HZ + 63.1


def geometry_path(spacing):
    return os.path.join(OUT, "airflow-mk1-%gmm.solidcraft" % spacing)


def solids(w):
    """(name, x0, x1, y0, y1, z0, z1) for every obstacle, with sheet w thick."""
    b = []
    b.append(("A_side_cpu", X0, X1, Y0, Y0 + w, Z0, Z1))
    b.append(("A_side_psu", X0, X1, Y1 - w, Y1, Z0, Z1))
    b.append(("A_front", X1 - w, X1, Y0, Y1, Z0, Z1))
    b.append(("A_rear", X0, X0 + w, Y0, Y1, Z0, Z1))
    for n, za, zb in (("bottom", Z0, Z0 + w), ("top", Z1 - w, Z1)):
        b.append(("A_%s_a" % n, X0, X1, Y0, MESH_Y[0], za, zb))
        b.append(("A_%s_b" % n, X0, X1, MESH_Y[1], Y1, za, zb))
        b.append(("A_%s_c" % n, X0, MESH_X[0], MESH_Y[0], MESH_Y[1], za, zb))
        b.append(("A_%s_d" % n, MESH_X[1], X1, MESH_Y[0], MESH_Y[1], za, zb))
    for n, za, zb in (("fanb", Z0 + w, M.FAN_T), ("fant", M.LZ - M.FAN_T, Z1 - w)):
        b += frame("A_%s" % n, "z", FX, FY, 70, w, za, zb)
    b += frame("A_fanc", "y", CX, CZ, 60, w, M.PLENUM, M.PLENUM + M.CPU_FAN)
    # tray with its cable opening, shelf, PSU
    ty = M.PSU_Y - w
    b.append(("A_tray_a", 0, 142, ty, M.PSU_Y, M.BASE, M.TRAY_TOP))
    b.append(("A_tray_b", 160, M.LX, ty, M.PSU_Y, M.BASE, M.TRAY_TOP))
    b.append(("A_tray_c", 142, 160, ty, M.PSU_Y, M.BASE, 60))
    b.append(("A_tray_d", 142, 160, ty, M.PSU_Y, 130, M.TRAY_TOP))
    b.append(("A_shelf", 0, M.LX, M.PSU_Y, M.PSU_Y + M.PSU[1], M.SHELF_Z - w, M.SHELF_Z))
    b.append(("A_psu", 0, M.PSU[0], M.PSU_Y, M.PSU_Y + M.PSU[1], M.SHELF_Z, M.SHELF_Z + M.PSU[2]))
    # board, ports, heatsink
    bz = M.BOARD_Z
    b.append(("A_board", M.BOARD_X, M.BOARD_X + M.BOARD, M.BOARD_Y, M.BOARD_Y + w, bz, bz + M.BOARD))
    b.append(("A_ports", 0, 20, M.BOARD_Y - 31.1, M.BOARD_Y, bz + 8, bz + 152))
    hy = M.BOARD_Y - M.HEATSINK
    b.append(("A_hs_base", HX, HX + 126.2, M.BOARD_Y - 6, M.BOARD_Y, HZ, HZ + 126.2))
    z, i = HZ, 0
    while z + w <= HZ + 126.2:
        b.append(("A_hs_fin%02d" % i, HX, HX + 126.2, hy, M.BOARD_Y - 6, z, z + w))
        z += 3 * w
        i += 1
    for i, (x, y) in enumerate(M.FEET):
        b.append(("A_foot%d" % i, x - 9, x + 9, y - 9, y + 9, FLOOR, Z0))
    return b


def frame(name, axis, c1, c2, half, w, a, b):
    """Four walls round a fan, which blows along `axis` from a to b."""
    out = []
    for k, (p0, p1, q0, q1) in enumerate(((c1 - half, c1 + half, c2 - half, c2 - half + w),
                                          (c1 - half, c1 + half, c2 + half - w, c2 + half),
                                          (c1 - half, c1 - half + w, c2 - half + w, c2 + half - w),
                                          (c1 + half - w, c1 + half, c2 - half + w, c2 + half - w))):
        if axis == "z":
            out.append(("%s_%d" % (name, k), p0, p1, q0, q1, a, b))
        else:
            out.append(("%s_%d" % (name, k), p0, p1, a, b, q0, q1))
    return out


def geometry(spacing):
    os.makedirs(OUT, exist_ok=True)
    sc = M.Bridge()
    sc.call("new_design")
    steps = [("solid.box", {"length": x1 - x0, "width": y1 - y0, "height": z1 - z0, "corner": [x0, y0, z0],
                            "operation": "new", "body_name": n}) for n, x0, x1, y0, y1, z0, z1 in solids(2 * spacing)]
    sc.batch(steps, "airflow geometry")
    sc.call("save", {"path": geometry_path(spacing)})
    sc.call("new_design")
    sc.call("open", {"path": M.DESIGN})  # leave the app on the real design
    print("wrote", geometry_path(spacing), len(steps), "bodies")


class Field(M.Bridge):
    ENV = "FIELDCRAFT_MCP"

    def execute(self, command, params=None):
        r = self.call("execute", {"command": command, "params": params or {}})
        return r.get("result", r) if isinstance(r, dict) else r


def curve(fan, s):
    return [[0, fan[0] * 9.80665 * PA * s * s], [fan[1] * M3H * s, 0]]


def run(spacing, case, end_time):
    w = 2 * spacing
    fc = Field()
    fc.call("open", {"path": geometry_path(spacing)})
    bodies = [b["name"] for b in fc.call("inspect_model")["bodies"]]
    try:
        fc.execute("model.material.create", {"name": "Air", "density": AIR_DENSITY,
                                             "fluid": {"type": "newtonian", "viscosity": AIR_VISCOSITY}})
    except SystemExit as e:
        if "already exists" not in str(e):
            raise
    sb, st, sc_ = CASES[case]
    fans = []
    if sb:
        fans.append({"name": "bottom", "min": [FX - 70 + w, FY - 70 + w, Z0 + w], "max": [FX + 70 - w, FY + 70 - w, M.FAN_T],
                     "direction": "+z", "curve": curve(NF_A14, sb)})
    if st:
        fans.append({"name": "top", "min": [FX - 70 + w, FY - 70 + w, M.LZ - M.FAN_T], "max": [FX + 70 - w, FY + 70 - w, Z1 - w],
                     "direction": "+z", "curve": curve(NF_A14, st)})
    if sc_:
        fans.append({"name": "cpu", "min": [CX - 60 + w, M.PLENUM, CZ - 60 + w], "max": [CX + 60 - w, M.PLENUM + M.CPU_FAN, CZ + 60 - w],
                     "direction": "+y", "curve": curve(NF_A12X15, sc_)})
    loss = {"type": "loss_coefficient", "coefficient": MESH_LOSS}
    name = "%s_%gmm" % (case, spacing)
    domain = {"name": name, "material": "Air", "min": BOX_MIN, "max": BOX_MAX, "spacing": spacing,
              "obstacles": bodies, "fans": fans,
              "porous": [{"name": "mesh_bottom", "min": [MESH_X[0], MESH_Y[0], Z0], "max": [MESH_X[1], MESH_Y[1], Z0 + w],
                          "axis": "z", "resistance": loss},
                         {"name": "mesh_top", "min": [MESH_X[0], MESH_Y[0], Z1 - w], "max": [MESH_X[1], MESH_Y[1], Z1],
                          "axis": "z", "resistance": loss}]}
    procedure = {"type": "fluid", "domain": name, "end_time": end_time, "time_step": 1e-5 * spacing,
                 "frames": 1,       # the app keeps every solved step's frames in memory
                 "collision": "hrr", "turbulence": {"type": "smagorinsky", "constant": 0.1}}
    for command in ("model.step.delete", "model.fluid_domain.delete"):
        try:
            fc.execute(command, {"name": name})
        except SystemExit:
            pass
    fc.batch([("model.fluid_domain.create", domain), ("model.step.create", {"name": name, "procedure": procedure})], "set-up")
    limits = {"max_cells": 40000000, "max_cell_updates": 1e13}
    est = fc.execute("solve.fluid", dict(limits, step=name, backend="gpu", estimate=True))
    mem = est.get("memory", est)
    print(name, "estimate: %.1f GB, problem: %s" % (mem.get("total_bytes", 0) / 1e9, mem.get("problem")))
    if mem.get("problem"):
        raise SystemExit("not solving: " + str(mem["problem"]))
    if "--estimate" in sys.argv:
        return
    r = fc.execute("solve.fluid", dict(limits, step=name, backend="gpu", threads=os.cpu_count()))
    json.dump(r, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    res = {"case": case, "spacing_mm": spacing, "end_time_s": end_time, "cells": r.get("cells"), "steps": r.get("steps"),
           "backend": r.get("backend"), "peak_speed_m_s": round(r["final_max_speed"] / 1000, 2), "zones": {}}
    for z in r.get("zones", []):
        q = z["flow"]
        dp = z.get("pressure_rise") or z.get("pressure_drop") or {}
        res["zones"][z["name"]] = {"flow_m3_h": round(q["mean"] / M3H, 1), "flow_final_m3_h": round(q["final"] / M3H, 1),
                                   "pressure_pa": round(dp.get("mean", 0) / PA, 2)}
    print(json.dumps(res, indent=1))
    path = os.path.join(OUT, "summary.json")
    summary = json.load(open(path)) if os.path.exists(path) else {}
    summary[name] = res
    json.dump(summary, open(path, "w"), indent=1)
    pictures(fc, name)


def pictures(fc, name):
    side = {"yaw": 0, "pitch": 0, "target": [88, 100, 140], "distance": 620}
    end = {"yaw": 90, "pitch": 0, "target": [88, 102, 140], "distance": 620}
    fc.execute("results.streamlines", {"step": name, "show": False})
    for field, axis, pos, camera, tag in (
            ("velocity", "y", 10, side, "cpu-plenum"), ("velocity", "y", 60, side, "heatsink"),
            ("velocity", "y", 194, side, "psu-plenum"), ("velocity", "x", 88, end, "middle"),
            ("pressure", "x", 88, end, "middle")):
        fc.execute("view.hide", {"items": [{"kind": "body", "name": n} for n in (
            ("A_side_cpu", "A_side_psu") if axis == "y" else ("A_front", "A_rear"))]})
        fc.execute("results.slice", {"step": name, "field": field, "axis": axis, "position": pos})
        fc.call("screenshot", {"source": "model", "width": 1100, "height": 1300, "camera": camera,
                               "path": os.path.join(OUT, "%s_%s_%s.png" % (name, field, tag))})


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["geometry"] and len(a) == 2:
        geometry(float(a[1]))
    elif a[:1] == ["run"] and len(a) >= 3 and a[2] in CASES:
        run(float(a[1]), a[2], float(a[3]) if len(a) > 3 and not a[3].startswith("-") else 0.6)
    else:
        raise SystemExit(__doc__)
