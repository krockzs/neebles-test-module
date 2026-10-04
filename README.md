# N.E.E.B.L.E.S. Test Module

`neebles-test-module` is the canonical reference module and tutorial for building a real N.E.E.B.L.E.S. module.

It is not a production dependency and it is not allowed to define Boss architecture.

Its purpose is to show, with a working module, **how a consumer declares itself, obtains certified material/worlds, connects to Boss, starts its runtime, registers endpoints and projects UI/Tray/Settings/Notifications without adding module-specific code to Boss**.

> **Boss governs. CUSTOM/Esbirro certifies material and worlds. OS supplies platform authority. The module declares and implements behavior.**

Current module version:

```text
1.2.0
```

Current module schema:

```text
4
```

The working tree contains the current runtime-birth adaptation and must be committed to a new immutable revision before the next Boss Registry/CUSTOM pin is finalized.

---

# 1. What to copy from this repository

Do **not** copy Python/Tk because "that is how N.E.E.B.L.E.S. modules are made".

Python/Tk is only this module's current implementation.

What future modules should copy is the connection pattern:

```text
manifest
contracts
Lifecycle
Surfaces
Settings
runtime entrypoint
Module IPC registration
Construction declaration
CUSTOM package/material declaration
runtime world
governed Open
optional Tray
optional Notifications
```

A Rust, Go, Node.js, C++, Java or other module can follow the same architecture.

---

# 2. Ownership map

```text
Module repository
    -> module manifest/contracts/runtime implementation

CUSTOM / Esbirro
    -> package membership
    -> material integrity
    -> runtime world
    -> Construction declaration

OS
    -> platform authorities/providers

BUILD
    -> image-side authority/declaration materialization
    -> shared module territory

Boss
    -> Registry consumption
    -> Preinstall
    -> materialization
    -> Lifecycle
    -> privilege
    -> runtime IPC
    -> state/settings/notifications/surfaces
```

The module never downloads or installs its own system package closure as a private apt flow.

---

# 3. Repository structure

Current reference structure:

```text
neebles-test-module/
├── manifest.json
├── lifecycle.json
├── surfaces.json
├── runtime.py
├── README.md
├── icon.jpeg
├── contracts/
│   └── commands.json
├── settings/
│   └── default.json
├── languages/
│   ├── manifest.json
│   ├── es_CL.json
│   └── en_US.json
├── tray/
│   └── tray-provider.py
├── ui/
│   └── test-module-ui.py
└── critical-update/
    └── manifest.json
```

Not every future module needs every optional directory.

---

# 4. `manifest.json`

The manifest declares identity and public module surfaces.

Current Test Module declares:

- Schema 4;
- module identity;
- version 1.2.0;
- runtime entrypoint `runtime.py`;
- Lifecycle;
- Surfaces;
- dynamic Commands contract;
- Settings defaults;
- Tray provider;
- Notifications protocol.

Boss reads declared contracts.

Boss does not inspect Python source to invent contracts.

Legacy top-level:

```text
manifest.commands
```

must not be used.

The dynamic contract type:

```text
commands
```

is valid.

---

# 5. Registry pin

A production module entry in the Boss Registry should select an immutable source commit.

Conceptually:

```json
{
  "repo": "https://github.com/example/module.git",
  "version": "1.0.0",
  "folder": "example-module",
  "commit": "<immutable commit>"
}
```

Do not use a floating branch as installed module truth.

For Test Module, Boss Registry and CUSTOM Construction must reference the same committed revision.

---

# 6. Material declaration in CUSTOM

The module repository does not own Debian package closure truth.

CUSTOM does.

For a module named `example-module`, declare package membership in:

```text
runtime/manifests/modules/example-module.packages.tsv
```

Columns:

```text
package
version
arch
filename
sha256
```

This answers:

> Which exact packages are required?

---

## Material integrity

Declare required resulting material in:

```text
runtime/manifests/modules/example-module.manifest.json
```

This answers:

> Which exact files/directories/symlinks must exist?

Keep the contracts separate:

```text
membership != integrity
```

For required package files, filename/SHA256 must agree.

---

# 7. Shared package pool

Module material is shared.

Canonical source territory:

```text
CUSTOM:
runtime/modules/packages/
runtime/modules/rootfs/
```

Observed installed/runtime territory:

```text
/opt/neebles-build/modules
```

Uninstall does not delete the shared package pool.

There is no per-module package ownership/refcount model.

