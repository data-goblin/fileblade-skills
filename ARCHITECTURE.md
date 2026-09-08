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

This file was written by an agent.

## Provider ownership and host availability

The blade contribution declares `provider: "Provider.qml"`. FileBlade creates
one nonvisual provider per enabled extension identity and shares it across its
views. It supplies `providerId`, the canonical absolute `providerRoot`, `files`,
and `inventoryComponentUrl` at construction. The provider exposes `inventory`,
`error`, `observers`, `viewCount`, `attach(context)`, `detach(context)`, and
`shutdown()`. Construction stays idle. Duplicate attachment is harmless, the
last detach suspends the shared inventory, and shutdown unloads it and refuses
late attachments. Existing inventory options and module contract 2 are preserved.

`Service.qml` resolves its directory from its own QML URL, even when the shell
strips the manifest's source directory. It lazily delegates to the same provider
only when an older FileBlade calls attach. The new host owns its provider directly,
so its companion Service never creates a second inventory. A legacy companion
without provider metadata still requires its actual old-shell service; a new
host on a restricted shell must request an extension update instead of loading
that old Service itself. Updating companions alone cannot repair an old core on
the restricted shell.

The missing-host card no longer inspects foreign registry entries.
`bin/fileblade-host-status` reads `omarchy plugin list --json`, validates unique
IDs and Boolean enabled states, then checks the enabled host with
`omarchy-shell data-goblin.fileblade status`. Each command has a two-second
deadline, 128 KiB stdout and 4 KiB stderr limits, and process-group cleanup.
Listings are limited to 512 rows; the helper returns only the four known companion
names and states. It reads no agent configuration and downloads nothing.

Missing, disabled, starting, ready, and unknown states stay distinct. Only a
confirmed disabled host offers the existing explicit Enable action. Starting
or failed checks never offer installation or enablement. The first enabled
companion in a successful listing owns the card. Polling backs off to 30 seconds,
and dismissal stops checks until the next shell start. This is presentation;
FileBlade's catalog separately controls permission to load providers and helpers.

The QML lifecycle and guard tests plus the standalone host-check tests are part
of `tests/run`. They cover cold creation, shared observers, last detach, terminal
shutdown, stripped manifests, both provider ownership paths, unavailable commands,
malformed authority, output limits and timeouts. User-visible expectation: an
enabled responding FileBlade produces no missing-host card on either shell API.
