"""python tools/test_siderroot.py

siderroot.py can put a world on that is not in sider.ini yet.

Its docstring says it "comments out every _FL26 root and uncomments (or inserts, above the
first root) the one named". The insert half did not work: the loop comments every _FL26 root
out on its way past, and the anchor was looked for after the loop, so by then no cpk.root line
was left uncommented and next() raised StopIteration. So switching between worlds worked and
adding one did not -- and adding one is the last step of installing a world whose name the ini
has never seen, which is why the failure landed on a fresh _FL26 name at the end of an install
that had worked right up to that line.

The three checks are the three ways this is called: a root that is already listed, one that is
not, and a name that is a prefix of another one.
"""

import os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import siderroot

N = 0

INI = """[sider]
lua.enabled = 1
luajit.ext.enabled = 1
cpk.root = ".\\livecpk\\_FL26Paises"
#cpk.root = ".\\livecpk\\_FL26World"
#cpk.root = ".\\livecpk\\root"
lua.module = "fl26caps.lua"
"""


def ok(name, cond):
    global N
    assert cond, name
    N += 1
    print("ok %d - %s" % (N, name))


def active(ini):
    """the _FL26 root lines that are not commented out"""
    return [
        l.strip()
        for l in ini.splitlines()
        if l.strip().startswith("cpk.root") and "_FL26" in l
    ]


def live_root(ini, name):
    """the uncommented cpk.root line for that root name, or None.

    Matched line by line, not with `in` over the whole text: the commented form
    `#cpk.root = ".\\livecpk\\root"` contains the uncommented one as a substring, so a plain
    `in` reports a root as live when it is switched off. The name is taken off the line the
    same way siderroot's own rootname() does it, which lives inside main() and is not
    importable.
    """
    for l in ini.splitlines():
        s = l.lstrip("#").strip()
        if not (s.startswith("cpk.root") and l == s):
            continue
        v = s.split("=", 1)[1].strip().strip('"').strip("'") if "=" in s else ""
        if v.replace("/", "\\").rstrip("\\").rsplit("\\", 1)[-1] == name:
            return s
    return None


def run(tmp, want, text=INI):
    """run main() against a throwaway ini and return what it wrote"""
    ini = os.path.join(tmp, "sider.ini")
    open(ini, "w", encoding="utf-8").write(text)
    saved, siderroot.INI = siderroot.INI, ini
    sys.argv = ["siderroot.py", want]
    try:
        siderroot.main()
    finally:
        siderroot.INI = saved
    return open(ini, encoding="utf-8").read()


def main():
    tmp = tempfile.mkdtemp()
    try:
        # a root already listed: the line is uncommented and the others go off
        got = run(tmp, "_FL26Paises")
        ok(
            "listed root: it is the active one",
            active(got) == ['cpk.root = ".\\livecpk\\_FL26Paises"'],
        )

        # the case that raised StopIteration: a name the ini has never seen
        got = run(tmp, "_FL26Paises39")
        ok(
            "new root: it is the active one",
            active(got) == ['cpk.root = ".\\livecpk\\_FL26Paises39"'],
        )
        ok(
            "new root: both other _FL26 roots went off",
            '#cpk.root = ".\\livecpk\\_FL26Paises"' in got
            and '#cpk.root = ".\\livecpk\\_FL26World"' in got,
        )
        ok(
            "new root: a root of the game, without _FL26, was left alone",
            live_root(got, "root") is None,
        )

        # the line went in above the old one, not at the end of the file
        ok(
            "new root: it sits above the one it replaced",
            got.index("_FL26Paises39") < got.index('_FL26Paises"'),
        )

        # switching again, to a name added a moment ago, still works
        got = run(tmp, "_FL26World", text=got)
        ok(
            "switching between two roots: only the new one is on",
            active(got) == ['cpk.root = ".\\livecpk\\_FL26World"'],
        )

        # a name that is a prefix of another one must not activate the longer one
        got = run(tmp, "_FL26Reg3", text='cpk.root = ".\\livecpk\\_FL26Reg39"\n')
        ok(
            "a prefix of a listed root does not activate it",
            active(got) == ['cpk.root = ".\\livecpk\\_FL26Reg3"'],
        )

        # an ini with no _FL26 root at all: refused in words, not with a traceback
        try:
            run(tmp, "_FL26World", text="[sider]\nlua.enabled = 1\n")
        except SystemExit as e:
            ok("no _FL26 root to anchor on: it says so", "no _FL26 cpk.root" in str(e))
        else:
            ok("no _FL26 root to anchor on: it says so", False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("1..%d" % N)


if __name__ == "__main__":
    main()
