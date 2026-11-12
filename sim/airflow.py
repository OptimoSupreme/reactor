"""Airflow through the Mk I, driven by the fans' own curves.

Two steps, each talking to a running desktop app over its MCP bridge:

  python3 sim/airflow.py geometry SPACING             SolidCraft: build the airflow geometry
  python3 sim/airflow.py run SPACING CASE [END_TIME]  FieldCraft: solve one case
  python3 sim/airflow.py run SPACING CASE --estimate  the same set-up, memory estimate only
  python3 sim/airflow.py heat SPACING CASE [END_TIME] the same with the parts' heat in the air

SPACING is the grid in mm (1 for results, 2 only to check a set-up is stable).
CASE is one of CASES below. SOLIDCRAFT_MCP and FIELDCRAFT_MCP hold the command
lines that start each bridge. Output goes to sim/out/.

The case stands on its feet on the floor of a closed box of air, so what
leaves the top comes back down the outside and in underneath. Each fan is a
zone carrying its pressure-flow curve, and the solver finds where the curves
meet the case's resistance. Open inlets and outlets would not stay stable in
the nova-reactor study, which this set-up follows.

Simplified against mechanical/mk1.py:
- sheet is two cells thick so the grid cannot leak through it, with the tray
  merged into the side wall behind it and the bulkhead into the front;
- the hex mesh is a pressure loss over each panel's meshed area;
- the PSU is an empty box with its fan in the face toward the board, a loss
  standing in for its insides, and the shelf's opening above it. Its fan and
  that loss are assumptions, not data for any real unit;
- the heatsink is a base with coarse horizontal fins;
- no cables.

A heat run puts the APU's power on the heatsink, the rest of the board's on the board and the
supply's losses on plates inside it, and takes the same total out through a cooler hung from the
box's ceiling, so the air that comes back in underneath is at room temperature. Solids are given
almost no heat capacity so that they settle within the second or so the flow is run for; the steady
state does not depend on it. The air temperatures are the result. The heatsink's own temperature is
not: its fins are far coarser than the real ones, so the chip's temperature is worked out from the
air reaching the heatsink and the real cooler's measured resistance, in docs/thermal.md.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mechanical"))
import mk1 as M  # noqa: E402

OUT = os.path.join(M.REPO, "sim", "out")

# mm-t-s units: density in t/mm3, viscosity in MPa s, pressure in MPa
PA = 1e-6
M3H = 1e9 / 3600     # mm3/s
AIR_DENSITY, AIR_VISCOSITY = 1.16e-12, 1.85e-11
AIR_CONDUCTIVITY, AIR_SPECIFIC_HEAT, AIR_EXPANSION = 0.026, 1.005e9, 3.35e-3
AMBIENT = 25.0
GRAVITY = [0, 0, -9810.0]
# solids in a heat run: density, conductivity, and a specific heat a thousandth of the real one
SOLIDS = {"Aluminium": (2.7e-9, 200, 9e5), "Board": (1.9e-9, 5, 1.2e6)}

# Shut-off pressure (mm H2O) and free flow (m3/h) at full speed. Noctua publishes no curve between
# the two for the NF-A12x15 (1850 rpm), so a straight line is assumed.
NF_A12X15 = (1.53, 94.2)
PSU_FAN = (2.0, 60.0)        # assumed: a 92 mm fan of the kind SFX units carry
PSU_FAN_SIZE = 88.0          # opening in the PSU's face
PSU_LOSS = 8.0               # assumed loss coefficient for the PSU's insides

# Thin perforated plate at about 70 % open, Idelchik.
MESH_LOSS = 1.2

# Fan speeds as a fraction of full: bottom pair, top, CPU, PSU. None leaves the fan out (its frame stays).
CASES = {
    "all-100": (1.0, 1.0, 1.0, 1.0),
    "all-50": (0.5, 0.5, 0.5, 0.5),
    "no-case-fans": (None, None, 1.0, 1.0),
    "bottom-only": (1.0, None, 1.0, 1.0),
    # The board as it is, flat out, with the fans turned down and the supply's fan stopped, as a Corsair
    # SF750's is below 300 W.
    "load": (0.5, 0.5, 0.6, None),
    # a hotter chip on a later board, every fan at full speed, the supply's still stopped
    "future": (1.0, 1.0, 1.0, None),
}
# Heat in W: heatsink, rest of the board, supply. 140 is the Framework board's boost limit and 180 a
# guess at a top Medusa Halo part; the supply's loss is about 8 % of what it delivers.
HEAT = {"load": (140, 15, 15), "future": (180, 20, 22)}

X0, X1 = -M.T, M.SHELL_XF
Y0, Y1 = M.SHELL_Y0, M.SHELL_Y1
Z0, Z1 = M.SHELL_Z0, M.SHELL_Z1
FLOOR = -20.0
BOX_MIN, BOX_MAX = [-32, -34, FLOOR], [288, 166, 272]
MESH_X, MESH_Y = (6, M.LX - 6), (6, M.LY - 6)
HX, HZ = M.BOARD_X + 18.54, M.BOARD_Z + M.BOARD - 136.06
HY = M.BOARD_Y - M.HEATSINK
CX, CZ = HX + 63.1, HZ + 63.1
PSU_Z = M.PSU_TOP - M.PSU[2]
PSU_C = (M.PSU_Y + M.PSU[1] / 2, PSU_Z + M.PSU[2] / 2)   # centre of its fan, Y and Z
PSU_FAN_T = 15.0


def geometry_path(spacing):
    return os.path.join(OUT, "airflow-mk1-%gmm.solidcraft" % spacing)


def frame(name, axis, c1, c2, half, w, a, b):
    """Four walls round a fan, which blows along `axis` from a to b."""
    out = []
    for k, (p0, p1, q0, q1) in enumerate(((c1 - half, c1 + half, c2 - half, c2 - half + w),
                                          (c1 - half, c1 + half, c2 + half - w, c2 + half),
                                          (c1 - half, c1 - half + w, c2 - half + w, c2 + half - w),
                                          (c1 + half - w, c1 + half, c2 - half + w, c2 + half - w))):
        n = "%s_%d" % (name, k)
        if axis == "z":
            out.append((n, p0, p1, q0, q1, a, b))
        elif axis == "y":
            out.append((n, p0, p1, a, b, q0, q1))
        else:
            out.append((n, a, b, p0, p1, q0, q1))
    return out


def ring(name, x0, x1, y0, y1, hx0, hx1, hy0, hy1, za, zb):
    """A horizontal plate with a rectangular hole in it."""
    return [(name + "_a", x0, x1, y0, hy0, za, zb), (name + "_b", x0, x1, hy1, y1, za, zb),
            (name + "_c", x0, hx0, hy0, hy1, za, zb), (name + "_d", hx1, x1, hy0, hy1, za, zb)]


def solids(w):
    """(name, x0, x1, y0, y1, z0, z1) for every obstacle, with sheet w thick."""
    b = [("A_side_open", X0, X1, Y0, Y0 + w, Z0, Z1),
         ("A_side_tray", X0, X1, min(M.TRAY_Y, Y1 - w), Y1, Z0, Z1),
         ("A_front", min(M.BULKHEAD_X[0], X1 - w), X1, Y0, Y1, Z0, Z1),
         ("A_rear", X0, X0 + w, Y0, Y1, Z0, Z1)]
    b += ring("A_bottom", X0, X1, Y0, Y1, MESH_X[0], MESH_X[1], MESH_Y[0], MESH_Y[1], Z0, Z0 + w)
    b += ring("A_top", X0, X1, Y0, Y1, MESH_X[0], MESH_X[1], MESH_Y[0], MESH_Y[1], Z1 - w, Z1)
    for i, (fx, fy) in enumerate(M.BOTTOM_FANS):
        b += frame("A_fanb%d" % i, "z", fx, fy, 60, w, Z0 + w, M.FAN_T)
    b += frame("A_fant", "z", M.TOP_FAN[0], M.TOP_FAN[1], 60, w, M.LZ - M.FAN_T, Z1 - w)
    b += frame("A_fanc", "y", CX, CZ, 60, w, HY - M.CPU_FAN, HY)
    # board, ports, mains inlet, heatsink
    bz = M.BOARD_Z
    b.append(("A_board", M.BOARD_X, M.BOARD_X + M.BOARD, M.BOARD_Y, M.BOARD_Y + w, bz, bz + M.BOARD))
    b.append(("A_ports", 0, 20, M.BOARD_Y - 31.5, M.BOARD_Y, bz + 11.5, bz + 143.9))
    b.append(("A_inlet", 0, 24, M.INLET[0] - 14, M.INLET[0] + 14, M.INLET[1] - 10, M.INLET[1] + 10))
    # a name given more than once is one body: the heatsink, the supply's insides and the cooler
    b.append(("A_hs", HX, HX + 126.2, M.BOARD_Y - 6, M.BOARD_Y, HZ, HZ + 126.2))
    z = HZ
    while z + w <= HZ + 126.2:
        b.append(("A_hs", HX, HX + 126.2, HY, M.BOARD_Y - 6, z, z + w))
        z += 3 * w
    # PSU: a box open at the top, its fan in the face toward the board
    px0, px1 = M.PSU_X, M.PSU_X + M.PSU[0]
    py0, py1 = M.PSU_Y, M.PSU_Y + M.PSU[1]
    b.append(("A_psu_floor", px0, px1, py0, py1, PSU_Z, PSU_Z + w))
    b.append(("A_psu_front", px1 - w, px1, py0, py1, PSU_Z + w, M.PSU_TOP))
    h = PSU_FAN_SIZE / 2
    cy, cz = PSU_C
    b += [("A_psu_face_a", px0, px0 + w, py0, py1, PSU_Z + w, cz - h), ("A_psu_face_b", px0, px0 + w, py0, py1, cz + h, M.PSU_TOP),
          ("A_psu_face_c", px0, px0 + w, py0, cy - h, cz - h, cz + h), ("A_psu_face_d", px0, px0 + w, cy + h, py1, cz - h, cz + h)]
    # what gets hot inside the supply: a bar across it carrying plates that stand in the air's way up
    b.append(("A_psu_core", px0 + 24, px0 + 24 + w, py0 + 14, py1 - 14, PSU_Z + 30, PSU_Z + 30 + w))
    y = py0 + 14
    while y + w <= py1 - 14:
        b.append(("A_psu_core", px0 + 24, px1 - 3 * w, y, y + w, PSU_Z + 30, M.PSU_TOP - 16))
        y += 5 * w
    # cooler for heat runs: a slab under the box's ceiling with plates hanging from it
    b.append(("A_cooler", BOX_MIN[0] + 4, BOX_MAX[0] - 4, BOX_MIN[1] + 4, BOX_MAX[1] - 4, BOX_MAX[2] - 4, BOX_MAX[2]))
    y = BOX_MIN[1] + 6
    while y + w <= BOX_MAX[1] - 4:
        b.append(("A_cooler", BOX_MIN[0] + 4, BOX_MAX[0] - 4, y, y + w, Z1 + 26, BOX_MAX[2] - 4))
        y += 4 * w
    # shelf: its web with the opening over the PSU, and its rear wall, which stops short of the top panel
    sx0, sx1 = M.SHELF_X
    b += ring("A_shelf", sx0, sx1, Y0 + w, M.TRAY_Y, px0 + 8, px0 + 55.5, py0 + 12, py0 + 113, M.PSU_TOP, M.PSU_TOP + w)
    b.append(("A_shelf_wall", sx0, sx0 + w, Y0 + w, M.TRAY_Y, M.PSU_TOP + w, M.LZ - 0.1 - 2 * M.T))
    for i, (x, y) in enumerate(M.FEET):
        b.append(("A_foot%d" % i, x - 9, x + 9, y - 9, y + 9, FLOOR, Z0))
    return b


def geometry(spacing):
    os.makedirs(OUT, exist_ok=True)
    sc = M.Bridge()
    sc.call("new_design")
    steps, seen = [], set()
    for n, x0, x1, y0, y1, z0, z1 in solids(2 * spacing):
        p = {"length": x1 - x0, "width": y1 - y0, "height": z1 - z0, "corner": [x0, y0, z0]}
        p.update({"operation": "join", "targets": [n]} if n in seen else {"operation": "new", "body_name": n})
        seen.add(n)
        steps.append(("solid.box", p))
    sc.batch(steps, "airflow geometry")
    sc.call("save", {"path": geometry_path(spacing)})
    sc.call("new_design")
    sc.call("open", {"path": M.DESIGN})  # leave the app on the real design
    print("wrote", geometry_path(spacing), len(seen), "bodies")


class Field(M.Bridge):
    ENV = "FIELDCRAFT_MCP"

    def execute(self, command, params=None):
        r = self.call("execute", {"command": command, "params": params or {}})
        return r.get("result", r) if isinstance(r, dict) else r


def curve(fan, s):
    return [[0, fan[0] * 9.80665 * PA * s * s], [fan[1] * M3H * s, 0]]


def fans(case, w):
    sb, st, sc_, sp = CASES[case]
    out = []
    if sb:
        for i, (fx, fy) in enumerate(M.BOTTOM_FANS):
            out.append({"name": "bottom%d" % (i + 1), "min": [fx - 60 + w, fy - 60 + w, Z0 + w],
                        "max": [fx + 60 - w, fy + 60 - w, M.FAN_T], "direction": "+z", "curve": curve(NF_A12X15, sb)})
    if st:
        fx, fy = M.TOP_FAN
        out.append({"name": "top", "min": [fx - 60 + w, fy - 60 + w, M.LZ - M.FAN_T],
                    "max": [fx + 60 - w, fy + 60 - w, Z1 - w], "direction": "+z", "curve": curve(NF_A12X15, st)})
    if sc_:
        out.append({"name": "cpu", "min": [CX - 60 + w, HY - M.CPU_FAN, CZ - 60 + w],
                    "max": [CX + 60 - w, HY, CZ + 60 - w], "direction": "+y", "curve": curve(NF_A12X15, sc_)})
    if sp:
        h = PSU_FAN_SIZE / 2
        cy, cz = PSU_C
        out.append({"name": "psu", "min": [M.PSU_X, cy - h, cz - h], "max": [M.PSU_X + PSU_FAN_T, cy + h, cz + h],
                    "direction": "+x", "curve": curve(PSU_FAN, sp)})
    return out


# where the air's temperature is read in a heat run
PROBES = {
    "under bottom fan 1": [M.BOTTOM_FANS[0][0], M.BOTTOM_FANS[0][1], Z0 - 8],
    "under bottom fan 2": [M.BOTTOM_FANS[1][0], M.BOTTOM_FANS[1][1], Z0 - 8],
    "into the CPU fan": [CX, HY - M.CPU_FAN - 10, CZ],
    "into the supply": [M.PSU_X - 6, PSU_C[0], PSU_C[1]],
    "by the board's top edge": [100, M.BOARD_Y - 12, M.BOARD_Z + M.BOARD - 8],
    "by the board's front edge": [M.BOARD_X + M.BOARD - 12, M.BOARD_Y - 12, 100],
    "out of the top fan": [M.TOP_FAN[0], M.TOP_FAN[1], Z1 + 8],
    "out above the supply": [M.PSU_X + 32, 64, Z1 + 8],
}


def run(spacing, case, end_time, heat=False):
    w = 2 * spacing
    fc = Field()
    fc.call("open", {"path": geometry_path(spacing)})
    bodies = [b["name"] for b in fc.call("inspect_model")["bodies"]]
    if not heat:
        bodies.remove("A_cooler")
    # The lattice cannot carry heat that diffuses as slowly as it does in still air at a time step the
    # flow is stable at, so a heat run raises the air's conductivity to the least the grid resolves:
    # about four times the real figure on the 1 mm grid, which is less than turbulence adds anyway.
    dt = (2e-5 if heat else 1e-5) * spacing
    k = max(AIR_CONDUCTIVITY, 1.05 * 0.005 * spacing ** 2 / (3 * dt) * AIR_DENSITY * AIR_SPECIFIC_HEAT) if heat else AIR_CONDUCTIVITY
    air = {"name": "Air_%d" % round(k * 1000), "density": AIR_DENSITY, "fluid": {"type": "newtonian", "viscosity": AIR_VISCOSITY},
           "thermal": {"conductivity": k, "specific_heat": AIR_SPECIFIC_HEAT}}
    for material in [air] + [{"name": n, "density": rho, "thermal": {"conductivity": k, "specific_heat": cp}}
                             for n, (rho, k, cp) in SOLIDS.items()]:
        try:
            fc.execute("model.material.create", material)
        except SystemExit as e:
            if "already exists" not in str(e):
                raise
    mesh = {"type": "loss_coefficient", "coefficient": MESH_LOSS}
    px0 = M.PSU_X + PSU_FAN_T + spacing
    name = "%s%s_%gmm" % (case, "_heat" if heat else "", spacing)
    domain = {"name": name, "material": air["name"], "min": BOX_MIN, "max": BOX_MAX, "spacing": spacing,
              "obstacles": bodies, "fans": fans(case, w),
              "porous": [{"name": "mesh_bottom", "min": [MESH_X[0], MESH_Y[0], Z0], "max": [MESH_X[1], MESH_Y[1], Z0 + w],
                          "axis": "z", "resistance": mesh},
                         {"name": "mesh_top", "min": [MESH_X[0], MESH_Y[0], Z1 - w], "max": [MESH_X[1], MESH_Y[1], Z1],
                          "axis": "z", "resistance": mesh},
                         {"name": "psu_insides", "min": [px0, M.PSU_Y, PSU_Z + w + 20],
                          "max": [M.PSU_X + M.PSU[0] - w, M.PSU_Y + M.PSU[1], M.PSU_TOP - 20],
                          "axis": "z", "resistance": {"type": "loss_coefficient", "coefficient": PSU_LOSS}}]}
    procedure = {"type": "fluid", "domain": name, "end_time": end_time, "time_step": dt,
                 "frames": 1,       # the app keeps every solved step's frames in memory
                 "collision": "hrr", "turbulence": {"type": "smagorinsky", "constant": 0.1}}
    if heat:
        apu, board, psu = HEAT[case]
        domain["thermal"] = {"initial_temperature": AMBIENT, "gravity": GRAVITY, "expansion": AIR_EXPANSION, "solids": [
            {"body": "A_hs", "material": "Aluminium", "power": "%g W" % apu},
            {"body": "A_board", "material": "Board", "power": "%g W" % board},
            {"body": "A_psu_core", "material": "Aluminium", "power": "%g W" % psu},
            {"body": "A_cooler", "material": "Aluminium", "power": "%g W" % -(apu + board + psu)}]}
        procedure["steady"] = {"tolerance": 1e-3, "min_time": 0.6, "monitors": [{"type": "mean_temperature"}]}
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
    res = {"case": case, "spacing_mm": spacing, "air_conductivity_w_mk": round(k, 3), "end_time_s": r.get("end_time", end_time), "cells": r.get("cells"), "steps": r.get("steps"),
           "backend": r.get("backend"), "peak_speed_m_s": round(r["final_max_speed"] / 1000, 2), "zones": {}}
    for z in r.get("zones", []):
        q = z["flow"]
        dp = z.get("pressure_rise") or z.get("pressure_drop") or {}
        res["zones"][z["name"]] = {"flow_m3_h": round(q["mean"] / M3H, 1), "flow_final_m3_h": round(q["final"] / M3H, 1),
                                   "pressure_pa": round(dp.get("mean", 0) / PA, 2)}
    if heat:
        pts = fc.call("probe", {"step": name, "points": list(PROBES.values())})["points"]
        res["heat_w"] = dict(zip(("heatsink", "board", "supply"), HEAT[case]))
        res["air_c"] = {k: round(pt["temperature"], 1) for k, pt in zip(PROBES, pts) if pt.get("temperature") is not None}
        res["solids_peak_c"] = {x["body"]: round(x["peak"], 1) for x in r.get("solids", [])}
        hist = [h for h in r.get("stop", {}).get("history", []) if h["time"] > 0]
        if len(hist) > 1:
            res["box_mean_c"] = round(hist[-1]["values"][-1], 2)
            res["box_mean_k_per_s"] = round((hist[-1]["values"][-1] - hist[-2]["values"][-1])
                                            / max(hist[-1]["time"] - hist[-2]["time"], 1e-9), 2)
    print(json.dumps(res, indent=1))
    path = os.path.join(OUT, "summary.json")
    summary = json.load(open(path)) if os.path.exists(path) else {}
    summary[name] = res
    json.dump(summary, open(path, "w"), indent=1)
    pictures(fc, name, heat)


def pictures(fc, name, heat=False):
    side = {"yaw": 0, "pitch": 0, "target": [128, 64, 110], "distance": 620}
    end = {"yaw": 90, "pitch": 0, "target": [128, 64, 110], "distance": 520}
    fc.execute("results.streamlines", {"step": name, "show": False})
    for field, axis, pos, camera, tag in (
            ("velocity", "y", 24, side, "open-side"), ("velocity", "y", 90, side, "heatsink"),
            ("pressure", "y", 24, side, "open-side"),
            ("velocity", "x", 90, end, "board"), ("velocity", "x", 212, end, "psu")) + ((
            ("temperature", "y", 24, side, "open-side"), ("temperature", "y", 90, side, "heatsink"),
            ("temperature", "x", 212, end, "psu")) if heat else ()):
        fc.execute("view.hide", {"items": [{"kind": "body", "name": n} for n in (
            ("A_side_open", "A_side_tray") if axis == "y" else ("A_front", "A_rear"))]})
        fc.execute("results.slice", {"step": name, "field": field, "axis": axis, "position": pos})
        fc.call("screenshot", {"source": "model", "width": 1300, "height": 1100, "camera": camera,
                               "path": os.path.join(OUT, "%s_%s_%s.png" % (name, field, tag))})


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if a[:1] == ["geometry"] and len(a) == 2:
        geometry(float(a[1]))
    elif a[:1] == ["run"] and len(a) >= 3 and a[2] in CASES:
        run(float(a[1]), a[2], float(a[3]) if len(a) > 3 else 0.6)
    elif a[:1] == ["heat"] and len(a) >= 3 and a[2] in HEAT:
        run(float(a[1]), a[2], float(a[3]) if len(a) > 3 else 1.2, heat=True)
    else:
        raise SystemExit(__doc__)
