# Agent Skills

An Omarchy Quattro plugin that lists agent skills (`SKILL.md` packages) from the
documented discovery roots of six coding agents, grouped by scope and source,
inside a blade of Omarchy Fileblade.

## Required dependency and Install order

**Omarchy Fileblade (`data-goblin.fileblade`) must be installed and enabled first.**

Requires Omarchy 4.0.2 or later, core FileBlade and Python 3.11+. Follow the direct GitHub installation
and removal instructions in the [root README](../../README.md), then select
Skills in a FileBlade module slot. No marketplace listing is required.

The contribution uses `extensions["data-goblin.fileblade/blade"]` with
`hostContract: 2`. Its service supplies the missing-host prompt and provider
lifecycle. With FileBlade unavailable, the shared guard offers to install or
enable the host. It does not install anything without an explicit action.
Inventories reuse FileBlade's shared services; see the
[host contract](https://github.com/data-goblin/fileblade/blob/main/EXTENSIONS.md).
Removing the extension preserves host layout/view state, recoverable bins and
previous changes to the user's files or agent configuration.

## What it shows

Every `SKILL.md` package found under a **documented** discovery root, deduped by
resolved target within a scope, with the agents that read each root.

Grouping is `scope > plugin`.

### Column control

The header (or the tab bar, when the slot has several tabs) carries one column
control shared with every Fileblade module. Its metric, sort, and filter are
remembered per module through the blade state.

```yaml
left click:   sort by the current metric; cycles descending, ascending, off
              (numbers and dates start descending, text starts ascending)
right click:  menu with the metric radio list, Sort ascending / descending /
              Clear sort, Filter…, Clear filter. Enter, Space, Menu, or
              Shift+F10 open the same menu from the keyboard
filter popup: since / until for the date metrics (Updated, Created) with 7d,
              30d, 90d, 1y presets and free text such as 2026-08, 3w, yesterday;
              min / max for the number metrics (Tokens for descriptions, Tokens for SKILL.md, Characters, Words, Size),
              accepting 1.5k style suffixes. An empty popup clears the filter
trigger text: short metric label, plus ↑ or ↓ when sorted by it and a filter
              glyph when a filter is active
```

Metrics and their kinds:

```yaml
agents:     agents      the default; renders the agent strip on every row
updated:    date        SKILL.md modification time
created:    date        SKILL.md birth time, empty when the filesystem has none
tokens:     number      transparent estimate for the frontmatter description only, UTF-8 bytes divided by four
fileTokens: number      the same estimate over the whole SKILL.md
characters: number      Unicode characters
words:      number      Unicode words
bytes:      number      descriptor size, shown as B / KB / MB
summary:    text        frontmatter description, not a discovery category
off:        text        no column
```

Sorting works inside each group; the filter runs before grouping, and the
number metrics draw a data bar proportional to the largest visible value. All
counts are exact for descriptors within the 64 KiB read bound.

### Agent strip

With the `agents` metric every skill row ends in one icon per installed agent,
in brand colour when that agent reads the skill and grey when it does not.
Installed agents come from Fileblade's `files.installedAgents` (a binary on
`PATH` or the agent home directory present). Clicking an icon runs
`agent-skillsctl apply` for that one agent with the opposite state and rescans.
The robot glyph on the left turns every installed agent on, or, when every
installed agent already reads the skill, turns them all off. While a call runs
the header status reads `Applying…`; when the backend refuses, its message
stays in the header status until the next rescan you trigger (`Shift+R` or an
anchor change). On the Summary column a skill without a description falls back
to its badge text: `off` for a disabled plugin or Codex switch, `N agents` when
several agents read it.

## Search syntax

The filter field is Fileblade's shared `PaneSearchField` with the FILES search
syntax: bare words match anywhere (case-insensitive), `"quoted text"` matches
exactly, `-word` excludes, `name:x` matches the row label only, and the
field keys shown in the placeholder (`agent, scope, source, plugin`) take exact comma-separated
values, negatable with a leading `-` (`agent:codex -scope:project`). Unknown keys are searched as
plain text.

## Keyboard

