from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from agent_skills import registry
import fileblade_paths
from fixtures import write_skill

CORE = Path(fileblade_paths.__file__).resolve().parents[1]

RESULTS: list[tuple[str, bool, str]] = []
SOCKET = "data-goblin.fileblade/blade"
KIND_ENTRY = {
    "bar": "bar", "bar-widget": "barWidget", "menu": "menu",
    "overlay": "overlay", "panel": "panel", "service": "service",
}

def check(name: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(condition), detail))

def test_manifest() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    check("manifest.schemaVersion", manifest.get("schemaVersion") == 1)
    check("manifest.id", manifest.get("id") == "data-goblin.fileblade-skills")
    check("manifest.id-pattern", bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", manifest["id"])))
    check("manifest.not-reserved", not manifest["id"].startswith("omarchy."))
    for field in ("name", "version", "author", "description", "license"):
        value = manifest.get(field)
        check(f"manifest.{field}", isinstance(value, str) and value != "")
    check("manifest.description-limit", len(manifest["description"]) <= 500)
    kinds = manifest.get("kinds")
    check("manifest.kinds", isinstance(kinds, list) and len(kinds) > 0)
    check("manifest.kinds-known", set(kinds) <= set(KIND_ENTRY), str(kinds))
    entry_points = manifest.get("entryPoints")
    check("manifest.entryPoints-object", isinstance(entry_points, dict))
    for kind in kinds:
        key = KIND_ENTRY[kind]
        check(f"manifest.entry-for-{kind}", key in entry_points)
    for key, value in entry_points.items():
        check(f"manifest.entry-relative:{key}", not value.startswith("/") and ".." not in value)
        check(f"manifest.entry-exists:{key}", (ROOT / value).is_file())
    contributions = manifest.get("extensions", {}).get(SOCKET)
    check("manifest.socket", isinstance(contributions, list) and len(contributions) == 1)
    module = contributions[0]
    check("manifest.module-hostContract", module.get("hostContract") == 2)
    check("manifest.module-entry", (ROOT / module["entry"]).is_file())
    check("manifest.module-singleton", module.get("singleton") is True)
    check("manifest.module-id", bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", module.get("id", ""))))

def test_license_and_readme() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    check("license.present", "MIT License" in license_text)
    readme = (ROOT / "docs" / "agent-written" / "README.md").read_text(encoding="utf-8")
    check("readme.names-host", "data-goblin.fileblade" in readme)
    check("readme.names-fileblade", "Omarchy Fileblade" in readme)
    check("readme.dependency-required", "required" in readme.lower())
    check("readme.install-order", "Install order" in readme)
    for agent in registry.AGENT_LABELS.values():
        check(f"readme.documents:{agent}", agent in readme)
    for url in set(registry.DOCS.values()):
        check(f"readme.cites:{url}", url in readme)

def test_qml_shape() -> None:
    module = (ROOT / "blades" / "Module.qml").read_text(encoding="utf-8")
    service = (ROOT / "Service.qml").read_text(encoding="utf-8")
    provider = (ROOT / "Provider.qml").read_text(encoding="utf-8")
    inventory = (CORE / "ui/ArtifactInventory.qml").read_text(encoding="utf-8")
    lane = (CORE / "ui/InventoryLane.qml").read_text(encoding="utf-8")
    directories = (CORE / "ui/ArtifactDirectories.qml").read_text(encoding="utf-8")
    native = (CORE / "src/module_helpers.rs").read_text(encoding="utf-8")
    check("qml.context-nullable", "property var context: null" in module)
    check("qml.no-required-context", "required property var context" not in module)
    check("qml.takeFocus", "function takeFocus(" in module)
    check("qml.title", "readonly property string title" in module)
    check("qml.status", "readonly property string status: statusText()" in module
          and "item.status = Qt.binding(function() { return module.status })" in module)
    check("qml.shared-header", 'context.ui.url("PaneHeader")' in module)
    check("qml.shared-tree", 'context.ui.url("ArtifactTree")' in module)
    check("qml.shared-context", "inventory.anchorPath" in module and "inventory.projectArguments" in module
          and "files.contextPath !== undefined" in inventory and "files.contextPath !== undefined || files.projectRoot" in inventory)
    check("qml.shared-bin", 'setSource(module.context.ui.url("ArtifactBin"), { service: module.files })' in module
          and 'item.module = "skills"\n      item.context = Qt.binding(function() { return module.context })' in module)
    check("qml.bin-position", "bin.item.mergeRows(items, binned, function(entry) { return module.groupPath(entry) })" in module
          and "position: Math.max(0, allRows().indexOf(entry))" in module
          and "groups: groupPath(entry)" in module
          and '[scope, parts.marketplace || "No marketplace", parts.plugin]' in module
          and '[scope, "No marketplace", "No plugin"]' in module
          and "item.groupGlyph = function(path) { return module.groupGlyph(path) }" in module
          and "metrics: entry.metrics" in module)
    check("qml.shared-view", 'context.ui.url("PaneView")' in module
          and "readonly property var view: viewLoader.item" in module
          and 'item.defaultMetric = "agents"' in module
          and "item.options = module.metricOptions" in module)
    check("qml.view-bound", module.count("item.view = Qt.binding(function() { return module.view })") == 2)
    check("qml.agents-contract", "item.appliedAgents = function(entry)" in module
          and "item.installedAgents = Qt.binding" in module
          and "item.agentToggled.connect" in module
          and "item.agentsAllRequested.connect" in module
          and "item.filterRequested.connect" in module
          and "header.item.openFilter()" in module
          and "item.specialMetricValue" in module
          and "item.leafDetail = function(entry)" in module)
    check("qml.no-old-metric-contract", "metricKey" not in module and "setMetric" not in module
          and "metricChosen" not in module and "restoreMetric" not in module and "leafBadge" not in module)
    check("qml.metric-options", 'context.metrics.options(["off", "agents", "updated", "created", '
          '{ key: "tokens", label: "Tokens (descriptions)" }, '
          '{ key: "fileTokens", label: "Tokens (SKILL.md)", shortLabel: "TOKENS (SKILL.MD)", kind: "number" }, '
          '"characters", "words", "bytes", "summary"])' in module)
    check("qml.metric-kinds", 'label: "Tokens (estimated)"' not in module and 'kind: "text"' not in module)
    check("qml.apply-argv", '["--json", "--project", anchorPath, "--id", String(entry.id), "--state", on ? "on" : "off"]' in module
          and 'command.push("--agent", String(agentIds[i]))' in module and 'inventory.mutate("apply", command)' in module)
    check("qml.apply-status", '"Applying…"' in module and "module.applyError" in module and "inventory.applying" in module)
    check("qml.apply-all-toggle", "function toggleAllAgents(entry, on)" in module and "applyAgents(entry, installedAgents, on)" in module
          and "module.toggleAllAgents(entry, true)" in module and "item.agentsAllRequested.connect(function(entry, on) { module.toggleAllAgents(entry, on) })" in module)
    check("qml.no-description-toggle", "showDescriptions" not in module
          and 'detailToggleLabel: "DESC"' not in module)
    check("qml.project-group-directory", "item.groupBadge = function(path)" in module
          and "module.projectRoot || module.anchorPath" not in module
          and 'item.groupBadge = function(path) { return "" }' in module)
    check("qml.tab-aware-header", "item.tabIndex = Qt.binding" in module)
    check("qml.destruction", "attachedProvider.detach(attachedContext)" in module
          and "suspendScan(true)" in lane and "stopWatch(true)" in lane and "lane.shutdown()" in inventory)
    check("qml.timeout", ".timeout(declared.timeout)" in native and "100..=30_000" in native)
    check("qml.generation", "request.generation === lane.generation" in lane)
    check("qml.queued-refresh", "refreshQueued" in lane and "startScan" in lane)
    check("qml.two-lanes", 'scope: "project"' in inventory and 'scope: "user"' in inventory
          and "projectLane.invalidate()" in inventory and "userLane.invalidate()" not in inventory)
    check("qml.exit-code", "!output.status.success()" in native)
    check("qml.stderr", ".limits(OUTPUT_LIMIT, 4096)" in native)
    check("qml.shared-runtime", 'context.ui.url("ArtifactInventory")' in service
          and "context.providerService" in module and "Process {" not in module)
    helper = json.loads((ROOT / "manifest.json").read_text())["extensions"]["data-goblin.fileblade/helper"][0]
    check("qml.helper-boundary", helper == {"id": "inventory", "entry": "bin/agent-skillsctl",
          "read": ["list"], "write": ["apply"], "timeoutMs": 8000})
    check("qml.suspension", "readonly property bool suspended" in module)
    check("qml.collapse-aware", "context.collapsed === true" in module)
    check("qml.blade-open-aware", "context.bladeOpen === false" in module)
    check("qml.shift-r", "rescan" in module)
    check("qml.schema-guard", "response.schemaVersion !== 1" in lane)
    check("qml.clamps-items", "maximumItems: 256" in provider and "i < owner.maximumItems" in lane
          and "rows.slice(0, maximumItems)" in inventory)
    check("qml.skill-folder-rows", "function skillDirectoryPath(path)" in module
          and "descriptorPath: descriptorPath" in module
          and "isDir: path !== descriptorPath" in module)
    check("qml.skill-folder-navigation", "function openDescriptor(item)" in module
          and 'files.navigateToLocation(String(item.path), context.screen, "browse")' in module
          and "module.openDescriptor(entry)" in module)
    check("qml.skill-folder-drop-glyph", 'return { glyph: "", actions: actions, includeDefaults: true }' in module)
    check("qml.skill-folder-tree", "item.expandableItems = true" in module and "item.loadFolderChildren = true" in module
          and 'files.backendRequest("children-batch"' in directories)
    check("qml.skill-folder-child-safety", "PathText.fileUrl(PathText.parent(raw.path)) !== PathText.fileUrl(parentPath)" in directories
          and "files.makeRow(raw, 0)" in directories and "result.entries.slice(0, directories.entryLimit)" in directories
          and "skillRoot: true" in module and "skillRoot: true" not in directories)
    check("qml.argv-array", 'var args = ["--project", owner.anchorPath, "--json", "--scope", scope].concat(owner.projectArguments, owner.scanArguments)' in lane
          and 'files.backendRequest("helper-read"' in lane)
    check("qml.no-shell-string", "/bin/sh" not in module and "bash -c" not in module)
    cli = (ROOT / "agent_skills" / "cli.py").read_text(encoding="utf-8")
    check("cli.output-byte-cap", "MAX_OUTPUT_BYTES = 1024 * 1024" in cli and "def encoded(" in cli)
    check("cli.shared-watch-plan", "with WatchPlan() as plan:" in cli and "plan.finish(discovery.collect" in cli)
    for name, text in (("Module.qml", module), ("Service.qml", service)):
        texts = re.findall(r"\bText\s*\{", text)
        formats = re.findall(r"textFormat:\s*Text\.PlainText", text)
        check(f"qml.plaintext:{name}", len(formats) >= len(texts), f"{len(formats)}/{len(texts)}")
        check(f"qml.no-shellroot:{name}", "ShellRoot" not in text)
        check(f"qml.no-required:{name}", "required property" not in text)
    check("qml.service-item", service.lstrip().startswith("import QtQuick") and "\nItem {" in service)
    check("qml.service-injection", "property var shell: null" in service and "property var manifest: null" in service)

def test_keyboard_contract() -> None:
    module = (ROOT / "blades" / "Module.qml").read_text(encoding="utf-8")
    keymap = (ROOT / "blades" / "KeyMap.js").read_text(encoding="utf-8")
    check("keys.keymap-imported", 'import "KeyMap.js" as KeyMap' in module)
    check("keys.delegates-to-keymap", "KeyMap.resolve(event.key, event.modifiers, Qt)" in module)
    check("keys.single-handler", module.count("Keys.onPressed") == 1)
    check("keys.only-rescan-handled", module.count('"rescan"') == 1)
    for chord in ("Qt.Key_Tab", "Qt.Key_Backtab", "Qt.Key_BracketLeft", "Qt.Key_BracketRight"):
        check(f"keys.module-never-names:{chord}", chord not in module)
    for owned in ("Qt.Key_Home", "Qt.Key_End", "Qt.Key_PageUp", "Qt.Key_PageDown",
                  "Qt.Key_G", "Qt.Key_D", "Qt.Key_U", "Qt.Key_Escape", "Qt.Key_Slash"):
        check(f"keys.no-tree-duplicate:{owned}", owned not in module)
    check("keys.no-module-paging", "movePage" not in module and "pageBy" not in module)
    check("keys.no-module-jumps", "jumpTo" not in module)
    check("keys.no-module-collapse-chord", "toggleCollapsed" not in module)
    check("keys.no-bare-z", "Qt.Key_Z" not in module and "Key_Z" not in keymap)
    check("keys.keymap-is-pure", "import " not in keymap and "Qt." not in keymap)
    check("keys.keymap-pragma", keymap.lstrip().startswith(".pragma library"))
    check("keys.host-chord-guard", "function hostTabChord(" in keymap)
    for chord in ("Key_Tab", "Key_Backtab", "Key_PageUp", "Key_PageDown",
                  "Key_BracketLeft", "Key_BracketRight"):
        check(f"keys.chord-listed:{chord}", f"qt.{chord}" in keymap)
    returned = {value for value in re.findall(r'return "([^"]*)"', keymap) if value}
    check("keys.keymap-single-action", returned == {"rescan"}, str(sorted(returned)))
    check("keys.search-clears-query", 'query = ""' in module)

def test_header_contract() -> None:
    module = (ROOT / "blades" / "Module.qml").read_text(encoding="utf-8")
    check("header.shared-component", 'context.ui.url("PaneHeader")' in module)
    check("header.tabIndex",
          "item.tabIndex = Qt.binding(function() { return module.context.tabIndex })" in module)
    check("header.reservedLeft",
          "item.reservedLeft = Qt.binding(function() { return module.context.cornerReserveLeft })" in module)
    check("header.reservedRight",
          "item.reservedRight = Qt.binding(function() { return module.context.cornerReserveRight })" in module)
    check("header.no-hand-rolled", "Rectangle {\n    id: header" not in module)

def test_no_internal_symlinks() -> None:
    found = subprocess.run(
        ["find", str(ROOT), "-name", ".git", "-prune", "-o", "-type", "l", "-print"],
        capture_output=True, text=True, check=False,
    )
    check("tree.no-symlinks", found.stdout.strip() == "", found.stdout.strip()[:200])

def test_cli_end_to_end() -> None:
    binary = ROOT / "bin" / "agent-skillsctl"
    check("cli.executable", os.access(binary, os.X_OK))
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        home = tmp / "home"
        prefix = tmp / "prefix"
        repo = tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        write_skill(home / ".claude" / "skills", "user-skill")
        write_skill(repo / ".agents" / "skills", "project-skill")
        write_skill(prefix / "etc" / "codex" / "skills", "system-skill")
        completed = subprocess.run(
            [sys.executable, str(binary), "list", "--json",
             "--home", str(home), "--project", str(repo), "--prefix", str(prefix),
             "--platform", "linux"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        check("cli.exit-zero", completed.returncode == 0, completed.stderr[:200])
        check("cli.no-stderr", completed.stderr == "", completed.stderr[:200])
        payload = json.loads(completed.stdout)
        check("cli.schemaVersion", payload["schemaVersion"] == 1)
        check("cli.project", payload["project"] == str(repo), payload["project"])
        found = {row["name"]: row for row in payload["items"]}
        check("cli.user-skill", "user-skill" in found)
        check("cli.project-skill", "project-skill" in found)
        check("cli.system-skill", "system-skill" in found)
        check("cli.single-json-line", completed.stdout.count("\n") == 1)
        check("cli.agents-listed", payload["agents"] == list(registry.agents()))
        check("cli.watches-project", str(repo) in payload["watchPaths"])
        check("cli.watch-limit", len(payload["watchPaths"]) <= 512 and isinstance(payload["watchTruncated"], bool))
        native = subprocess.run(
            [str(CORE / "fileblade-bin"), "_backend", "helper-read", "--provider", "data-goblin.fileblade-skills",
             "--plugin-dir", str(ROOT), "--helper", "inventory", "--method", "list", "--arguments",
             json.dumps(["--project", str(repo), "--home", str(home), "--prefix", str(prefix), "--json"])],
            capture_output=True, text=True, check=False, timeout=30,
        )
        check("cli.native-helper-exit", native.returncode == 0, native.stderr[:200] or native.stdout[:200])
        try:
            delivered = json.loads(native.stdout)
        except ValueError:
            delivered = {}
        check("cli.native-helper-rows", delivered.get("ok") is True and delivered.get("items") == payload["items"])

        roots = subprocess.run(
            [sys.executable, str(binary), "roots", "--home", str(home), "--prefix", str(prefix),
             "--platform", "linux"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        check("cli.roots-exit-zero", roots.returncode == 0, roots.stderr[:200])
        root_rows = json.loads(roots.stdout)["roots"]
        check("cli.roots-documented", all(row["doc"].startswith("https://") for row in root_rows))
        check("cli.roots-inside-home-or-prefix", all(
            row["path"].startswith(str(home)) or row["path"].startswith(str(prefix))
            for row in root_rows if row["kind"] in ("user", "managed", "system")
        ))

        agents_out = subprocess.run(
            [sys.executable, str(binary), "agents"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        check("cli.agents-exit-zero", agents_out.returncode == 0)
        check("cli.agents-count", len(json.loads(agents_out.stdout)["agents"]) == 6)

        bad = subprocess.run(
            [sys.executable, str(binary), "nonsense"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        check("cli.unknown-command-fails", bad.returncode != 0)

        ident = found["user-skill"]["id"]
        base = [sys.executable, str(binary), "apply", "--json", "--home", str(home), "--project", str(repo),
                "--prefix", str(prefix), "--platform", "linux", "--id", ident]
        applied = subprocess.run(base + ["--agent", "codex", "--agent", "pi", "--state", "on"],
                                 capture_output=True, text=True, check=False, timeout=30)
        check("cli.apply-exit-zero", applied.returncode == 0, applied.stderr[:200])
        result = json.loads(applied.stdout)
        check("cli.apply-shape", result["ok"] is True and result["schemaVersion"] == 1
              and result["project"] == str(repo) and [row["agent"] for row in result["results"]] == ["codex", "pi"])
        check("cli.apply-result-keys", all(set(row) == {"agent", "ok", "changed", "message", "touched"}
                                           for row in result["results"]))
        check("cli.apply-linked", (home / ".agents" / "skills" / "user-skill").is_symlink())
        check("cli.apply-no-items-key", "items" not in result)
        refused = subprocess.run(base + ["--agent", "claude-code", "--state", "off"],
                                 capture_output=True, text=True, check=False, timeout=30)
        check("cli.apply-refusal-exit-one", refused.returncode == 1)
        check("cli.apply-refusal-payload", json.loads(refused.stdout)["ok"] is False)
        check("cli.apply-refusal-kept-dir", (home / ".claude" / "skills" / "user-skill" / "SKILL.md").is_file())
        missing = subprocess.run(base + ["--agent", "codex"], capture_output=True, text=True, check=False, timeout=30)
        check("cli.apply-requires-state", missing.returncode != 0)

def secure_read_contract() -> None:
    read = lambda name: (ROOT / name).read_text(encoding="utf-8")
    expect = check
    bounds_source = read("agent_skills/bounds.py")
    discovery_source = read("agent_skills/discovery.py")
    expect("return start, [start]" in discovery_source, "discovery.non_git_anchor_workspace")
    expect("clean(env.environ" not in discovery_source, "discovery.no_clean_on_env")
    expect("def env_path_value(" in bounds_source, "bounds.env_path_value")
    expect("MAX_ENV_PATH" in bounds_source, "bounds.env_path_limit")
    expect("metadata = os.fstat(descriptor)" in bounds_source
           and "metadata.st_uid != 0" in bounds_source
           and "stat.S_IWGRP | stat.S_IWOTH" in bounds_source
           and "read_descriptor(path, limit, secure=enforce)" in bounds_source, "bounds.securely_owned")
    expect("O_NOFOLLOW" in bounds_source, "bounds.nofollow")

def main() -> int:
    test_manifest()
    test_license_and_readme()
    test_qml_shape()
    test_keyboard_contract()
    test_header_contract()
    test_no_internal_symlinks()
    test_cli_end_to_end()
    secure_read_contract()
    failures = [row for row in RESULTS if not row[1]]
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"FAIL {name} {detail}")
    print(f"contract: {len(RESULTS) - len(failures)}/{len(RESULTS)} passed")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