---

# 8. Preinstall

The module does **not** run Preinstall.

Boss does.

Correct flow:

```text
Boss install/update
    -> read module package membership
    -> verify existing package files
    -> reuse valid package
    -> obtain missing exact package
    -> reject mismatched package
    -> materialize module runtime material
    -> continue Lifecycle
```

The module must not contain a hidden alternative installer for the same dependencies.

---

# 9. Runtime world

A module that needs a controlled runtime references a world provided by CUSTOM/Esbirro.

The Test Module currently uses:

```text
modules.python3.13-tk
```

Its world exposes:

```text
executable:
    usr/bin/python3.13

library_paths:
    usr/lib/x86_64-linux-gnu

runtime_paths:
    usr/lib/python3.13
    usr/lib/tcltk
    usr/share/tcltk
```

This is one example.

A future Node.js module should request a certified Node world.

A future Rust module may need a different runtime/material shape.

**Do not add technology-specific source code to Boss merely to resolve the new world.**

---

# 10. Domestic Construction

CUSTOM stores the module Construction declaration:

```text
runtime/construction/<module_id>.json
```

Construction tells Boss **what controlled step to execute**, using generic fields.

The current Test Module declaration has:

```text
init
fetch
checkout
open-runtime
```

---

## Source acquisition steps

Current `init`, `fetch` and `checkout` use:

```text
runtime_authority: boss.runtime
world: boss.git
execution: foreground
session: false
```

They write only inside the supplied domestic workspace authority.

This demonstrates that Boss can use a certified infrastructure tool without exposing host Git as fallback authority.

---

## Runtime start step

Current `open-runtime` uses:

```text
runtime_authority: modules.runtime
world: modules.python3.13-tk
execution: persistent
session: true
```

It requests:

```text
readonly:
    boss.modules.ipc

dynamic_readonly:
    authority: modules.installed_runtime
    source: /opt/neebles/modules/test-module
    destination: /opt/neebles/modules/test-module
```

and starts:

```text
/opt/neebles/modules/test-module/runtime.py
--intent
open
```

This is the canonical reference for a graphical persistent module runtime.

---

# 11. Lifecycle

`lifecycle.json` binds Governor actions to module-owned transitions.

Install/update/uninstall/enable/disable may be empty when no extra module-specific operation is required.

Do not invent fake work merely to make a transition non-empty.

---

## Governed Open

The important current integration is:

```text
governor.open
    -> open
```

The `open` transition executes:

```text
artillery: boss.workspace_execution
objective: construction.step
munition:
    subject: test-module
    step: open-runtime
```

This means:

```text
Launcher / command Open
    -> Governor
    -> Lifecycle
    -> generic workspace execution
    -> CUSTOM Construction
    -> certified module runtime world
```

Boss contains no Test Module-specific launch branch.

---

# 12. Persistent runtime

`open-runtime` is persistent.

Boss spawns the runtime and returns control instead of waiting for the runtime's entire lifetime.

The child is reaped when it eventually exits.

The module runtime itself remains responsible for its application behavior and cooperative shutdown protocol.

---

# 13. Desktop session

The Test Module runtime is graphical, so Construction requests:

```text
session: true
```

Boss resolves the certified desktop-session interface.

It may project:

```text
XDG_RUNTIME_DIR
DBUS_SESSION_BUS_ADDRESS
DISPLAY
WAYLAND_DISPLAY
XAUTHORITY
```

plus the exact physical sockets/files required.

Boss also resolves the authenticated desktop UID/GID and enters that identity using the certified `boss.setpriv` world.

The runtime does not inherit arbitrary host environment as authority.

---

# 14. Module IPC

The runtime connects to:

```text
/run/neebles/modules.sock
```

The socket is exposed through the narrow OS authority:

```text
boss.modules.ipc
```

not by exposing the entire `/run` tree.

---

## Registration sequence

A normal runtime should:

```text
connect
    -> register module/session/endpoints
    -> validate registered response
    -> subscribe to required topics
    -> enter invoke/event loop
```

The Test Module also supports:

```text
--intent open
```

After registration/subscription, the `open` intent launches its UI.

This proves runtime birth without bypassing Boss.

---

## Runtime identity

Boss authenticates the real Unix peer.

Runtime identity is bound to process evidence.

A runtime cannot become authoritative merely by claiming a module name in JSON.

---

# 15. Commands contract

The current Commands contract exposes:

```text
open
version
hello
notify
state
settings
setting
toggle
events
external
```

The runtime discovers its endpoints from the contract.

Do not maintain a second manually diverging endpoint list.

Privilege policy remains installed-contract truth.

Runtime advertisement is live availability only.

---

# 16. Surfaces

The current module exposes the Launcher Open surface.

A surface is a presentation projection.

It is not a second functional state authority.

Future modules may expose:

- zero surfaces;
- one surface;
- multiple UI/Launcher/Tray surfaces.

Boss must remain generic.

---

# 17. UI

The current UI is implemented with Tk.

That is not architectural.

The UI consumes canonical module settings/state and sends intent back through governed paths.

The UI must not become the persistence authority.

---

# 18. Settings

Current feature examples:

```text
features.option1
features.option2
```

The rule is:

```text
writer
    -> Boss Settings
    -> canonical persistence
    -> settings event
    -> UI/Tray refresh
```

Persist first, project later.

---

# 19. Tray

The current Tray provider is optional module behavior.

Tray:

- consumes canonical settings;
- may request SettingsGet/SettingsSet;
- reacts to settings changes;
- publishes visual state.

Tray does not own global module Active/Inactive state.

---

# 20. Notifications

The current module uses Notifications protocol 4.

Module notifications travel over Module IPC.

The module declares intent.

Boss owns:

- policy;
- validation;
- desktop presentation;
- notification ownership;
- replacement routing;
- return routing.

A module should not invoke a private host notification transport to bypass Boss.

---

# 21. Critical Update

The module owns:

```text
critical-update/manifest.json
```

An empty instruction set is valid when the release does not require Critical Update work.

Do not invent an operation merely to populate the file.

---

# 22. Uninstall/reinstall law

Uninstall may remove module installation/state according to governed policy.

It does **not** remove the shared domestic package pool.

A later reinstall may reuse already-verified `.deb` files.

This is expected behavior.

---

# 23. Minimal recipe for a new module

For a new module `example-module`:

```text
1. Create the module repository.
2. Define manifest.json with Schema 4.
3. Define only the contracts the module actually needs.
4. Define lifecycle.json with real transitions.
5. Add runtime code that registers through Module IPC if a persistent runtime is needed.
6. Add CUSTOM package-membership TSV if system/runtime packages are required.
7. Add CUSTOM material-integrity manifest.
8. Add or reuse a certified runtime world.
9. Add CUSTOM Construction declaration for build/start steps.
10. Request only exact OS authorities needed.
11. Add immutable Registry commit.
12. Install through Boss.
13. Let Boss perform Preinstall/materialization.
14. Exercise Lifecycle.
15. Verify runtime registration.
16. Verify UI/Tray/Notifications only when the module declares them.
17. Verify uninstall/reinstall and shared package reuse.
```

---

# 24. When Boss should change

A module should **not** cause a Boss change merely because it needs:

- Python instead of Rust;
- Node.js instead of Python;
- another package set;
- another runtime world;
- another module install directory;
- another module identity;
- another executable inside an existing generic world contract.

Boss should change only when the ecosystem truly lacks a generic **HOW** capability.

Example:

```text
new module needs an already-supported generic readonly projection
    -> no Boss architecture change

new module needs a genuinely new generic execution primitive
    -> evaluate/add generic Boss capability
```

Never add a module-name branch.

---

# 25. What not to copy

Do not copy these as architecture requirements:

```text
Python
Tkinter
test-module identity
its exact package list
its exact UI
its exact Tray behavior
```

Copy the contract relationships.

---

# 26. Current certification status

Current source-side reference gates are GREEN for:

```text
Schema 4
Construction contract
runtime world
47-DEB declarative package set
module material manifest
governor.open
construction.step
persistent execution
desktop-session projection
boss.modules.ipc
dynamic installed-runtime readonly projection
runtime --intent open
Boss module-agnostic audit
full Boss Rust regression
```

Fresh Live still must prove the complete real runtime birth inside the newly rebuilt image.

---

# 27. Final tutorial law

If a future module can:

```text
declare itself
    -> obtain exact certified material
    -> use a declared world
    -> request exact authorities
    -> execute through Lifecycle
    -> start/register its runtime
    -> expose behavior
    -> update/uninstall/reinstall
```

without adding module-specific source to Boss, the architecture is working.

That is the purpose of N.E.E.B.L.E.S. Test Module.