Fileblade's shared `ArtifactTree`, `PaneSearchField`, and `BladeSlot` own every
navigation key, so this pane behaves exactly like every other Fileblade pane.
This module adds one binding of its own and consumes nothing else.

```yaml
move:            j / k, Down / Up                    ArtifactTree
hierarchy:       h / l, Left / Right                 ArtifactTree
                 h collapses a group or steps to its parent
                 l expands a group, or opens a skill folder in Files
page:            Ctrl+D / Ctrl+U, PageDown / PageUp  ArtifactTree
first / last:    g / G, Home / End                  ArtifactTree
                 gg is g twice and lands in the same place
search:          /                                   ArtifactTree
sort:            s cycles the current metric         ArtifactTree
filter popup:    f                                   ArtifactTree
activate:        Enter / o                           ArtifactTree; opens the skill folder in Files
reveal:          r                                   ArtifactTree
back out:        Escape                              ArtifactTree
between slots:   Tab / Shift+Tab                     ArtifactTree
between tabs:    Ctrl+Tab / Ctrl+Shift+Tab           BladeSlot
                 Ctrl+PageDown / Ctrl+PageUp
                 Ctrl+] / Ctrl+[
collapse slot:   Alt+Z or header disclosure chevron BladeSlot / PaneHeader
rescan:          Shift+R                             this module
column menu:     Menu / Shift+F10 / Enter or Space   Fileblade column control
menu choices:    j / k, g / G, Home / End, Enter    Fileblade column control
```

`blades/KeyMap.js` resolves exactly one action, `rescan`, and returns nothing
for every other key. It explicitly returns nothing for any `Ctrl`-modified
`Tab`, `Backtab`, `PageUp`, `PageDown`, `[`, or `]`, so a `BladeSlot` tab-cycle
chord is never consumed here. `tests/keymap.py` asserts that across the full
modifier matrix, and asserts that no key other than `Shift+R` resolves to a
module action, using the Qt key and modifier values read from the installed Qt
headers.

### Mouse actions and their keys

```yaml
click a row:            j / k
click a group chevron:  h / l
double-click a row:     Enter / o
clear the search field: Escape
column control click:   s
column control menu:    Enter / Space / Menu on the control, f for the filter
agent icon click:       no keyboard equivalent yet
header disclosure:      Alt+Z
header drag to reorder: no keyboard equivalent; a Fileblade host action
```

## Supported agents and roots

Only paths named in each project's own documentation are scanned. No path is
inferred from a dot-directory that happens to exist.

```yaml
Claude Code:
  managed:  /etc/claude-code/.claude/skills                     Linux and WSL
            /Library/Application Support/ClaudeCode/.claude/skills   macOS
            C:\Program Files\ClaudeCode\.claude\skills          Windows
  user:     ~/.claude/skills
  project:  .claude/skills, in the anchor directory and every parent up to the
            repository root
  plugin:   <installPath>/skills and <installPath>/SKILL.md, where installPath
            comes from ~/.claude/plugins/installed_plugins.json
  reserved: ~/.claude/skills/synced, scanned one level deeper
  enabled:  ~/.claude/settings.json -> enabledPlugins
  precedence: managed 0, user 1, project 2

Codex:
  project:  .agents/skills, anchor directory through repository root
  user:     ~/.agents/skills
  system:   /etc/codex/skills
  enabled:  ~/.codex/config.toml -> [[skills.config]] path, enabled
  precedence: project 0, user 3, system 4

OpenCode:
  project:  .opencode/skills, .claude/skills, .agents/skills
  user:     ~/.config/opencode/skills, ~/.claude/skills, ~/.agents/skills
  precedence: not documented, reported as null

Pi:
  user:     ~/.pi/agent/skills, ~/.agents/skills
  project:  .pi/skills, .agents/skills
  precedence: as listed in the Pi documentation, 0 through 3

GitHub Copilot CLI:
  user:     ~/.copilot/skills, ~/.agents/skills
  project:  .github/skills, .claude/skills, .agents/skills
  precedence: not documented, reported as null

Google Antigravity:
  user:     ~/.gemini/antigravity-cli/skills
  project:  .agents/skills
  precedence: not documented, reported as null
```

### Enable and disable state

