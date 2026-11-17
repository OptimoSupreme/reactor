"""Render the pictures in docs/images from the assembly that mk1.py has just built.

  python3 mechanical/renders.py [name ...]

Run it straight after mk1.py, while its assembly is the design shown in SolidCraft; SOLIDCRAFT_MCP as
for mk1.py. With names, only those pictures.
"""
import math
import os
import sys

import mk1
from mk1 import FEET, HANDLE_X, IMAGES, LX, LY, LZ, PSU_TOP, SHELL_SCREW, SWITCH, TIE_X

MID = [LX / 2, LY / 2, LZ / 2]
UP, DOWN = math.pi / 2 - 1e-4, -(math.pi / 2 - 1e-4)
# name: target, yaw, pitch, distance, and the bodies hidden (prefixes) or the only ones shown ("only", ...).
# Yaw 0 looks from the open side toward the tray, 1.57 from the rear toward the front; pitch looks down.
VIEWS = {
    "mk1-front": (MID, -0.75, 0.33, 760, ()),
    "mk1-rear": (MID, 2.45, 0.33, 760, ()),
    "mk1-top": ([LX / 2, LY / 2, LZ], -0.75, 0.8, 560, ()),
    "mk1-top-plan": ([LX / 2, LY / 2, LZ], math.pi / 2, UP, 570, ()),
    "mk1-top-detail": ([30, 40, LZ + 10], 0.95, 0.5, 230, ()),
    "mk1-rear-corner": ([6, 4, LZ + 6], 1.0, 0.55, 120, ()),
    "mk1-handle": ([HANDLE_X[1], LY / 2, LZ + 16], -1.1, 0.4, 260, ()),
    "mk1-under": ([LX / 2, LY / 2, 0], -0.75, -0.7, 620, ()),
    "mk1-under-plan": ([LX / 2, LY / 2, 0], math.pi / 2, DOWN, 570, ()),
    "mk1-under-corner": ([FEET[0][0] + 10, FEET[0][1], -6], 0.75, -0.8, 190, ()),
    "mk1-foot": ([FEET[0][0] + 8, FEET[0][1] + 5, -8], 0.75, -0.95, 120, ()),
    "mk1-shell-screw": ([SHELL_SCREW[0] + 10, -3, SHELL_SCREW[1]], 0.55, 0.15, 170, ()),
    "mk1-shell-screw-inside": ([SHELL_SCREW[0], 0, SHELL_SCREW[1]], math.pi + 0.5, 0.2, 90,
                               ("only", "core", "shell", "screw-shell", "nut-shell")),
    "mk1-switch-front": ([LX, SWITCH[0] + 10, SWITCH[1] - 8], -1.05, 0.25, 170, ()),
    "mk1-switch-inside": ([LX - 12, SWITCH[0], SWITCH[1] - 4], 0.55, -0.2, 150, ("shell", "screw-shell")),
    "mk1-board-open": (MID, 0.4, 0.3, 720, ("shell", "screw-shell")),
    "mk1-board-rear": (MID, 1.15, 0.3, 720, ("shell", "screw-shell")),
    "mk1-open-board-side": (MID, 0.08, 0.12, 700, ("shell", "screw-shell")),
    "mk1-open-front": (MID, -0.7, 0.3, 720, ("shell", "screw-shell")),
    "mk1-tray-side": (MID, math.pi - 0.25, 0.2, 720, ("shell", "screw-shell")),
    "mk1-psu-mount": ([LX - 35, 40, PSU_TOP + 15], -0.95, 0.45, 300, ("shell", "screw-shell")),
    "mk1-tie-slots": ([TIE_X, LY, LZ / 2], math.pi - 0.3, 0.1, 330, ("shell", "screw-shell")),
    "mk1-shelf-alone": ([LX - 40, LY / 2, PSU_TOP + 15], 0.9, 0.5, 300, ("only", "shelf", "nut-shelf")),
    "mk1-shelf-tongues": ([LX, LY / 2, PSU_TOP], -1.25, 0.25, 260, ("only", "shelf", "bulkhead", "core")),
    "mk1-shelf-top": ([LX - 40, LY / 2, PSU_TOP], 0.9, 1.0, 330,
                      ("only", "shelf", "ref-psu", "screw-psu", "nut-shelf", "bulkhead")),
}


def main():
    sc = mk1.Bridge()
    for _ in range(8):   # the assembly's tab, whichever is shown
        if sc.call("inspect_design").get("name") == os.path.splitext(os.path.basename(mk1.ASSEMBLY))[0]:
            break
        sc.call("execute", {"command": "view.next_tab", "params": {}})
    else:
        raise SystemExit("the assembly is not open: run mk1.py first")
    names = [b["name"] for b in sc.call("measure", {"summary": True})["bodies"]]
    show = lambda items, on: sc.call("execute", {"command": "browser.visibility", "params": {"visible": on, "items": items}})
    show(names, True)
    for name in sys.argv[1:] or VIEWS:
        target, yaw, pitch, distance, rule = VIEWS[name]
        if rule and rule[0] == "only":
            hide = [n for n in names if not n.startswith(rule[1:])]
        else:
            hide = [n for n in names if rule and n.startswith(rule)]
        if hide:
            show(hide, False)
        sc.call("screenshot", {"source": "model", "path": os.path.join(IMAGES, name + ".png"), "width": 1400,
                               "height": 1000, "grid": False, "axes": False,
                               "camera": {"target": target, "yaw": yaw, "pitch": pitch, "distance": distance, "fov": 0.6}})
        if hide:
            show(hide, True)
        print("rendered", name)


if __name__ == "__main__":
    main()
