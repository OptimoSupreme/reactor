"""List the smallest gaps in the assembly that reactor.py has just built.

  python3 mechanical/clearances.py [limit]

Run it while the assembly is open in SolidCraft; SOLIDCRAFT_MCP as for reactor.py. Every pair of bodies
closer than the limit (1.0 by default) is measured, the wires and the mains lead apart, and the closest
pair of each kind is printed: contacts first, then gaps, smallest first.
"""
import os
import re
import sys

import reactor


def main():
    limit = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    sc = reactor.Bridge()
    for _ in range(8):   # the assembly's tab, whichever is shown
        if sc.call("inspect_design").get("name") == os.path.splitext(os.path.basename(reactor.LOW_DETAIL))[0]:
            break
        sc.call("execute", {"command": "view.next_tab", "params": {}})
    else:
        raise SystemExit("the assembly is not open: run reactor.py first")
    names = [b["name"] for b in sc.call("measure", {"summary": True})["bodies"]]
    bodies = [n for n in names if not n.startswith(("wire-", "ref-mains-lead"))]
    r = sc.call("execute", {"command": "inspect.clearance", "params": {"bodies": bodies, "clearance": limit}})
    kind = lambda n: re.sub(r"-\d+$", "", n)
    closest = {}
    for p in r["near"]:
        k = tuple(sorted((kind(p["a"]), kind(p["b"]))))
        if k not in closest or p["distance_mm"] < closest[k]["distance_mm"]:
            closest[k] = p
    touching = sorted(k for k, p in closest.items() if p["distance_mm"] < 0.02)
    print("%d bodies, %d pairs measured, %d overlaps, %d not measured" % (
        len(bodies), r["pairs_checked"], len(r["overlaps"]), len(r["unchecked"])))
    print("in contact: " + "; ".join("%s / %s" % k for k in touching))
    for k, p in sorted(closest.items(), key=lambda kv: kv[1]["distance_mm"]):
        if p["distance_mm"] >= 0.02:
            print("  %.2f  %s / %s  at %s" % (p["distance_mm"], p["a"], p["b"], [round(v, 1) for v in p["from"]]))


if __name__ == "__main__":
    main()
