"""python siderroot.py <_FL26Root>   -> make that the one active _FL26* cpk.root in sider.ini

Every test world is a livecpk root, and only one of them may be live at a time or the
pesdb tables layer in an order nobody asked for.  This comments out every _FL26 root and
uncomments (or inserts, above the first root) the one named, then prints what is active.
"""

import os, sys

INI = os.path.join(
    os.environ.get("FL26_DIR", r"C:\Football Life 2026"), "SiderAddons", "sider.ini"
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    want = sys.argv[1]
    lines = open(INI, encoding="utf-8", errors="replace").read().splitlines()

    # Match the root's own name, not a substring of the line.  Asking for _FL26Reg3 while
    # _FL26Reg39 is also listed used to activate _FL26Reg39 and say so in a line that reads
    # almost the same, which is a whole boot spent measuring the wrong world.
    def rootname(line):
        v = line.split("=", 1)[1].strip().strip('"').strip("'") if "=" in line else ""
        return v.replace("/", "\\").rstrip("\\").rsplit("\\", 1)[-1]

    out, found, first = [], False, None
    for i, l in enumerate(lines):
        s = l.lstrip("#").strip()
        if s.startswith("cpk.root") and "_FL26" in s:
            # Where the first root sits has to be noted here, while this line is still live.
            # Asking for it after the loop found nothing, because the loop above has just
            # commented out every root there was -- so a root that was not already listed could
            # never be added, and the docstring above promises that it is inserted. That is the
            # last step of installing a world nobody has built before, so it is the step that
            # failed: StopIteration, on a fresh _FL26 name, in an install that had gone fine up
            # to that line. Index i of `lines` is the same index of `out`, because out is built
            # by appending every line of lines in order and nothing is inserted before this.
            if first is None:
                first = i
            if rootname(s) == want:
                if found:
                    raise SystemExit("sider.ini lists %s more than once" % want)
                l, found = s, True
            else:
                l = "#" + s
        out.append(l)
    if not found:
        if first is None:
            raise SystemExit("sider.ini lists no _FL26 cpk.root to put a new one above")
        out.insert(first, r'cpk.root = ".\livecpk\%s"' % want)
    open(INI, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(
        "active:", [l for l in out if l.strip().startswith("cpk.root") and "_FL26" in l]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
