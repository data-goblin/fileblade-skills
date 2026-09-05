from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = Path("/usr/include/qt6/QtCore/qnamespace.h")
ENGINES = ("bun", "node", "deno")
RESULTS: list[tuple[str, bool, str]] = []

def check(name: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(condition), detail))

def qt_constants() -> dict[str, int]:
    if not HEADER.is_file():
        raise RuntimeError(f"qt6 headers not found at {HEADER}; install qt6-base")
    text = HEADER.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(r"^\s+(Key_[A-Za-z0-9_]+|[A-Za-z]+Modifier)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,", re.MULTILINE)
    found: dict[str, int] = {}
    for name, raw in pattern.findall(text):
        found.setdefault(name, int(raw, 16) if raw.startswith("0x") else int(raw))
    return found

def engine() -> list[str]:
    for name in ENGINES:
        path = shutil.which(name)
        if path:
            return [path, "run"] if name == "deno" else [path]
    raise RuntimeError("no JavaScript engine found; install bun, node, or deno")

def evaluate(cases: list[tuple[int, int]], qt: dict[str, int]) -> list[str]:
    source = (ROOT / "blades" / "KeyMap.js").read_text(encoding="utf-8")
    stripped = "\n".join(line for line in source.splitlines() if not line.strip().startswith(".pragma"))
    harness = (
        stripped
        + "\nconst qt = " + json.dumps(qt) + ";\n"
        + "const cases = " + json.dumps(cases) + ";\n"
        + "console.log(JSON.stringify(cases.map(c => resolve(c[0], c[1], qt))));\n"
    )
    with tempfile.TemporaryDirectory() as raw:
        script = Path(raw) / "harness.mjs"
        script.write_text(harness, encoding="utf-8")
        completed = subprocess.run(
            engine() + [str(script)], capture_output=True, text=True, check=False, timeout=60
        )
        if completed.returncode != 0:
            raise RuntimeError(f"key map harness failed: {completed.stderr.strip()[:300]}")
        return json.loads(completed.stdout.strip().splitlines()[-1])

def main() -> int:
    qt = qt_constants()
    required = [
        "Key_Tab", "Key_Backtab", "Key_Escape", "Key_Home", "Key_End",
        "Key_PageUp", "Key_PageDown", "Key_BracketLeft", "Key_BracketRight",
        "Key_J", "Key_K", "Key_H", "Key_L", "Key_Up", "Key_Down", "Key_Left", "Key_Right",
        "Key_Return", "Key_Enter", "Key_O", "Key_R", "Key_G", "Key_D", "Key_U", "Key_Z",
        "Key_Slash", "NoModifier", "ShiftModifier", "ControlModifier", "AltModifier", "MetaModifier",
    ]
    missing = [name for name in required if name not in qt]
    check("keymap.qt-constants-parsed", not missing, str(missing))
    if missing:
        return 1

    none, shift = qt["NoModifier"], qt["ShiftModifier"]
    ctrl, alt, meta = qt["ControlModifier"], qt["AltModifier"], qt["MetaModifier"]

    expectations: list[tuple[str, str, int, int, str]] = []

    chords = ["Key_Tab", "Key_Backtab", "Key_PageUp", "Key_PageDown", "Key_BracketLeft", "Key_BracketRight"]
    combos = [ctrl, ctrl | shift, ctrl | alt, ctrl | meta, ctrl | shift | alt | meta]
    for key in chords:
        for index, modifiers in enumerate(combos):
            expectations.append((f"blade-slot-chord.{key}.combo{index}", key, modifiers, 0, ""))

    tree_focus = [("Key_Tab", none), ("Key_Backtab", none), ("Key_Backtab", shift), ("Key_Escape", none)]
    for key, modifiers in tree_focus:
        label = "plain" if modifiers == none else "shift"
        expectations.append((f"tree-focus.{key}.{label}", key, modifiers, 0, ""))

    tree_paging = [("Key_PageDown", none), ("Key_PageUp", none), ("Key_PageDown", shift),
                   ("Key_PageUp", shift), ("Key_D", ctrl), ("Key_U", ctrl)]
    for index, (key, modifiers) in enumerate(tree_paging):
        expectations.append((f"tree-paging.{key}.{index}", key, modifiers, 0, ""))

    tree_jumps = [("Key_G", none), ("Key_G", shift), ("Key_Home", none), ("Key_End", none)]
    for index, (key, modifiers) in enumerate(tree_jumps):
        expectations.append((f"tree-jump.{key}.{index}", key, modifiers, 0, ""))

    for key in ["Key_J", "Key_K", "Key_H", "Key_L", "Key_Up", "Key_Down", "Key_Left",
                "Key_Right", "Key_Return", "Key_Enter", "Key_O", "Key_R", "Key_Slash", "Key_Z"]:
        expectations.append((f"tree-motion.{key}", key, none, 0, ""))
    expectations.append(("tree-motion.Key_Z.shift", "Key_Z", shift, 0, ""))

    expectations.append(("rescan.shift-r", "Key_R", shift, 0, "rescan"))
    for name, modifiers in (("plain", none), ("ctrl-shift", ctrl | shift),
                            ("alt-shift", alt | shift), ("meta-shift", meta | shift),
                            ("ctrl", ctrl), ("alt", alt), ("meta", meta)):
        expectations.append((f"rescan.rejects-{name}", "Key_R", modifiers, 0, ""))

    cases = [(qt[key], modifiers) for _, key, modifiers, _, _ in expectations]
    actual = evaluate(cases, {name: qt[name] for name in required})
    check("keymap.harness-shape", len(actual) == len(expectations))
    for (name, _key, _mods, _unused, expected), got in zip(expectations, actual):
        check(f"keymap.{name}", got == expected, f"expected {expected!r} got {got!r}")

    actions = {row for row in actual}
    check("keymap.only-rescan-is-module-owned", actions <= {"", "rescan"}, str(sorted(actions)))
    check("keymap.rescan-present", "rescan" in actions)

    failures = [row for row in RESULTS if not row[1]]
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"FAIL {name} {detail}")
    print(f"keymap: {len(RESULTS) - len(failures)}/{len(RESULTS)} passed")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
