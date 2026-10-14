# N.E.E.B.L.E.S. Test Module

**Official reference implementation and developer tutorial**
**Current source / local installation:** `1.2.8` (Uninstall candidate, not published through the coordinated Registry/CUSTOM release) · **Module manifest:** schema `4` · **Uninstall:** schema `1` · **Surfaces:** schema `2` · **Commands:** schema `1`
**Last published integration baseline:** Test Module `1.2.7` with Boss `1.0.51` · **Reference platform:** NEEBLES OS (Debian Trixie, KDE Plasma)

> **Boss governs HOW. CUSTOM V2 certifies WHAT. The operating system supplies platform authority. The module declares WHAT IT DOES and implements its own behavior.**

This repository is a *working reference consumer*, not a mandatory runtime dependency and not the definition of the Boss architecture. A new NEEBLES module can be implemented in Rust, Python, Go, Node.js, C++, Java or another technology **without teaching Boss about that technology or hard-coding the module's name**.

The purpose of this README is to take a developer from an empty module repository to a governed, installed, updated, tested module. It distinguishes a real **contract** from Test Module's **Python/Tk example**, a **published source** from a **running installation**, and verified behavior from work that still requires tests.

## Contents

1. [Version, exact integration snapshot and verification](#1-version-exact-integration-snapshot-and-verification)
2. [Architecture, owners and boundaries](#2-architecture-owners-and-boundaries)
3. [Real project layout](#3-real-project-layout)
4. [Create the module identity and manifest](#4-create-the-module-identity-and-manifest)
5. [Declare Commands and implement the runtime](#5-declare-commands-and-implement-the-runtime)
6. [Define Lifecycle and governed Open/Close](#6-define-lifecycle-and-governed-openclose)
7. [Declare Surfaces and synchronize Open](#7-declare-surfaces-and-synchronize-open)
8. [Settings, language and notifications](#8-settings-language-and-notifications)
9. [Prepare CUSTOM V2 material and Multi-RootFS](#9-prepare-custom-v2-material-and-multi-rootfs)
10. [Define domestic Construction](#10-define-domestic-construction)
11. [Tray, session controller and Linux startup](#11-tray-session-controller-and-linux-startup)
12. [Source publishing, CUSTOM alignment and Boss Registry](#12-source-publishing-custom-alignment-and-boss-registry)
13. [Install, update, Critical Update and release notes](#13-install-update-critical-update-and-release-notes)
14. [Validation and acceptance matrix](#14-validation-and-acceptance-matrix)
15. [Troubleshooting learned from the real installation](#15-troubleshooting-learned-from-the-real-installation)
16. [Template checklist for a new module](#16-template-checklist-for-a-new-module)
17. [Non-goals, security invariants and future evolution](#17-non-goals-security-invariants-and-future-evolution)
18. [Historical compatibility and release chronology](#18-historical-compatibility-and-release-chronology)
19. [1.2.8 Uninstall development candidate and pending certification](#19-128-uninstall-development-candidate-and-pending-certification)

---

## 1. Version, exact integration snapshot and verification

This table is the **historical, successfully published 1.2.7 integration snapshot**, not the current 1.2.8 worktree. The SHAs identify code/material selected by the coordinated October 2026 publication; a newer `main` commit or installed manifest does not retroactively change those pins:

| Authority | Revision / identity | Meaning |
|---|---|---|
| Published module baseline | `1.2.7` | Version of the historical, coordinated release (the current repository manifest is `1.2.8`) |
| Module source | `5db32c4fdec61564415839851c18c092896e11bc` | Published functional reference revision; immutable source selection |
| CUSTOM V2 | `3416f29e57785a520aef93e456daf71440f06e7e` | Published module material and Construction alignment |
| Boss Registry | `4c729c4d72ee7dbdf8c25a1501826f557d8678e0` | Published `registry/modules.json` selecting module `1.2.7` |
| Boss release | `v1.0.51` | General-purpose Governor, UI, Launcher and update host |
| Boss release build source | `ebe8f0242c0c826803bbf22711534eb101058d4b` | Exact commit compiled for Boss 1.0.51; not a module source SHA |
| Runtime world | `modules.python3.13-tk` | Example Python/Tk world supplied by CUSTOM V2 |
| Material | `59` Essential DEBs + `32` module-delta DEBs | Certified **example** package set for the referenced amd64 material |
| Module material manifest | `2,242` entries | Effective filesystem integrity inventory for this example RootFS |

**These are distinct identities.** The Boss Registry pins a **module source commit**, while Boss Preinstall independently resolves and records an exact **CUSTOM V2 material revision**. A README-only commit does not secretly replace the module source selected by the installed Registry. A future functional module release must deliberately advance all relevant references.

### Current 1.2.8 candidate — audited 2026-10-13

| Item | Observed state / source |
|---|---|
| Test Module source | `3835ca4ffbac847e28f8b9e105da7d7747c07c94`, `main` aligned with `origin/main`, no local changes in the audit |
| Repository manifest | `test-module` version `1.2.8`, schema `4`, `uninstall` schema `1` |
| Installed NEEBLES OS module | `/opt/neebles/modules/test-module/manifest.json` version `1.2.8`; bytes matched repository manifest (SHA-256 `c9c4e88b1290830bdc9a6831b737f0bd835f605af46bf11edd51b2927655238b`) |
| Python source tests | `14/14` passed in the local audit; they validate contracts and source behavior, not a physical Uninstall |
| Host resources observed | Opt-in `systemd-user` session controller active, Tray runtime/Bubblewrap and local controller socket present before Uninstall |
| Boss TXN V5 development source | `66f0f7af33c4f320bb1bd1122d46937376ab8ab1` on `feat/txnv5-lifecycle-arsenal-bridge`; adds module-owned XDG Autostart retirement alongside the user service adapter |
| Publication/certification | 1.2.8 is **not yet a coordinated, certified module release**. A live end-to-end Uninstall, recovery and both Settings choices remain pending. |

The installed 1.2.8 copy in this audit proves local source selection, **not** that the Boss TXN V5 development branch is the currently running Boss binary. Do not conflate GitHub source, installed module, compiled Boss or Registry publication. The 1.2.7 table below remains useful, unchanged history.

### What was actually observed

- Test Module `1.2.7` was published; its nine existing Python unit tests passed prior to publication.
- CUSTOM V2 `fetch` and `checkout` were published with the same immutable module SHA; the two material manifests changed version metadata while retaining the 2,242 entries and their hashes.
- Boss `1.0.51` was built successfully in GitHub Actions, verified with release checksums, published with eleven assets, updated on an installed NEEBLES OS system and reported working correctly after final startup repair.
- On that installed system, Governor reported `runtime_state=closed`, `open_available=true`, `enabled=true` when the module was closed. The originally installed Tray controller was discovered running an obsolete *home-directory* copy, which did not return the `open_available` field expected by the 1.2.7 popup. The service was migrated to the installed module code.
- KDE Plasma session restoration was found separately launching `neebles-ui` directly, outside Boss's authenticated startup context. The user subsequently reported that the startup repair was successful. **Do not attribute this independent desktop-session issue to the module's Construction or rewrite Boss to hide it.**
- The user reported that the integrated procedure now works. This is **installed-system acceptance of the exercised workflow**, not evidence that every VM, Fresh Live, multi-module concurrency, uninstall/reinstall and rollback case has been exercised.

Run the acceptance matrix in §14 for any *new* module, architecture, host, runtime world or clean-image release. A successful source test or published SHA is not automatically a successful GUI test.

---

## 2. Architecture, owners and boundaries

```text
Module repository (THIS repo)
    manifest / Lifecycle / Commands / Surfaces
    runtime code, UI, language strings, defaults
    optional module-owned Tray client / helper
    module release notes
               |
               | immutable source commit
               v
Boss Registry (in neebles-boss)
    remote module identity, version, repository, commit
               |
               v
Boss (generic authority)
    validation, authorization, Preinstall, transactions
    MaterialBinding, RuntimeLease, rollback
    Governor, RuntimeRegistry, Module IPC
    Settings, Events, Notifications, Surface projection
               |
               | authenticated material revision
               v
CUSTOM V2 (in neebles-custom)
    Essential + module-delta package membership
    package and filesystem integrity
    named RootFS and runtime worlds
    canonical domestic Construction recipe
               |
               v
OS platform authorities (NEEBLES OS)
    desktop session, system services, sockets, UID/GID
    permitted runtime boundaries and providers
```

**Separations that must never be collapsed:**

| Owner | Does | Does not |
|---|---|---|
| Module | Declares its contracts; handles its own application, private UI intents and cooperative Close | Install arbitrary host packages; forge a Governor state; decide how Boss runs sandboxed worlds |
| CUSTOM V2 | Certifies package and RootFS material, world and Construction | Implement GUI business logic or Governor policy |
| Boss | Authenticates/validates declarations, owns installed state, runs governed operations, issues RuntimeLease | Hard-code `test-module`, Python/Tk, a future module language or a private module feature |
| OS | Provides desktop, systemd, IPC and security primitives | Rewrite module identity or functional contracts |
| BUILD | Composes the OS image and recovery environment | Replace CUSTOM V2 as the module material authority |

**CUSTOM classic is not CUSTOM V2.** The same repository contains classic Boss/Calamares material and separate V2 module material. This tutorial uses the V2 paths only; never modify classic Boss or Calamares rootfs to repair a module presentation bug.

Every dependency, filesystem path and capability in a module is an explicit request that Boss must be able to validate. Never treat the entire host filesystem, user HOME or inherited process environment as an implicit entitlement.

---

## 3. Real project layout

```text
neebles-test-module/
├── README.md                         # this tutorial
├── manifest.json                     # identity and declarations (schema 4)
├── lifecycle.json                    # Governor / object state transitions
├── surfaces.json                     # optional Launcher / Tray / Boss Config items
├── runtime.py                        # example runtime, Module IPC and UI child
├── icon.jpeg
├── contracts/
│   └── commands.json                 # public Commands schema 1
├── languages/
│   ├── manifest.json
│   ├── en_US.json
│   └── es_CL.json
├── settings/
│   └── default.json
├── material/
│   ├── python3.13-tk.packages.tsv     # module-side reference copy
│   └── python3.13-tk.manifest.json
├── ui/
│   └── test-module-ui.py              # private Tk UI, not a Boss admin client
├── tray/
│   ├── tray-provider.py               # isolated Tray provider + popup
│   ├── session-controller.py          # optional host-user helper
│   └── install-session-controller.py  # explicit opt-in systemd user installer
├── critical-update/
│   ├── manifest.json                  # [] is valid
│   └── release-notes/
│       ├── es_cl_1_2_3.txt ... es_cl_1_2_8.txt
│       └── en_us_1_2_3.txt ... en_us_1_2_8.txt
└── tests/
    ├── test_cast30_runtime_close.py
    ├── test_governor_open_127.py
    └── test_uninstall_contract_128.py
```

The complete **canonical material** lives in a different repository, CUSTOM V2, chiefly:

```text
neebles-custom/
└── runtime/
    ├── construction/test-module.json
    ├── modules/domestic-runtime.json
    └── manifests/modules/
        ├── essentials.packages.tsv
        ├── test-module.packages.tsv
        ├── test-module.manifest.json
        └── rootfs/test-module/
            ├── python3.13-tk.packages.tsv
            └── python3.13-tk.manifest.json
```

An example module does not need every optional file. A CLI-only Rust module might need no Tray, no UI translations and no graphical desktop-session request. **Omit undeclared features rather than inserting empty fake integrations.**

---

## 4. Create the module identity and manifest

The identity is a stable machine-readable module ID. This reference uses `test-module`; a future module must consistently replace it in its own paths, contracts and CUSTOM recipes. A display name, repository name or programming language is not an alternative machine identity.

**Current productive declaration (`manifest.json`, 1.2.8 candidate):**

```json
{
  "schema": 4,
  "name": "test-module",
  "version": "1.2.8",
  "entrypoint": "runtime.py",
  "lifecycle": "lifecycle.json",
  "surfaces": "surfaces.json",
  "contracts": [
    {
      "type": "commands",
      "file": "contracts/commands.json",
      "schema": 1,
      "enabled": true
    }
  ],
  "tray": {
    "icon": "icon.jpeg",
    "provider": "tray/tray-provider.py",
    "protocol": 1,
    "construction_step": "tray-provider"
  },
  "notifications": {
    "protocol": 4
  },
  "settings": "settings/default.json",
  "uninstall": {
    "schema": 1,
    "hardcoded": {
      "session_service": "neebles-test-module-session-controller.service",
      "cache_directory": "cache"
    },
    "main": "governor",
    "extras": [
      {
        "id": "session-controller",
        "type": "service",
        "provider": "systemd-user",
        "name": "$hardcoded.session_service",
        "exec_start": "/usr/bin/python3.13 /opt/neebles/modules/test-module/tray/session-controller.py",
        "required": false,
        "stop": {
          "disable": true,
          "timeout_ms": 5000
        },
        "verify": "inactive",
        "remove": true
      },
      {
        "id": "tray",
        "type": "governed",
        "ref": "manifest.tray",
        "required": false,
        "verify": "terminated"
      }
    ],
    "cleanup": [
      {
        "id": "module-cache",
        "type": "directory",
        "scope": "module-data",
        "path": "$hardcoded.cache_directory",
        "policy": "always"
      },
      {
        "id": "local-settings",
        "type": "settings",
        "ref": "manifest.settings",
        "policy": "user-choice"
      }
    ],
    "failure": {
      "unknown_process_owner": "abort",
      "resource_still_running": "abort",
      "cleanup_error": "abort"
    }
  }
}
```

The `contracts` array advertises contract types. Boss validates installed declarations; it does **not** reverse-engineer Python methods or invent unspecified capabilities. The historical top-level `manifest.commands` shape is **obsolete** for this reference. Public Commands belong inside the declared `contracts` array. The 1.2.8 `uninstall` schema is documented in §19; its declared extras and cleanup are not auto-installed merely because they appear in a manifest.

`tray.construction_step` must name an actual step in the certified CUSTOM Construction recipe. If a module has no Tray, do not declare a provider or reserve a fictitious construction step.

A version change is intentional and coordinated; changing the string in a working tree does not update an installed module by itself.

---

## 5. Declare Commands and implement the runtime

### Public Commands contract

`contracts/commands.json` contains schema `1`, `contract: "commands"`, `endpoints` and `metadata`. This reference exposes the public actions `open`, `version`, `hello`, `notify`, `state`, `settings`, `setting`, `toggle`, `events` and `external`.

A simplified member looks like this:

```json
{
  "schema": 1,
  "contract": "commands",
  "endpoints": {
    "version": {
      "endpoint": "test.version",
      "lifecycle": "runtime",
      "state_mode": "preserve",
      "requires_root": false,
      "launcher": false
    }
  },
  "metadata": {}
}
```

That JSON is an *illustration of the schema*, not the complete real contract: use the repository's `contracts/commands.json` for the exact productive endpoint set and policies. A declared public action is **not** an arbitrary permission to run executable code. Boss resolves the installed contract and authorizes/dispatches an invocation to the authenticated module runtime.

### Runtime registration, not a private replacement for Boss

`runtime.py` uses the authenticated module IPC socket (`/run/neebles/modules.sock` under the narrow `boss.modules.ipc` authority). Its current example protocol is `1`. It follows:

```text
Construction creates governed runtime process
    -> connect to Module IPC
    -> register { module, session_id, protocol, endpoints }
    -> validate Boss 'registered' identity and protocol
    -> subscribe to approved events
    -> handle invoke, settings events, notifications, control and shutdown
    -> explicit unregister / socket close when the owned Open session ends
```

The current Python sample frames Module IPC JSON with a **4-byte big-endian length prefix**, bounds frames, validates session identity and rejects unexpected messages. Do not confuse this channel with the line-delimited Tray Manager and private session-controller sockets; they are **different protocols and privilege boundaries**.

`declared_endpoints()` builds its advertised public runtime endpoints from the installed Commands contract. **Do not maintain an independent hard-coded public endpoint list.** The runtime may maintain a separate `PRIVATE_UI_ENDPOINTS` allowlist for its private UI presentation intents, but that map is not public contract truth.

### Private module UI flow

```text
Tk UI (child process)
    -> JSON request on child's stdout
    -> runtime.py private-intent allowlist
    -> internal endpoint handler
    -> authenticated Module IPC request if Boss authority is required
    <- Boss result / Settings / Notifications
    <- JSON response to child stdin
```

The UI must **not** gain access to Boss's administrative socket simply because it happens to share a Python implementation with the runtime. Private UI requests and public installed Commands are intentionally separate.

### Application lifetime is not an implicit Governor lifetime

The runtime is responsible for exiting/unregistering when its declared *Open session* ends. A future headless module can implement a different lifetime, but it must do so deliberately. No client may infer `closed` from a window title, process name or GUI toolkit heuristic.

---

## 6. Define Lifecycle and governed Open/Close

`lifecycle.json` declares the bindings between Boss actions and module operations. Reference Governor aliases include `governor.install`, `.update`, `.uninstall`, `.enable`, `.disable`, `.open` and `.notify-demo`.

### Real Open path

```text
Boss UI / Launcher / declared Tray Open / CLI
    -> Governor Open (single authority)
    -> module Lifecycle transition 'open'
    -> boss.workspace_execution / construction.step
    -> step 'open-runtime'
    -> certified RootFS / runtime world / RuntimeLease
    -> Module IPC registration
    -> module UI appears
```

The key part of the productive `lifecycle.json` is:

```json
{
  "hardcoded": { "governor.open": "open" },
  "transitions": {
    "open": {
      "operations": {
        "launch-runtime": {
          "artillery": "boss.workspace_execution",
          "objective": "construction.step",
          "munition": { "step": "open-runtime" },
          "tactics": {},
          "intelligence": {}
        }
      }
    }
  }
}
```

This fragment intentionally omits other declarations. Do not replace the real `lifecycle.json` with it. Boss already knows the governed module identity; the Lifecycle munition names **only** the declared step. The module does not get to select another module's Construction subject.

### Matching Close is mandatory

For this graphical example, the child Tk window **is** the lifetime of the `Open` session:

```text
Governor: closed -> opening -> open
    -> UI child closes via X
    -> runtime.py detects UI child exit
    -> authenticated unregister for the same module/session
    -> close Module IPC connection
    -> Boss RuntimeRegistry releases that session
    -> Boss emits lifecycle/runtime_dead evidence
    -> Governor: closed (if the module remains Active, Open can be available)
```

If an IPC connection dies unexpectedly, Boss's runtime registry must be able to release the lost authenticated session; the module must not fabricate successful cleanup. **The optional Tray provider is independent of the foreground Open runtime**: closing the application must not kill the Tray or erase persisted Settings.

### Object-based Lifecycle, not Settings pretending to be state

The reference `notify-switch` declares `initial_active: false`, `feature-on: true` and `feature-off: false`. Each transition routes to the `notify` Commands endpoint through generic `boss.module_ipc`; the canonical object state changes only after a successful governed transition. A Settings leaf is not a substitute for functional Lifecycle state.

Empty install/update/uninstall/enable/disable operations are legitimate when the module has no extra work for those transitions. **Never add ceremonial commands or private apt installs.**

---

## 7. Declare Surfaces and synchronize Open

`surfaces.json` uses schema `2` and declares four reference items:

| Item | Surface | Requires | Action |
|---|---|---|---|
| `open.launcher` | `launcher` | `self: active` | `open` |
| `open.tray` | `tray` | `self: active` | `open` |
| `config.notify` | `ui` (Boss Config/Features) | `self: open` | `notify-demo` |
| `config.notify-switch` | `ui` (Boss Config/Features) | `self: open` | `feature-on` / `feature-off` on `notify-switch` |

The Governor's own **Boss UI Modules/Open** action remains available as an administrative control when allowed. Optional Launcher and Tray controls only exist when declared. The above `open.tray` is a governed Surface in the NEEBLES Tray; the **module-owned Tk popup** also contains an optional Open button implemented through the 1.2.7 session-controller protocol. These are related UI locations but not the same IPC API.

A simplified declared Open Surface:

```json
{
  "open.launcher": {
    "surface": "launcher",
    "visible": true,
    "data": {
      "control": "button",
      "action": "open",
      "label_key": "surface.open"
    },
    "require": { "self": "active", "modules": {} }
  }
}
```

**Never replace Governor with a local `isRunning` boolean.** On the canonical `neebles boss surface-model` entry, inspect **both** `runtime_state` and `open_available`:

| Governor output | Open enabled? | Meaning |
|---|---|---|
| `closed`, `open_available: true` | Yes | Closed, Active, declared Governor action allowed |
| `closed`, `open_available: false` | No | Closed alone is insufficient: may be Inactive or otherwise unavailable |
| `opening`, `open_available: false` | No | Open in progress, block duplicates |
| `open`, `open_available: false` | No | One registered Open session exists |
| invalid / stale / unavailable response | No (fail closed) | Don't guess and don't bypass Governor |

All declared surfaces must converge on one RuntimeRegistry session. Requery authoritative state after transitions, upon reopening a hidden popup and after a failed/delayed request. A button becoming visually enabled is not sufficient evidence that multiple Open requests are safe: Governor still owns single-flight protection.

Manual read-only inspection of the installed system:

```bash
neebles boss surface-model | python3 -c '
import json,sys
for item in json.load(sys.stdin):
    if item.get("name") == "test-module":
        print({k: item.get(k) for k in ("enabled", "runtime_state", "open_available")})
'
```

**Accepted interaction:** start from any available Open control, observe every other declared control disabled during `opening/open`, close the GUI with **X**, then observe every control re-enabled when Governor returns `closed/true`. Repeat with the module disabled, with Tray popup hidden/reopened, and with repeated rapid clicks.

---

## 8. Settings, language and notifications

### Module-owned Settings

The reference defaults in `settings/default.json` are **string** values:

```json
{
  "hardcoded": { "module": "test-module" },
  "ui": {},
  "features": {
    "option1": "false",
    "option2": "false"
  },
  "tray": {
    "visible": "false",
    "autostart": "false",
    "session_boot_id": ""
  }
}
```

Settings are persisted by Boss for the installed module. The runtime performs authenticated Settings requests; a Tray provider uses the granted Tray settings protocol. Do not write arbitrary configuration into a globally shared file or use HOME as a hidden persistence authority.

- `features.option1` and `features.option2` are demonstration Settings leaves.
- `tray.visible` governs the optional StatusNotifier icon's visibility.
- `tray.autostart` means the module wants its Tray reconciled on subsequent Linux logins; it does **not** authorize the module to install a user service automatically.
- `tray.session_boot_id` disambiguates the first Tray reconciliation after a boot.
- Hiding Tray also turns off its autostart preference; a hidden Tray must not silently remain configured to start itself.

Settings and visibility do **not** mean Active, Inactive, `opening` or `open`. The Tray provider is not the foreground Open runtime.

### Languages

The module's `languages/manifest.json` selects `es_CL` by default and declares `en_US` as an alternative. Module-facing keys live in `languages/es_CL.json` and `en_US.json`. `NEEBLES_LANGUAGE` in the authenticated environment selects the current module locale; the module resolves its own localized strings, with fallback to its declared default.

**Do not conflate module translations with Boss UI translations.** Boss's own `app.title`, `config.tray`, etc. come from `/opt/neebles/client/languages/`, through the authorized Boss UI backend. Missing UI authority can expose raw keys even when the JSON language files are correct; see §15.

### Notifications

The manifest declares Notifications protocol `4`. Normal notification delivery is:

```text
Boss Config Surface -> Lifecycle
  -> boss.module_ipc (Commands/notify)
  -> authenticated runtime request
  -> Boss Notifications policy and presenter
  -> desktop notification
  -> authenticated responses/closure events
```

The runtime supports `notification_closed` callbacks, validates the session/module and does not accept foreign notification ownership. Do not replace this with an ungoverned desktop notification subprocess inside the module.

---

## 9. Prepare CUSTOM V2 material and Multi-RootFS

A module does not bootstrap its own apt environment as a shortcut. **CUSTOM V2 is the material authority** for package membership, integrity, the RootFS and runtime world. The current amd64 Test Module example was built with `59` Essential DEBs and `32` module-delta DEBs.

### Package membership vs integrity

- Essential membership: `runtime/manifests/modules/essentials.packages.tsv`.
- Module delta membership: `runtime/manifests/modules/test-module.packages.tsv`.
- Named RootFS membership: `runtime/manifests/modules/rootfs/test-module/python3.13-tk.packages.tsv`.
- Module integrity: `runtime/manifests/modules/test-module.manifest.json`.
- Named RootFS integrity: `runtime/manifests/modules/rootfs/test-module/python3.13-tk.manifest.json`.

Membership TSV columns are `package`, `version`, `arch`, `filename`, `sha256` (tab separated). The integrity manifest checks effective filesystem entries, including type, mode, size, SHA-256 or symlink target where appropriate. Those two contracts answer **different questions** and must agree. Never rebuild them by blindly hashing an already modified host rootfs.

The reference's two module integrity manifests have **2,242 entries** each, with the same certified material; the per-RootFS one additionally identifies `python3.13-tk`. Version metadata follows the selected module version. The 1.2.6 → 1.2.7 source-only update did **not** require changing DEBs or recomposing the same certified world.

### Runtime world declaration

The canonical material world's declaration is in CUSTOM V2:

```text
runtime/modules/domestic-runtime.json
  worlds.modules.python3.13-tk
    executable: usr/bin/python3.13
    library_paths: usr/lib/x86_64-linux-gnu
    runtime_paths:
      usr/lib/python3.13
      usr/lib/tcltk
      usr/share/tcltk
```

This is a **Python/Tk example**, not a NEEBLES module ABI mandate. For a different technology, certify that module's real executable and dependency closure, and declare its own world rather than teaching Boss which interpreter it uses.

### Multi-RootFS and RuntimeLease

The active contract is **named Multi-RootFS**, introduced after legacy MaterialBinding schema 2. A Construction recipe declares a `rootfs` map, and each runtime step selects a matching `rootfs` and `world`. Boss produces persistent authenticated material bindings and creates isolated, ephemeral RuntimeLeases for controlled execution.

Known Boss-owned territories documented for this integration include:

```text
/opt/neebles-build/modules/packages/essentials/   # permanent Essential pool
/opt/neebles-build/modules/packages/              # permanent module delta pool
/opt/neebles-build/modules/material/<module-id>/  # authenticated material binding
/opt/neebles-build/modules/runtime-leases/         # ephemeral runtime composition
/opt/neebles/modules/<module-id>/                 # installed module source/material
```

Do not copy the obsolete global `/opt/neebles-build/modules/rootfs` model or interpret a legacy shared mutable `domestic-runtime.json` as the active contract. Uninstalling one module does not erase a shared certified package pool. RuntimeLeases are separate from that permanent pool and from other modules.

### What Preinstall actually does

```text
Boss Install / Update
  -> read Registry's immutable module-source selector
  -> resolve and authenticate an exact CUSTOM V2 source revision
  -> verify Essential and module delta membership + integrity
  -> validate selected RootFS, world and Construction subject/steps
  -> reuse/fetch exact certified DEBs into permanent pools
  -> prepare versioned MaterialBinding / named RootFS inventory
  -> stage and transactionally activate the module
  -> create RuntimeLease only for the runtime that is requested
```

The installed binding records the **exact CUSTOM revision it consumed**. CUSTOM's current branch revision and the module's selected source SHA are different authorities; neither is a mutable substitute for the other.

---

## 10. Define domestic Construction

In CUSTOM V2, `runtime/construction/test-module.json` declares:

```json
{
  "schema": "1",
  "name": "neebles-domestic-construction",
  "subject": "test-module",
  "rootfs": {
    "python3.13-tk": {
      "domination": { "world": "modules.python3.13-tk" }
    }
  }
}
```

This excerpt omits `steps`, which are required in the productive file. The reference has **five** steps, not the obsolete four-step example:

| Step ID | Runtime authority | World / RootFS | Mode | Purpose |
|---|---|---|---|---|
| `init` | `boss.runtime` | `boss.git` | foreground | Initialize controlled domestic source workspace |
| `fetch` | `boss.runtime` | `boss.git` | foreground | Fetch exact immutable module SHA |
| `checkout` | `boss.runtime` | `boss.git` | foreground | Detach checkout at the exact SHA |
| `open-runtime` | `modules.runtime` | `modules.python3.13-tk` / `python3.13-tk` | persistent, session | Start the authenticated module foreground runtime |
| `tray-provider` | `modules.runtime` | `modules.python3.13-tk` / `python3.13-tk` | persistent, session | Start the separate optional Tray provider |

**Source steps** use the `boss.git` world and a controlled writable workspace, not arbitrary host Git authority. Both `fetch` and `checkout` must select the same published SHA. A floating `main`, a local worktree or a guessed revision is not acceptable for the installed source.

**Open runtime step** includes:

```text
id: open-runtime
runtime_authority: modules.runtime
rootfs: python3.13-tk
world: modules.python3.13-tk
execution: persistent
session: true
readonly: boss.modules.ipc
dynamic_readonly: modules.installed_runtime
chdir: /opt/neebles/modules/test-module
arguments: /opt/neebles/modules/test-module/runtime.py --intent open
```

**Tray provider step** is a *separate* `modules.runtime` execution, with the same declared RootFS/world but its own session and socket grants:

```text
id: tray-provider
runtime_authority: modules.runtime
rootfs: python3.13-tk
world: modules.python3.13-tk
execution: persistent
session: true
dynamic_readonly: modules.installed_runtime
session_readonly:
  - neebles/tray.sock
  - neebles/test-module-controller.sock
arguments: /opt/neebles/modules/test-module/tray/tray-provider.py
```

The `session_readonly` entry is a narrowly granted Unix socket in the authenticated desktop session, **not the entire host `/run`**. Read the productive JSON for exact mounts, `chdir`, arguments and authority mappings; these compact illustrations are not a substitute for it.

A new module may define one or several RootFS worlds. Validate the names and per-step selections; do not silently reuse the wrong RootFS just because two source steps happen to be Python.

---

## 11. Tray, session controller and Linux startup

### Two separate Tray concepts

1. **NEEBLES Tray's declared `open.tray` Surface**: a Boss-projected module action that uses the normal Governor semantics.
2. **Test Module's optional Tray provider/popup** (`tray/tray-provider.py`): a separate module runtime that displays settings and an `Open Test Module` button.

The second is *not* automatically granted an administrative Boss socket. Instead, in `1.2.6+`, the popup uses a narrow **module-owned user-session controller** over:

```text
/run/user/<desktop-uid>/neebles/test-module-controller.sock
```

The controller accepts only the actions `status` and `open` for the fixed installed module. The socket is user-owned, permission `0600`, and the controller checks the Unix peer's UID. `open` eventually calls the same governed `neebles modules action test-module open` path; it is **not** a second module launcher.

### 1.2.7's canonical status contract

The controller reads **`neebles boss surface-model`**, not the older `modules runtime status` response. `status` returns fields including:

```json
{
  "ok": true,
  "opened": false,
  "runtime_state": "closed",
  "open_available": true
}
```

The popup begins with Open disabled until a fresh successful status response. It polls while visible, closes/fails safe on an error, and must recover Disabled → Enabled after GUI Close when `closed/true` is restored. An `open` response and a `status` response are not interchangeable: clients must read the fields declared for each action.

### Opt-in systemd user controller — installed 1.2.7 or newer

The helper is *optional* and requires an explicit action by the desktop user. It is **not** installed automatically by Boss or by the module's `install` Lifecycle. For this reference, the command is:

```bash
python3 /opt/neebles/modules/test-module/tray/install-session-controller.py
```

Run this as the **logged-in desktop user, without `sudo`**. It installs/refreshes:

```text
~/.config/systemd/user/neebles-test-module-session-controller.service
```

The service starts the installed module's source directly:

```text
ExecStart=/usr/bin/python3.13 /opt/neebles/modules/test-module/tray/session-controller.py
```

It is a `Type=notify` user service, announces readiness after its socket exists, uses `NoNewPrivileges=true`, `PrivateTmp=true`, `Restart=on-failure`, and is ordered with the Tray Manager session behavior. It does **not** install a root system service, a host package or a copy of Python/Tk packages.

Verify the effective systemd command, not merely that the unit says `active`:

```bash
systemctl --user show neebles-test-module-session-controller.service \
  -p ActiveState -p SubState -p ExecStart --no-pager
```

**Mandatory one-time migration from 1.2.6:** version 1.2.6's installer copied a snapshot to:

```text
~/.local/share/neebles/test-module/session-controller.py
```

That stale snapshot could return only `{'ok': True, 'opened': False}` — without `open_available`. A 1.2.7 popup then remained Disabled despite Governor reporting `closed/true`. Installing module 1.2.7 **does not rewrite an existing user unit**. After the module update, run the 1.2.7 installer above once to point the user service at the installed module's actual `session-controller.py`; then recheck status and restart the session as required. Do not try to repair this by changing Governor or editing a sandbox bind mount. This was the historical 1.2.7 diagnosis; the later 1.2.8 candidate introduces a distinct Uninstall contract and does not retroactively change the diagnosis.

**Removal policy depends on the installed Boss version.** For the 1.2.7/Boss 1.0.51 historical workflow, users could explicitly remove the opt-in helper with:

```bash
python3 /opt/neebles/modules/test-module/tray/install-session-controller.py --remove
```

For the **1.2.8 Uninstall candidate with a compatible TXN V5 Boss**, the module declares this `systemd-user` unit as module-owned, with `stop.disable=true`, `remove=true` and `verify=inactive`. Boss is intended to stop, disable, verify and retire the declared unit as part of its governed Uninstall; the user should **not** be instructed to run a separate helper-removal command after a successful certified transaction. This path has not yet passed the installed-system Uninstall acceptance matrix (§14 and §19). The opt-in installation of the helper remains a distinct explicit action; the Uninstall declaration does not silently install it.

A future production module should decide explicitly whether a host-user helper is necessary. It is **not** part of the minimum NEEBLES module ABI.

### Correct KDE startup authority (important separate lesson)

A graphical Boss UI must be launched by the authenticated Boss startup path (`neebles start` / the installed `neebles-boss-ui-autostart.service` as configured), rather than KDE Session Restore running `/opt/neebles/client/ui/neebles-ui` **directly**. A directly restored process can omit `NEEBLES_AUTHORITY_SUPPLY`, causing its C++ controller's Boss CLI subprocesses to fail; the UI then shows raw i18n keys (`app.title`, `config.tray`, etc.) and may show an empty Modules list even when `neebles i18n dump` and `neebles boss surface-model` succeed in a proper context.

This was an **independent KDE KSMServer startup-path conflict** observed during module integration, not proof that Test Module's helper modified Boss language files. The working repair was reported by the user. Future setups should avoid duplicate starts, check Plasma Session Restore, and keep a **single canonical Boss startup owner**. See §15 for safe, read-only diagnostics before changing KDE session preferences. Avoid force-killing the whole desktop, deleting `ksmserverrc` or bypassing AuthoritySupply validation.

---

## 12. Source publishing, CUSTOM alignment and Boss Registry

These are the mandatory **ordering and integrity** rules for a new version. They do not require a new Boss release merely because a module's Python, Rust or Qt code changed.

### Release progression (one functional module version)

1. Change module code/contracts and bump `manifest.json` version. Add tests and localized release notes.
2. Validate JSON, static syntax, contract identity, runtime behavior and README against the **actual changed files**. Do not call a source/unit test a Live test.
3. Commit and push the complete module source. Record its **full 40-character commit SHA**.
4. In CUSTOM V2, update `runtime/construction/<module-id>.json` so both `fetch` and `checkout` select that SHA; update associated material manifest version metadata. Change package hashes **only if the actual certified material changed**.
5. Validate parsed Construction, matching names/world/RootFS, package counts and manifest hashes. Commit and push CUSTOM V2, recording its distinct full revision SHA.
6. In **Boss's** `registry/modules.json`, update the declared module `version` and `commit` to the published module SHA. The Registry does **not** contain or require a fake separate module named Registry. This is only the catalog file in the Boss repository.
7. Commit and push the Registry change. Boss fetches the current branch's exact revision and reads the module selection from that immutable snapshot; Boss Preinstall separately resolves the applicable CUSTOM V2 revision and records it in the installed material binding.
8. Perform the installed-system update, migration (if needed), reboot/session startup checks and test matrix. Only mark each acceptance criterion passed when observed on the relevant system.

### Real reference Registry entry

The catalog has schema `2` and currently selects:

```json
{
  "schema": 2,
  "modules": {
    "test-module": {
      "repo": "https://github.com/krockzs/neebles-test-module.git",
      "commit": "5db32c4fdec61564415839851c18c092896e11bc",
      "version": "1.2.7"
    }
  }
}
```

The exact installed source remains the referenced commit even if a **documentation-only** commit is later added to the module's `main`. Changing README or release notes on GitHub does not automatically change a published binary, authenticated installed source or old update modal; repinning is an *explicit, separate* release decision. Do not silently change a source pin while describing a docs-only closure as “no update needed.”

### Avoid hazardous publication shortcuts

- Do not publish a floating `main` as an immutable module selector.
- Do not commit or push unreviewed local files, mutate Boss product sources while publishing Registry, or clean unknown local changes automatically.
- Do not rewrite CUSTOM classic rootfs or regenerate unrelated DEB checksums for a source-only module patch.
- Do not tag a new Boss release for a docs-only Test Module change.
- Do not claim that a GitHub Actions artifact, a GitHub Release and a verified installed update are the same event.

---

## 13. Install, update, Critical Update and release notes

### First install

Open **Boss UI → Modules**, select the declared module from the Registry and run the Boss-governed **Install** action. Boss owns authorization, Preinstall, package/material verification, rollback staging and installation. Source repositories and helper installers do **not** substitute for this transaction.

The CLI equivalent `neebles modules install test-module` is a **privileged** operation; prefer the Boss UI authorization workflow. Do not use `sudo` on this module's optional *user-session controller* installer.

After installation, verify the module appears under installed modules and the local manifest declares the expected version:

```bash
neebles modules installed
python3 -m json.tool /opt/neebles/modules/test-module/manifest.json >/dev/null
neebles boss surface-model
```

### Update

Boss UI → Modules → **Update** is the normal governed route. Updating a module's installed source is independent of installing a new Boss product version. If the running app must be closed, follow the transaction's explicit governed Close policy rather than killing an arbitrary PID.

CLI `neebles modules update test-module` is likewise a privileged operation; `--close-running` is a supported explicit update flag. Never force an unreviewed close, purge or rollback on a user's active module simply to produce a green status.

For the 1.2.6 → 1.2.7 upgrade, after Boss finishes updating the module, the explicit helper-migration step was:

```bash
python3 /opt/neebles/modules/test-module/tray/install-session-controller.py
systemctl --user show neebles-test-module-session-controller.service \
  -p ActiveState -p SubState -p ExecStart --no-pager
```

Then test the next KDE session/reboot and cross-surface Open again. This *migration* is separate from Boss's module update transaction. Subsequent updates using the 1.2.7 installed-code path should not need to copy a new script into HOME; any material protocol/service change still requires its own migration review.

### Critical Update and localized release notes

The module owns `critical-update/manifest.json`, currently a valid empty instruction list:

```json
[]
```

An empty manifest does **not** mean “no update”: it means there are no additional declared Critical Update instructions for that release. Do not insert no-op commands just to make the list nonempty.

The last coordinated **published** release has versioned, authenticated notes under:

```text
critical-update/release-notes/es_cl_1_2_7.txt
critical-update/release-notes/en_us_1_2_7.txt
```

The **1.2.8 candidate** also contains `es_cl_1_2_8.txt` and `en_us_1_2_8.txt`; their presence in source does not mean the version was published through CUSTOM/Registry or shown in an installed update modal.

Historical note pairs for 1.2.3–1.2.6 are intentionally retained, so prior changes remain auditable. Boss's generic module-update presentation reads the matching installed source/version/locale notes **for a real version transition**; an initial Install does not falsely display an Update note and reinstalling the same version must not fabricate a new change.

**Release-note authoring law:** record functional changes, security/authority boundaries, explicit user migrations, whether a restart is needed, and what remains unverified. Do **not** hide an optional required systemd user-unit refresh in README only. Locales must agree on facts even when prose differs. A docs-only amendment to notes on GitHub does not retroactively change a previously installed authenticated source or an already-shown update modal.

See the repository's `critical-update/release-notes/` for the actual per-version notes. This documentation delivery also includes reviewed 1.2.7 notes in both locales.

### Uninstall/reinstall

Uninstall is a **Boss-owned transaction**, not a call to an arbitrary module-specific cleanup script. The module describes governed resources in `manifest.json`, and the compatible Boss implementation must verify ownership and route supported cleanup operations through the appropriate Lifecycle Arsenal adapters. The principal runtime and declared Tray are governed separately from the optional `systemd-user` controller. A successful Uninstall must not leave a module-owned service, its executable process, Tray/Bubblewrap runtime or active controller socket behind.

For Test Module 1.2.8, the requested policy is to stop/disable and retire only the exact module-owned `neebles-test-module-session-controller.service` unit, including its user-service enablement symlink, once the transaction passes its safety gates. **Do not remove unrelated units or kill all `python3` processes.** No module-owned XDG Autostart file is declared by Test Module; that new generic Boss adapter must not invent one. A different module may legitimately use XDG Autostart or other explicitly supported resources. Unknown owners or unverified running resources must fail safely rather than be forcibly removed.

User Settings follow an explicit preserve/remove choice. The transaction does **not** delete shared Essential/dependency pools. Rollback before irreversible commit must restore integrity before restarting services that were active beforehand; failures after commit are not an excuse to reanimate a partly removed installation.

**Certification status:** the 2026-10-13 audit observed the 1.2.8 installed manifest and live resources, and 14 passing Python tests. It did **not** run an actual Uninstall, certify all process/Tray shutdown paths or prove the rollback and both Settings choices. Those tests are pending, and the TXN V5 Boss branch is not automatically the installed binary.

---

## 14. Validation and acceptance matrix

A test is **GREEN** only if its inputs, environment and observed result are recorded. `python -m unittest` passing does not certify GUI behavior; a healthy Governor JSON does not prove the Tray button actually re-enabled.

### A. Source and contract checks

From a clean local checkout:

```bash
cd /path/to/neebles-test-module

python3 -m json.tool manifest.json >/dev/null
python3 -m json.tool lifecycle.json >/dev/null
python3 -m json.tool surfaces.json >/dev/null
python3 -m json.tool contracts/commands.json >/dev/null
python3 -m json.tool languages/manifest.json >/dev/null
python3 -m json.tool settings/default.json >/dev/null
python3 -m json.tool critical-update/manifest.json >/dev/null

python3 -m py_compile runtime.py ui/test-module-ui.py \
  tray/tray-provider.py tray/session-controller.py \
  tray/install-session-controller.py

python3 -m unittest discover -s tests -v
```

The **published 1.2.7** source had **nine tests**, covering UI Close → IPC unregister and Governor-controlled Tray status/action behavior. In the **2026-10-13 1.2.8 candidate audit**, the local suite passed **14/14** tests, including declarative Uninstall checks. These are source/contract tests only; they do not certify an actual Linux service, Tray shutdown or on-disk Uninstall transaction.

Before publishing, compare the module's installed manifest version, release-note filenames, CUSTOM material metadata, Construction steps, source SHA and Registry version. A script should fail on unexpected dirty files, but must parse Git porcelain status correctly and must not delete other worktree changes.

### B. Installed-system acceptance — Open/Close

| Scenario | Expected evidence |
|---|---|
| Initial Active, closed | Governor `closed`, `open_available=true`; Open buttons available |
| Open from Boss UI | Exactly one authenticated runtime; Launcher and Tray Open disabled |
| Close Tk UI with X | Session unregisters; RuntimeRegistry returns `closed`; all declared controls become available |
| Open from Launcher, then X | Same single-flight and recovery, no extra modal |
| Open from declared Tray Surface, then X | Same single-flight and recovery |
| Open from module Tray popup, then X | Controller calls Governor, and popup status returns to enabled |
| Manual `neebles modules action test-module open` | All other Open surfaces reflect opening/open; X restores availability |
| Rapid repeated Open clicks | No duplicate authenticated Open runtime |
| Inactive module | Even when `closed`, `open_available=false`; no Open bypass |
| Hide/reopen Tray popup | Fresh canonical status; no stale enabled/disabled flag |
| Controller socket unavailable or invalid payload | Popup Open remains disabled; visible failure, no fallback host launch |
| GUI/IPC abnormal close | Governor releases dead registration as designed |

Read Governor state using `neebles boss surface-model`, not window-title heuristics. Verify on-screen button behavior separately.

### C. Installed-system acceptance — Uninstall (1.2.8 + compatible Boss TXN V5)

Execute on a controlled, recoverable installation. Capture pre/post evidence and the exact installed Boss build SHA; do not assume that the development branch is deployed.

| Scenario | Required evidence |
|---|---|
| Initial state | Installed module manifest, actual user service unit path/state, process identities, Tray/Bubblewrap processes, controller socket and settings snapshot |
| `remove_settings=false` | Module and module-owned executable resources are gone; explicitly retained user Settings survive unchanged |
| `remove_settings=true` | Same complete resource retirement; module Settings are removed according to contract |
| `systemd-user` service | Declared unit stopped, disabled and removed, user enablement symlink absent, manager reloaded; no service process remains |
| Governed runtime and Tray | Governor/runtime and Tray provider stopped; no module-owned descendant/Bubblewrap process remains; ownership verified before destructive actions |
| Controller socket | No live listener or forgotten module-owned socket remains after successful service retirement |
| XDG Autostart | Not declared for Test Module: no synthetic desktop file, no unrelated entry touched; exercise the generic adapter in a separate owned fixture/module |
| Pre-commit failure | Fail closed; verify original manifest/installation/material/settings integrity and safe recovery of previously active services |
| Post-commit failure | Report `CRITICAL` without attempting to resurrect a partially removed installation |
| Foreign/unknown process | Stop and explain unsafe Uninstall; never kill a process on name matching alone |
| Reinstallation | Exact source/material selection, optional helper state and Open/Close/Tray behavior re-verified after a genuine reinstall |

The 2026-10-13 audit is a **pre-Uninstall baseline only**, not evidence that any post-Uninstall criterion above passed.

### D. Other acceptance areas

| Area | Minimum real-system check |
|---|---|
| Commands | Every declared endpoint routes through Boss and respects installed contract/privilege |
| Settings | Option toggles persist/reload; Tray visibility/autostart behave as declared |
| Notifications | Notify action and switch reach Boss presenter; closure callbacks validate identity |
| Tray provider | Icon/provider registration, popup position/dismissal, independent lifetime |
| Desktop startup | No duplicate Boss UI launch; canonical AuthoritySupply; helper user service active only when explicitly enabled |
| Update | Published immutable version is selected, installed and correctly reported; localized notes appear only for real version change |
| Security | No host package fallback, unapproved socket grant, foreign module/session identity or direct admin socket in module Tk UI |
| Material | Exact DEB memberships/hashes, manifest entries/modes, RootFS/world, RuntimeLease isolation |
| Failure/recovery | Network interruptions, failed transaction, rollback, clean uninstall/reinstall on a disposable system |
| Integration | Fresh Live image, installed OS after Calamares, multi-module isolation when supported/tested |

The user reported the exercised installed-system procedure working after the final desktop startup repair; **unexecuted rows above remain a test plan**, not automatically signed-off evidence.

---

## 15. Troubleshooting learned from the real installation

### Tray button never returns Disabled → Enabled

**Observed symptom:** Boss UI and Launcher see the module closed, but the popup's `Open Test Module` stays disabled.

1. Confirm Governor, before touching Boss:

   ```bash
   neebles boss surface-model | python3 -c '
   import json,sys
   for item in json.load(sys.stdin):
       if item.get("name") == "test-module":
           print(item.get("runtime_state"), item.get("open_available"), item.get("enabled"))
   '
   ```

2. Query the module-owned session controller *read-only*:

   ```bash
   python3 - <<'PY'
   import os,socket,json
   path=f"/run/user/{os.getuid()}/neebles/test-module-controller.sock"
   with socket.socket(socket.AF_UNIX) as s:
       s.settimeout(10)
       s.connect(path)
       s.sendall(b'{"action":"status"}\n')
       s.shutdown(socket.SHUT_WR)
       print(json.loads(s.makefile("r").readline()))
   PY
   ```

3. Check the actual executable in the user unit:

   ```bash
   systemctl --user show neebles-test-module-session-controller.service \
     -p ActiveState -p SubState -p ExecStart --no-pager
   ```

If Governor says `closed/true`, but the controller returns only `opened:false` without `open_available`, it is probably still executing 1.2.6's obsolete user-HOME snapshot. Run the **installed 1.2.7** opt-in installer (without sudo), verify the new ExecStart and retest. If the controller correctly returns `closed/true` yet popup remains disabled, then diagnose the popup's background status polling/event processing and active provider revision. **Do not assume that every Disabled state is the same root cause.**

### Boss UI shows untranslated keys and empty Modules after reboot

**Observed symptom:** Qt UI displays literal `app.title`, `config.tray`, `telemetry.settings`, and Modules may be empty; `neebles start` in a proper session restores normal UI until the next KDE login.

- `neebles i18n dump` can still show correct translations and `/opt/neebles/client/languages` remain intact. That rules out missing translation files.
- The running `neebles-ui` may lack `NEEBLES_AUTHORITY_SUPPLY`; Boss UI's `QProcess` CLI transport requires this authenticated authority. It fails closed without it.
- Check the authorized systemd user autostart path:

  ```bash
  systemctl --user cat neebles-boss-ui-autostart.service
  systemctl --user status neebles-boss-ui-autostart.service --no-pager
  journalctl --user -b -u neebles-boss-ui-autostart.service --no-pager -n 30
  ```

- Inspect `~/.config/ksmserverrc` for a saved `/opt/neebles/client/ui/neebles-ui` direct restart while the official autostart also runs. KDE Session Restore can launch a stale UI outside the Boss authority handoff. Use KDE Plasma's **Desktop Session** options to avoid restoring a duplicate Boss window, while preserving legitimate sessions. Do not delete all session state as a first step.
- Inspect environment of `neebles-ui` via `/proc/<PID>/environ` as the same user. Compare with a process launched through the official Boss path. Reopening an existing broken D-Bus window is not equivalent to launching a new correctly authorized process.

**Scope:** this is a Boss/KDE *startup orchestration* lesson discovered during integration, not a Test Module protocol requirement. Do not modify module material or Boss translations to hide the symptom.

### Tray controller absent, inactive or socket unreachable

The user service is opt-in; an uninstalled controller is not a Boss defect. Verify `systemctl --user is-active neebles-test-module-session-controller.service` and its journal. Check that the `session_readonly` grant in the certified `tray-provider` step includes the narrow controller socket. Do not grant the whole user runtime directory or loosen the controller socket's ownership/mode to make a failing test pass.

### Installed version and Registry version differ

An updated Registry is a **remote selection**, not proof of successful installation. Check `neebles modules installed`, `/opt/neebles/modules/<id>/manifest.json` and `neebles boss surface-model`, and ensure the particular update transaction completed. Confirm the module source commit and CUSTOM Construction `fetch`/`checkout` use the same module SHA. Only then investigate material or runtime problems.

### GUI Close leaves Governor permanently Open

This was a historical runtime bug fixed in 1.2.3. The UI child's X must be observed by the owning runtime; otherwise the parent can remain registered forever. Check actual registered session state and runtime cleanup. Do **not** add ad hoc process-name detection to Boss or make Tray kill the foreground module.

---

## 16. Template checklist for a new module

Use this as the actual development order, not as an instruction to copy this module's Python implementation:

- [ ] Pick one module ID and own repository. Write your own `README.md` and explicit contracts.
- [ ] Declare real `manifest.json` schema/version, Lifecycle, Commands and optional Surfaces.
- [ ] Implement a runtime in your chosen language: authenticated Module IPC identity, endpoint registration, subscriptions, invocation, errors and clean Close.
- [ ] Implement the *application* UI/private intents only if needed. No direct privileged Boss calls in private UI.
- [ ] Decide whether `Open` is foreground-window lifetime or durable background service lifetime; test both entry and exit semantics.
- [ ] Declare Settings, localized module strings and Notifications only where actually used.
- [ ] Identify exact Essential + module-delta dependencies in CUSTOM V2, certify membership/integrity and named RootFS/world.
- [ ] Define a Construction recipe with correct `subject`, `rootfs`, `world`, authorities, `init/fetch/checkout` and only the required runtime steps.
- [ ] Document socket, UID, D-Bus, desktop session and filesystem grants; reject accidental host fallbacks.
- [ ] Publish a module source commit; pin the identical SHA in CUSTOM Construction source steps; publish CUSTOM V2.
- [ ] Update Boss's Registry catalog with the exact module source SHA and version; **do not create a separate Registry module**.
- [ ] Provide release notes and explicit migrations for any update that changes a user/system service outside the module's installed files.
- [ ] Install/update via Boss; verify material binding, RuntimeLease, GUI/session lifetime and rollback behavior.
- [ ] Run source tests **and** the real acceptance matrix on target hardware/VM; record the specific scope and evidence.
- [ ] Keep Boss and CUSTOM classic free of module-specific hacks; add a new generic primitive only if a real cross-module capability is missing.

A new Node/Go/Rust module should replace this example's Python/Tk package delta, world name, runtime command, UI/Tray choices and private logic. It should **retain the ownership pattern, authenticated contracts and governance**.

---

## 17. Non-goals, security invariants and future evolution

- This module is an educational/diagnostic consumer, not a required NEEBLES OS component.
- Boss must not grow a `if module == "test-module"` branch or a hardwired module programming language.
- The optional host-user controller exists to bridge a specific, declared sandboxed Tray capability and does not become universal Boss administrative authority. Its two allowed actions are fixed and user-scoped.
- A `session_readonly` socket grant is an intentionally narrow platform capability. It is **not** permission to mount all `/run/user`, the HOME directory, the host D-Bus administrative plane or the unrestricted `neebles` CLI into a module sandbox.
- Governor alone owns Active/Open, one-at-a-time runtime registration, and release of a dead session. Settings are not a second lifecycle database.
- The source SHA, CUSTOM revision, module version, release note locale and Boss product version are **not interchangeable** identifiers.
- A successful update must preserve history and allow diagnosis of old revisions; never rewrite a historical release note to claim a previously absent behavior was already tested.
- A future module with different process lifetime, multiple named RootFS worlds or another language is a new consumer of the generic architecture, not a reason to retrofit this reference's Tk and service behavior into Boss.

---

## 18. Historical compatibility and release chronology

This is **history**, not the procedure for creating a new module today:

| Module version | Main lesson | Current rule |
|---|---|---|
| 1.2.2 | Authenticated Notifications protocol 4 closure callback | Validate session identity; event handlers do not replace public contract |
| 1.2.3 | Closing Tk UI must release the owning Module IPC session | Explicit unregister/disconnect, Governor returns `closed` |
| 1.2.4 | X11 Tray popup placement and localized module update notes | Module presentation remains subordinate to Boss; notes versioned by locale |
| 1.2.5 | Module-owned Tray Settings and declared governed Tray Open Surface | Visibility/autostart are Settings; Open always goes through Governor |
| 1.2.6 | Optional user-session controller for a sandboxed Tray popup | Narrow `status/open` socket; historical HOME snapshot installer is **obsolete** |
| 1.2.7 | Canonical `runtime_state` + `open_available`, fail-closed popup, installed-code controller path | Migrate old user unit once; verify Disabled → Enabled after Close |

**Do not use these obsolete historical patterns as new templates:** MaterialBinding schema 2 as the active Multi-RootFS shape, four-step Construction without `tray-provider`, `modules runtime status`'s historical `registered` field as Open authority, a copied HOME controller as a current installed service, or the assumption that a `closed` runtime is always eligible for Open.

The existing `critical-update/release-notes/es_cl_1_2_3.txt` through `es_cl_1_2_7.txt`, and corresponding `en_us_*` files, are the per-version user-facing historical notes. Keep them with their published revisions; this README is the **current developer tutorial**.

### Final architectural law

A NEEBLES module is correctly integrated when it can:

```text
DECLARE its identity and contracts
    -> SELECT an immutable source revision
    -> OBTAIN exact certified CUSTOM V2 material/worlds
    -> REQUEST only explicit platform authorities
    -> EXECUTE through Boss-governed Lifecycle and Construction
    -> REGISTER authenticated Module IPC runtime/endpoints
    -> PRESENT its own optional UI/Launcher/Tray/Settings/Notifications
    -> CLOSE/UNREGISTER without orphaned state
    -> UPDATE/ROLL BACK/UNINSTALL according to governed transactions
```

**...without introducing any module-specific implementation into Boss.**

That — and not Python/Tk, this module's icon, or its sample buttons — is the reusable N.E.E.B.L.E.S. module contract.


---

## 19. 1.2.8 Uninstall development candidate and pending certification

This section documents **current development source**, not an amendment of the already published 1.2.7 baseline. Test Module commit `3835ca4` declares `uninstall` schema 1, while Boss TXN V5 commit `66f0f7a` is a development implementation with separate governed `systemd-user` and XDG-user Autostart retirement capabilities. Neither a source commit nor a local installation is by itself a certified coordinated release.

### Actual declaration and ownership

The module's `uninstall` contract (`manifest.json`) declares:

- `main: governor`: Boss owns lifecycle and runtime deactivation; this is not a module-supplied `kill` script.
- `extras[id=session-controller]`: `type: service`, `provider: systemd-user`, `name: $hardcoded.session_service`, `exec_start: /usr/bin/python3.13 /opt/neebles/modules/test-module/tray/session-controller.py`, `required: false`, `stop.disable: true`, `stop.timeout_ms: 5000`, `verify: inactive`, `remove: true`.
- `extras[id=tray]`: `type: governed`, `ref: manifest.tray`, `required: false`, `verify: terminated`. This is a distinct governed provider/runtime, **not the same process** as the user-session service.
- `cleanup[id=module-cache]`: `type: directory`, `scope: module-data`, `path: $hardcoded.cache_directory`, `policy: always`.
- `cleanup[id=local-settings]`: `type: settings`, `ref: manifest.settings`, `policy: user-choice`.
- `failure`: `unknown_process_owner`, `resource_still_running` and `cleanup_error` are all `abort`.

The `lifecycle.json` transition named `uninstall` deliberately has no module-specific operations. This is legitimate: Boss runs the governed lifecycle and owns the Uninstall coordinator and declared extra-resource handling; an empty transition must not be misread as a request to skip the Boss transaction.

### Generic contract, not a Test Module special case

The goal of Uninstall TXN V5 is to retire **all module-owned, declared and supported executable resources safely** via appropriate authorities/adapters, not merely this Python helper. The known development adapters cover `systemd-user` services and XDG-user Autostart, while the existing Governor/Boss runtime manages governed resources. Different module technologies require their own declared and verifiable ownership routes; do not add unconditional process-name kills, arbitrary host-wide sweeps or invented `test-module` branches inside Boss.

A module without extras can omit `extras` if allowed by the applicable schema. Test Module currently declares **no XDG Autostart desktop file**; this is not a missing entry. XDG cleanup belongs to a separate real owner or isolated test fixture. No Linux service, socket, process or desktop entry should be removed merely because its name resembles a module ID.

### Evidence and publication gate

The Ryzen audit dated `2026-10-13 20:46` found the 1.2.8 manifest installed and equal to source, a running opt-in user service, Tray/Bubblewrap processes and controller socket. All **14 local Python tests** passed. It did not execute Uninstall and cannot certify resource retirement or rollback. The `systemd-user` removal, governed Tray/runtime shutdown, failure handling and both Settings modes must be demonstrated with before/after traces against an identified installed Boss build.

Only after integral verification should the 1.2.8 release be coordinated with the correct immutable module source, CUSTOM V2 material/Construction identities and Boss Registry selection. **Updating this README does not change the manifest, running installation, Registry, CUSTOM or Boss build.**