```yaml
per-skill /skills state:     unknown, for the same reason. `/skills disable`
                             defaults to user scope, and its storage is
                             undocumented
```

On a production Linux read the two system files must be regular, owned by root,
and not group or world writable, or they are ignored. Nothing else from those
files is read or emitted, and no new system skill directory is introduced.

### Workspace resolution

Project roots are discovered by walking up from the selected directory to the
repository root, and every directory along that walk is searched. When no
repository marker is found the selected directory alone is the workspace, so a
plain folder still contributes its `.agents/skills`,
`.opencode/skills`, `.pi/skills`, `.claude/skills`, and `.github/skills`
directories. Arbitrary parents of a non-repository folder are never scanned,
which keeps an unrelated directory above your workspace from injecting skills.

### Applying a skill to agents

`agent-skillsctl apply` is the only writer in this plugin. It links or unlinks
one skill for one or more agents and prints one result per agent:

```bash
./bin/agent-skillsctl apply --project <dir> --id <row id> --agent codex --agent pi --state on --json
./bin/agent-skillsctl apply --project <dir> --id <row id> --agent all --state off --json
```

```yaml
payload:  { ok, schemaVersion: 1, project, id, state,
            results: [ { agent, ok, changed, message, touched: [paths] } ] }
exit:     0 when every result is ok, 1 when any result is a refusal
on:       creates <agent root>/<skill directory name> as a symlink to the
          realpath of the directory holding SKILL.md. The root is the first
          documented root for that agent in the row's scope: user rows link
          under $HOME, project rows
          link under the resolved project root, never under a nested anchor.
          A missing root directory is created. An agent that already reads the
          skill reports ok with changed false
off:      unlinks every symlink in that agent's roots for the scope whose
          target is the skill directory, and reports ok with changed false when
          there is none
shared:   ~/.agents/skills and <project>/.agents/skills are read by several
          agents, so switching one of them switches all of them. The message
          says so, for example "also applies to codex, opencode, pi,
          copilot-cli, antigravity"
refuses:  (ok false, changed false, nothing written) when the link path exists
          and is not a symlink, when it is a symlink to a different directory,
          when an entry to remove is a real directory (the only copy of the
          skill), when the row is plugin, extension, managed, or system scope,
          when the agent id or row id is unknown, when a project row has no
          resolved project, or when the skill directory name is not a single
          path component
never:    deletes a non-symlink, rewrites an existing link, or touches a file
          outside the documented roots. `list` still writes nothing at all and
          the tests snapshot the tree to prove it
```

Within one call agents are handled in order and the row is re-resolved after
each change, so `--agent all` links the shared `.agents/skills` once and
reports the other readers of that root as already applied instead of adding
redundant links in their private roots.

### Deliberately not scanned

- `~/.codex/skills`. Present on some machines, named in no Codex document
- `~/.gemini/antigravity/global_skills`. Named in no Antigravity document
- `~/.gemini/antigravity/skills` and `.agent/skills`. Their current primary
  documentation could not be verified, so this plugin does not guess them
- any other `~/.<name>/skills`, because a folder called `skills` is not evidence
  of an agent
- `skill.md` in lower case. Every project that states a filename requires
  `SKILL.md`
- Antigravity CLI plugin skills, because that project does not document where
  those live on disk
- Claude Code's lazily-loaded nested project skills below the anchor directory,
  because they are only reachable through paths the agent itself decides to open

### Documentation

- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code managed settings: https://code.claude.com/docs/en/managed-settings
- Codex skills: https://developers.openai.com/codex/skills
- OpenCode skills: https://opencode.ai/docs/skills/
- Pi skills: https://pi.dev/docs/latest/skills
- GitHub Copilot CLI skills: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills
- Antigravity IDE skills: https://antigravity.google/docs/ide/skills/
- Antigravity CLI plugins and skills: https://antigravity.google/docs/cli/plugins/

Agent and product names are used only to describe which discovery paths this
plugin supports. This is an unofficial project with no affiliation with, or
endorsement by, Anthropic, OpenAI, GitHub, Google, or the OpenCode or Pi
projects.

## Security boundaries

