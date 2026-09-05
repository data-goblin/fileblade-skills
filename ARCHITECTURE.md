# Skills architecture

The Omarchy service owns one lazily loaded FileBlade `ArtifactInventory`.
Visible views attach to it; the final detach stops discovery and filesystem
subscriptions. Search, grouping, selection and expansion remain view-local.

The manifest declares `bin/agent-skillsctl` with `list` as a read method and
`apply` as a write method. FileBlade's resident backend runs it with bounded
arguments, output and an eight-second deadline. Accepted link changes retain
their original project and finish after the view closes or changes project.
Disabling the provider cancels its work. These ownership and resource limits
do not sandbox an enabled Omarchy plugin.

Discovery records bounded source-directory watches through FileBlade's shared
Python watch planner. Missing roots watch an existing parent; linked skill
directories also watch their target. External additions, descriptor changes,
removals and directory replacement trigger rescanning. Partial watch coverage
is visible and can be retried with Refresh.

`ArtifactTree` owns navigation, file actions, cursor visibility and folder
loading. Skills supplies folder rows, descriptor paths, groups and agent-link
actions. It has no separate child-request queue, filesystem cache or process
runner. Expanded folders use the same native listing and row conversion as
Files; nested changes and hidden-file settings are observed by the shared tree.

Helper directory walks bound examined names before sorting, including entries
that are not skills. The output remains capped at 256 skills and 1 MiB. A
truncated scan is reported, and unlink refuses an incomplete root scan.
Protected system settings are read and ownership-checked through the same
non-following file descriptor. Filesystem identities use FileBlade's shared
native-path codec, separately from display labels.

Link creation and removal use the shared native mutation boundary: creation is
exclusive, unlink checks the selected symlink's identity, and descriptor-relative
operations refuse substituted entries instead of following later path changes.

`tests/run` is the local gate: discovery/apply tests, native-path regressions,
watch and read-boundary tests, key and host contracts, actual native helper
dispatch, read-only imports, provider cold loading, and QML validation.

## Missing host

`Service.qml` loads `HostGuard.qml` once the shell injects `pluginRegistry`.
`HostGuard.js` decides from the registry alone: nothing shows while
`data-goblin.fileblade` is installed and enabled; otherwise the alphabetically
first enabled plugin that declares a `data-goblin.fileblade/*` extension owns
one overlay listing every waiting extension. Install runs detached through
`sh -c` because the clone landing in the plugins directory hot-reloads every
third-party plugin, guard included: `omarchy plugin add --enable --yes` (or
`omarchy plugin enable` when the host is installed but disabled), a wait for
the entry in `shell.json` and the host IPC target, then
`omarchy restart shell`. Failure raises a critical notification with the last
error line and rescans plugins so a fresh guard reappears. The close glyph or
Escape hides it until the next shell start. The card reuses the host's look:
`assets/fileblade-logo.png` tinted with the accent colour, and the welcome
tab's accent Install button. `tests/tst_host_guard.qml` covers the
decision table offscreen.
