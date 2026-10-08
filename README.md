# N.E.E.B.L.E.S. Test Module

`neebles-test-module` is the canonical reference module and tutorial for building a real N.E.E.B.L.E.S. module.

It is not a production dependency and it is not allowed to define Boss architecture.

Its purpose is to show, with a working module, **how a consumer declares itself, obtains certified material/worlds, connects to Boss, starts its runtime, registers endpoints and projects UI/Tray/Settings/Notifications without adding module-specific code to Boss**.

> **Boss governs. CUSTOM/Esbirro certifies material and worlds. OS supplies platform authority. The module declares and implements behavior.**

Current module version:

```text
1.2.2
```

Current module schema:

```text
4
```

The current reference adaptation follows the governed MaterialBinding schema 2 architecture. Boss Registry selects the module repository through an immutable module-source commit. Independently, Boss Preinstall authenticates an exact CUSTOM V2 revision that owns the package, material, runtime-world and Construction truth consumed by the installed module. Those are separate revision identities and must not be conflated. Fresh Live and installed-system acceptance remain mandatory final gates.

## CAST30 patch 1.2.2 — source staging

This patch teaches the reference runtime to consume the authenticated
`notification_closed` callback returned by Boss Notifications protocol 4.
The event is recorded with its notification id and closing reason; foreign
module or session identity remains rejected and unknown IPC messages remain
unhandled. This is module-side protocol handling, not a new Boss capability.

The module source is installable only after **both** the Boss Registry immutable
source commit and CUSTOM V2 Construction `fetch`/`checkout` source selectors
point to this exact new commit. This README does not claim that those pins
have already been published or that Fresh Live/installed-system acceptance
has passed. The certified Essential layer, module package delta and Python/Tk
world remain unchanged by this source-only fix.

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
    -> image-side materialization
    -> recovery environment
    -> ISO composition

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
- version 1.2.2;
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

For Test Module, the Boss Registry commit pins the module-source revision. CUSTOM V2 has its own immutable revision, selected and authenticated by Boss for package, material, runtime-world and Construction truth. These are separate pins: coherence means that each consumer uses the exact immutable revision declared by its own contract, not that both SHA values are equal.

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

# 7. MaterialBinding, package pools and RuntimeLease

CUSTOM V2 owns the exact global Essential package layer, the per-module package delta, material-integrity manifests, runtime-world truth and module Construction declaration.

The productive Boss-side material territories are:

```text
/opt/neebles-build/modules/packages/essentials/
    -> permanent verified Essential DEB pool

/opt/neebles-build/modules/packages/
    -> permanent verified module-delta DEB pool

/opt/neebles-build/modules/material/<module-id>/
    -> persistent authenticated MaterialBinding

/opt/neebles-build/modules/runtime-leases/
    -> ephemeral independent RuntimeLeases
```

The active MaterialBinding is module-specific installed truth. Schema 2 binds:

```text
module identity
installed module version
CUSTOM V2 revision
Essential selector + manifest
module-delta selector + manifest
domestic-runtime.json + SHA256
construction.json + SHA256
```

The binding does not duplicate the DEB payloads. Those remain in the permanent package pools.

When a controlled module runtime is required, Boss creates a fresh RuntimeLease and composes Essential + module delta into that private lease rootfs. Concurrent executions therefore receive independent runtime territories.

The following old shape is not productive architecture:

```text
/opt/neebles-build/modules/rootfs
shared mutable domestic-runtime.json
```

Uninstall removes module-owned installed state and binding according to the transaction, but it does not erase the permanent certified DEB arsenal.
---

# 8. Preinstall

The module does **not** run Preinstall.

Boss does.

Correct flow:

```text
Boss install/update
    -> immutable module-source selection from Registry
    -> authenticate exact CUSTOM V2 revision
    -> validate Essential membership + integrity
    -> validate module-delta membership + integrity
    -> validate domestic-runtime.json
    -> validate Construction subject against module identity
    -> reuse/download exact certified DEBs into permanent pools
    -> produce MaterialBindingInput
    -> transactionally activate MaterialBinding schema 2
    -> continue Lifecycle
    -> create RuntimeLease only when runtime execution is required
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
    step: open-runtime
```