- **Read only, except symlinks you ask for.** `list`, `roots`, and `agents`
  write nothing. `apply` runs only from a click on the agent strip, creates or
  removes symlinks inside documented agent skill roots, and never deletes,
  moves, or rewrites a real file or directory. Enter opens the skill folder in
  Fileblade; the drop action's `Open SKILL.md` command opens the descriptor in the editor
- **No network.** Nothing is fetched, and no dependency is installed
- **No privilege.** No `sudo`, `pkexec`, service, or system configuration change
- **Bounded descriptor reads.** Each `SKILL.md` is opened once with `O_NOFOLLOW`
  and `O_NONBLOCK`, checked with `fstat` for a regular file and a 64 KiB size
  limit, and read from that same descriptor. A FIFO, device, or symlinked
  descriptor is refused. A skill *directory* may still be a symlink, which is
  what Claude Code documents
- **Bounded traversal.** At most 256 roots, 512 entries per root, 8192 entries
  total, 256 plugins, and a 32-level project walk
- **Bounded output.** At most 256 rows, a 256-character name and a 512-character
  description per row, with control characters stripped. The QML side re-clamps
  everything after parsing and refuses a payload without `schemaVersion: 1`
- **No shell.** The helper is spawned as an argument array. No value from disk
  reaches a shell, a command name, an option, or a file path the plugin opens
- **Plain text only.** Every `Text` binding a discovered value sets
  `textFormat: Text.PlainText`, so a `SKILL.md` cannot inject rich text or a
  resource URL
- **Bounded lifecycle.** One scan at a time, an 8 second timeout, a request
  generation that discards a stale result, cancellation on destruction, and no
  scanning at all while the blade is closed or the slot is collapsed

## Requirements

- Omarchy Quattro with Quickshell
- Omarchy Fileblade (`data-goblin.fileblade`), installed and enabled
- Python 3.11 or newer, for `tomllib`. Nothing else; no third-party packages

## Development

```bash
./tests/run
omarchy plugin validate .
```

`tests/run` needs Python 3.11 or newer plus, for the key map matrix only, the
Qt 6 headers (`qt6-base`) and one of `bun`, `node`, or `deno`. It reads the real
`Qt::Key_*` and `Qt::KeyboardModifier` values from
`/usr/include/qt6/QtCore/qnamespace.h` rather than hardcoding them, and
evaluates `blades/KeyMap.js` unmodified. None of that is needed at runtime.

`tests/unit.py` injects a synthetic home, project, and system prefix through
`--home`, `--project`, `--prefix`, and `--platform`, so no test reads your real
agent configuration. `tests/contract.py` checks the manifest against the
installed validator's rules, the QML host contract, the absence of internal
symlinks, and the CLI end to end.

The helper is usable on its own:

```bash
./bin/agent-skillsctl agents
./bin/agent-skillsctl roots --project .
./bin/agent-skillsctl list --project . --json
./bin/agent-skillsctl apply --project . --id <row id> --agent codex --state on --json
```

`--home`, `--prefix`, and `--platform` work on `apply` too, so a test can link
inside a synthetic home without touching yours.

## Known limitations

- Precedence is reported only where a project documents it. OpenCode, Copilot
  CLI, and Antigravity report `null` rather than a guess
- Enable state is available only for Claude Code plugins and Codex
  `[[skills.config]]` entries. Every other row reports `null`, meaning "this
  agent documents no switch", not "off"
- Bundled first-party skills that ship inside Codex and Antigravity
  are not listed, because none of those projects documents an on-disk location
- A `SKILL.md` whose front matter exceeds 32 KiB is listed by directory name
  with an empty description rather than being parsed
- The scan is on demand. It runs on load, on an anchor change, on `Shift+R`,
  and after every `apply`; it does not watch the skill directories for changes
- `apply` can only make an agent read a skill through a symlink in that
  agent's own root. It cannot flip a Codex `[[skills.config]]` switch or a
  Claude Code plugin enable flag, so a row marked `off` stays off after linking
- Reordering a slot by dragging its header has no keyboard equivalent. That
  action belongs to Fileblade's blade host, not to a module
- `Home`/`End` mirror `g`/`G`, while `Alt+Z` toggles the current slot without
  taking bare `z` away from the Files module's zoxide navigation