The module does not declare its own Construction subject in Lifecycle.

Boss injects the Governor-owned module identity into the prepared operation. `boss.workspace_execution` derives the Construction subject from that governed identity and accepts only the module-declared `step`.

This prevents one module from selecting another module's Construction declaration.

This means:

```text
Launcher / command Open
    -> Governor
    -> Lifecycle
    -> generic workspace execution
    -> Governor-owned module identity
    -> MaterialBinding Construction
    -> certified module runtime world
```

Boss contains no Test Module-specific launch branch.

## Feature Lifecycle and Module IPC

The tutorial Features reuse the same generic Lifecycle machinery.

The Notify button resolves:

```text
config.notify
    -> notify-demo
    -> artillery: boss.module_ipc
    -> objective: commands
    -> munition.endpoint: notify
    -> installed Commands contract
    -> test.notify
    -> Module IPC
    -> Boss Notifications
```

The Notify switch is backed by the Lifecycle object `notify-switch`.

```text
initial_active: false
feature-on  -> true
feature-off -> false
```

Its canonical object state is committed only after the governed transition succeeds. Settings must not become a second owner of this functional state.

The module selects the logical Commands endpoint. Boss owns the generic `boss.module_ipc` capability, authenticates the module identity and resolves the installed contract.

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

This is the public module Commands contract.

External callers reach these actions through Boss. Boss resolves the installed declaration, applies contract policy and invokes the registered runtime through Module IPC.

The embedded module UI does not enumerate this public contract and does not self-invoke it.

The UI uses a separate explicit private-intent map owned by the module runtime. Private UI intents may reuse the same internal endpoint implementation, but they do not acquire public Commands authority and cannot automatically inherit future contract capabilities.

The runtime derives its public advertised endpoints from the Commands contract.

Do not maintain a second manually diverging list for public Commands advertisement.

`PRIVATE_UI_ENDPOINTS` is intentionally different: it is a private presentation allowlist owned by the module runtime. It is not a Commands declaration, does not advertise runtime capabilities to Boss and cannot inherit new public Commands automatically.

Privilege policy remains installed-contract truth.

Runtime advertisement is live availability only.

---

# 16. Surfaces

The current reference module uses Surface schema 2 and exposes four presentation items:

```text
open.launcher
    -> Launcher Open button
    -> require self active

open.tray
    -> Tray Open Surface
    -> require self active

config.notify
    -> Config Feature button
    -> require self open

config.notify-switch
    -> Config Feature switch
    -> require self open
    -> Lifecycle object notify-switch
```

`open.launcher` and `open.tray` project the same governed `open` action. The Tray projection does not create another Open implementation or another state authority.

`active` means the installed module is enabled; it does not require a running module IPC session. `open` requires `active` plus an authenticated runtime registered in the Boss RuntimeRegistry. Closing only the Tk window is not itself evidence that the persistent module runtime has stopped. These requirements are evaluated by Boss and never by module UI code.

**1.2.2 staging law:** This module-source revision becomes installable only after the Boss Registry and CUSTOM V2 Construction `fetch`/`checkout` declarations both select its new immutable commit. The standalone Test Module push does not silently retarget existing installations or modify Esbirro's pinned world.


`config.notify` and `config.notify-switch` use `surface: ui`, so Boss presents them under Config -> Features rather than Modules.

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

The UI is intentionally not a Boss client and receives no Boss CLI authority.

Its private communication path is:

```text
UI
    -> stdout JSON request
    -> module runtime
    -> boss.modules.ipc
    -> Boss

Boss / runtime result
    -> module runtime
    -> UI stdin JSON
```

The module runtime is the sole owner of the Boss Module IPC connection.

The UI cannot open that socket directly, cannot execute the Boss CLI and cannot expand its own authority.

This keeps presentation subordinate to the authenticated module runtime.

The UI consumes canonical module settings/state and sends private presentation intents only to its own runtime. When an intent requires Boss-owned services such as Settings or Notifications, the runtime uses its authenticated Module IPC.

The UI must not become the persistence authority.

---

# 18. Settings

Current module-owned Settings examples are:

```text
features.option1
features.option2
```

These Settings keys are distinct from the Boss `Config -> Features` Surface projections `config.notify` and `config.notify-switch`.

The functional state of `notify-switch` belongs to the Lifecycle object `notify-switch`; it must not be duplicated into Settings.

The Settings rule is:

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

The Test Module Tray provider is optional module behavior governed by Boss infrastructure without exposing its private technology to Boss.

The module also publishes `open.tray` as a Tray Open Surface. It is a presentation-only projection of the same governed `open` action already used by `open.launcher`; it is independent from the Tray provider process itself.

Its manifest declares:

```text
tray.provider             tray/tray-provider.py
tray.protocol             1
tray.construction_step    tray-provider
```

Its CUSTOM V2 Construction step declares:

```text
runtime_authority         modules.runtime
world                     modules.python3.13-tk
execution                 persistent
session                   true
session_readonly          neebles/tray.sock
```

Productive birth:

```text
Boss Tray reconciliation
    -> module Tray contract
    -> tray-provider Construction step
    -> modules.runtime
    -> authenticated RuntimeLease
    -> Essential + Test Module delta
    -> desktop-session authority
    -> readonly Tray socket grant
    -> Workspace boundary
    -> persistent provider
    -> kernel SO_PEERCRED registration
```

Boss does not know that this provider currently uses Python/Tk.

Tray consumes canonical settings, reacts to settings changes and publishes visual state. It does not own global module Active/Inactive state.

The Construction supervisor owns a dedicated process group. Runtime stop is fail-closed around PID-incarnation identity.

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

The tutorial `config.notify` button and `config.notify-switch` both reach the existing `notify` Commands endpoint through Lifecycle and `boss.module_ipc`. The runtime then emits the normal Module IPC notification request and waits for the Boss notification acknowledgement.

This deliberately exercises the universal path:

```text
Surface
    -> Lifecycle
    -> boss.module_ipc
    -> module runtime
    -> Module IPC notification
    -> Boss policy/validation
    -> desktop notification
```

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

# 26. Current verification status

Current local source diagnostics verify the reference shape for:

```text
Schema 4
Construction declaration
Essential layer                          59 DEBs
Test Module delta                        32 DEBs
MaterialBinding schema 2
Construction payload bound by SHA
RuntimeLease
runtime world modules.python3.13-tk
module material integrity manifest
Governor-owned module identity
governor.open
construction.step open-runtime
Lifecycle munition contains step only
tray.construction_step tray-provider
boss.modules.ipc
dynamic installed-runtime readonly projection
runtime --intent open
private UI intents <-> Runtime channel
private UI allowlist is independent from public Commands declaration
public Commands remain Boss-governed
UI has no Boss CLI dependency
UI does not own Boss Module IPC
Surface schema 2
module-scoped Surface translations
Config -> Features projection
require self active
require self open
strict RuntimeRegistry-backed open resolution
persistent surface-model projection
persistent surface-action execution
boss.module_ipc Lifecycle capability
config.notify -> notify-demo -> commands.notify
config.notify-switch -> notify-switch object
feature-on / feature-off canonical Lifecycle state
object state committed only after successful governed transition
open.tray presentation projection
```

These are source/local diagnostic results, not final system certification.

Fresh Live must still prove install, Launcher Open, Tray Open Surface, governed Tray provider birth, private UI intents, public Commands through Boss, Config -> Features visibility, active/open requirement gating, Notify button delivery, Notify switch transitions with canonical Lifecycle state, settings behavior, disable/enable, runtime close/reopen gating, uninstall and reinstall with this single Test Module.

The complete battery must then be repeated after installing N.E.E.B.L.E.S. OS through Calamares.

Only after that single-module cycle is GREEN will a second repository with a different module identity be created from this same reference implementation to certify simultaneous multi-module isolation.

The Test Module is a reference consumer/template. Python/Tk is implementation detail, not Boss architecture.

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
