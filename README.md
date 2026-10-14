# N.E.E.B.L.E.S. — Guia definitiva de desarrollo de modulos

**Referencia funcional y tutorial normativo:** [NEEBLES Test Module v1.2.12](https://github.com/krockzs/neebles-test-module/releases/tag/v1.2.12). Version instalada/codigo fuente y fuentes de material se verifican con los contratos del sistema; ningun README altera los pins por si mismo.

| Identidad | Estado de referencia (14-10-2026) |
|---|---|
| Modulo de ejemplo | `test-module` schema `4`, source `3d265bc62a7ff51ed1c42aecf0158abfa29b3223` |
| CUSTOM V2 | `5dbb74f11d66ad873f422991102d05072c91c0fb`; `59` DEB Essential, `32` delta, 2.242 entradas/manifiesto |
| Boss | `v2.0.0` publicado, Registry `07cd931decce2251333e0982f7b510c272e43188` |
| Pruebas | **38/38 de fuente** ejecutadas en Ryzen; aceptacion instalada se registra separadamente |
| Idiomas | 253 locales, **32 claves/JSON**, `en_US` fallback del modulo; `ui.language` desde Settings |
| Tray | Proveedor moderno mediante Boss Tray Manager y Construction `tray-provider` |

**Ley central:** el modulo define **que hace** y su logica privada; CUSTOM V2/Esbirro certifican material y mundos; NEEBLES OS otorga autoridad de plataforma; Boss gobierna autorizacion, ejecucion, estados y transacciones. Los modulos pueden programarse en cualquier lenguaje que cumpla los protocolos. Python/Tk es solo la implementacion de esta referencia.

## Contenido del tutorial

1. Estado vigente y receta rapida.
2. Arquitectura, dueños y fronteras.
3. Estructura real del proyecto.
4. Identidad y `manifest.json`.
5. Commands y runtime.
6. Lifecycle y Open/Close.
7. Surfaces y coherencia del Open.
8. Settings, idiomas y Notifications.
9. Material certificado CUSTOM V2 y Multi-RootFS.
10. Construction domestico.
11. Tray moderno, login y autostart.
12. Publicacion fuente → CUSTOM → Registry.
13. Install, Update, Critical Update, Uninstall y notas.
14. Pruebas, aceptacion y rollback.
15. Troubleshooting.
16. Checklist para modulos nuevos.
17. Invariantes de seguridad y evolucion.
18. Receta completa y puertas de publicacion.

[Registro historico completo de versiones, incidentes y el antiguo tutorial 1.2.10](docs/history/TEST_MODULE_EVOLUTION.md). Los tutoriales obsoletos quedan ahi **verbatim** y no deben copiarse a proyectos nuevos.

---

## 1. Estado y receta rapida para un modulo nuevo

**Pasos de alto nivel (sin asumir Python/Tk ni instalacion de servicios privados):**

1. Elegir un ID estable (`mi-modulo`) y version semantica, crear repositorio independiente y un `manifest.json` esquema `4` que apunte a los contratos que **realmente** se utilizan.
2. Declarar `lifecycle.json`, `contracts/commands.json` solo si hay comandos publicos, y `surfaces.json` schema `2` para acciones configurables de Boss/Launcher/Tray si se requieren. No declarar capacidades ni estados falsos.
3. Implementar un runtime en el lenguaje elegido con Module IPC autenticado, registro de endpoints, errores y Close que libere Governor. La UI, notificaciones y el Tray son opcionales.
4. Para textos visibles, preparar `settings/default.json` y `languages/manifest.json` mas los JSON de cada idioma soportado. Boss controla el idioma global; el modulo interpreta su propia copia de `ui.language`, emite fallback y actualiza componentes vivos via Settings.
5. Certificar el material exacto en CUSTOM V2: Essential reutilizable, delta, RootFS(s), mundos, integridad SHA y `Construction`. El modulo **no** instala paquetes host arbitrarios ni pide la autoridad de todo HOME.
6. Probar contratos, fuente, mundo y limites de seguridad; publicar un SHA inmutable de la fuente del modulo.
7. En CUSTOM V2, fijar ese SHA exactamente en `fetch` y `checkout`, alinear versiones/material sin modificar hashes de DEB intactos y publicar su commit independiente.
8. En Boss `registry/modules.json` schema `2`, seleccionar `{repo, commit, version}` del modulo. No modificar Boss ni publicar otra release del gobernador por un cambio que solo sea del modulo.
9. Instalar/actualizar desde **Boss UI → Modules** y probar Governor, UI, Settings, Tray, idioma, login, uninstall/reinstall y rollback segun corresponda.
10. Publicar release notes de modulo por version/idioma y, si se decide crear GitHub Release del modulo, adjuntar el archivo fuente exacto y sus SHA. El catalogo de Boss sigue apuntando al commit inmutable, no a un `main` flotante.

**Nota:** El modulo de ejemplo publica 253 JSON para que sus textos coincidan con el catalogo multibanderas; un modulo nuevo solo necesita declarar los idiomas que realmente soporta y un fallback correcto. No debe inventar traducciones no verificadas.

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

## 3. Estructura real de un módulo de referencia

```text
neebles-test-module/
├── README.md                         # tutorial normativo actual
├── manifest.json                     # manifest schema 4, versión 1.2.12
├── lifecycle.json                    # transiciones Governor
├── surfaces.json                     # Launcher, Tray y Config (schema 2)
├── contracts/commands.json           # endpoints públicos (schema 1)
├── runtime.py                        # runtime Python/Tk: ejemplo, no ley
├── ui/test-module-ui.py              # UI propia sin autoridad administrativa
├── tray/tray-provider.py             # proveedor Boss Tray Manager
├── languages/manifest.json           # 253 locales regionales
├── languages/en_US.json              # 32 claves; fallback del módulo
├── languages/es_CL.json              # 32 claves
├── languages/*.json                  # restantes locales declarados
├── settings/default.json             # ui.language, features, tray
├── critical-update/manifest.json     # [] es válido
├── critical-update/release-notes/    # notas localizadas por versión
├── tests/                             # 38 tests al publicar 1.2.12
└── docs/history/TEST_MODULE_EVOLUTION.md
```

El repositorio conserva `tray/session-controller.py` e `install-session-controller.py` solo por historia/migración de instalaciones antiguas. Igualmente, `material/python3.13-tk.manifest.json` es una copia histórica de 1.2.3, **no** la autoridad material actual. Los manifiestos y mundos vigentes están en CUSTOM V2.

Los módulos sin UI, Tray, Notifications ni Settings simplemente omiten esas capacidades y sus archivos. Un módulo Rust, Go, Node o C++ declara su propio runtime, mundo y dependencias en lugar de copiar Python/Tk.

---

## 4. Identidad y manifest actual

Elegir un nombre técnico estable y una versión semántica. El contrato de referencia está en [`manifest.json`](manifest.json), schema **4**, versión **1.2.12**. No confundir el nombre visual de la aplicación con la identidad que firman Boss y CUSTOM.

Ejemplo **reducido e ilustrativo**, para un módulo que implementa Lifecycle y un endpoint Commands, pero que no solicita Tray ni host-user controllers:

```json
{
  "schema": 4,
  "name": "mi-modulo",
  "version": "1.0.0",
  "entrypoint": "runtime.py",
  "lifecycle": "lifecycle.json",
  "contracts": [
    {
      "type": "commands",
      "file": "contracts/commands.json",
      "schema": 1,
      "enabled": true
    }
  ]
}
```

La plantilla no constituye un módulo listo para instalar: hay que crear el runtime y sus contratos reales, probar el parser de Boss y certificar el mundo en CUSTOM V2. Añadir `surfaces`, `settings`, `notifications`, `tray` y `uninstall` **solo si existen** en el producto. No copiar `uninstall.extras.session-controller` de Test Module: ese bloque únicamente permite retirar una unidad `systemd-user` legada si se encuentra bajo autoridad validada; **no ordena instalarla**.

Los comandos públicos se declaran mediante `contracts` (no el antiguo top-level `manifest.commands`). `tray.construction_step` solo se declara si existe ese paso certificado en CUSTOM V2. Cambiar `manifest.version` en un checkout no modifica una instalación ni publica una release.

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

The current Python sample frames Module IPC JSON with a **4-byte big-endian length prefix**, bounds frames, validates session identity and rejects unexpected messages. Do not confuse this channel with the line-delimited authenticated Tray Manager protocol; these are **different protocols and privilege boundaries**. The private session-controller protocol is historical only.

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

The Governor's own **Boss UI Modules/Open** action remains available as an administrative control when allowed. Optional Launcher and Tray controls only exist when declared. The above `open.tray` is a governed Surface in the NEEBLES Tray. The optional **module-owned Tk Tray popup** requests Open through authenticated **Boss Tray Manager** `surface_query` / `surface_action` for that same declared item, not through the obsolete 1.2.7 private controller. Module IPC for the main app remains a different, independently authenticated transport.

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
  "ui": { "language": "en_US" },
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

The current `languages/manifest.json` declares **253 region/language codes** with exactly **32 keys each**. Its module fallback is `en_US` (matching `settings/default.json`), although Boss's global default is `es_CL`. The selected language flows through module Settings `ui.language`; `runtime.py`, UI and Tray handle `settings_changed` for live updates. A module owns its own dictionaries and falls back to its declared default when a locale is missing. Locale parity is structural, not native-language translation certification.

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

The reference's two module integrity manifests have **2,242 entries** each, with the same certified material; the per-RootFS one additionally identifies `python3.13-tk`. Version metadata follows the selected module version. The 1.2.11 → 1.2.12 translation-resource update did **not** require changing certified DEBs or recomposing the same world.

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
arguments: /opt/neebles/modules/test-module/tray/tray-provider.py
```

The `session_readonly` entry is a narrowly granted Unix socket in the authenticated desktop session, **not the entire host `/run`**. Read the productive JSON for exact mounts, `chdir`, arguments and authority mappings; these compact illustrations are not a substitute for it.

A new module may define one or several RootFS worlds. Validate the names and per-step selections; do not silently reuse the wrong RootFS just because two source steps happen to be Python.

---

## 11. Tray moderno, Surface y arranque con Linux

**Patron actual 1.2.12:** el proveedor de Tray vive en `tray/tray-provider.py` y se gobierna mediante **Boss Tray Manager** con `manifest.tray.construction_step = tray-provider`. El mismo Governor gestiona Open desde Boss UI, Launcher y Tray. El popup no crea un segundo runtime principal, otro Governor ni un administrador de sesiones del modulo.

Hay dos conceptos diferentes: (1) un item `surface=tray` de `surfaces.json` que solicita una accion gobernada; (2) un proveedor Tray con popup propio, opcional, que consulta y solicita acciones por el socket concedido `neebles/tray.sock`. Los proveedores se autentican y se ejecutan bajo `modules.runtime`/RuntimeLease/Construction, no lanzando Python en el host como fallback.

### Protocolo del proveedor y aislamiento

- `manifest.tray`: declara `icon`, `provider`, `protocol` y `construction_step` **real**.
- `runtime/construction/<module-id>.json` en CUSTOM V2: declara el paso persistente del proveedor, el mundo, RootFS y grants de sesion explicitamente necesarios.
- El Tray Manager usa JSON delimitado por **salto de linea** para `surface_query` / `surface_action`, validando `tray_id`, `item_id`, origen/PID y accion declarada.
- El Module IPC del runtime principal usa **otro transporte**, con prefijo de longitud de 4 bytes. No confundir los protocolos ni montar un socket como si fuera otro.
- Si Boss no puede autenticar/resolver el paso, falla en cerrado. Nada de ejecuciones paralelas por host, `sudo`, HOME irrestricto o sockets privados improvisados.

Los archivos `tray/session-controller.py` y `tray/install-session-controller.py` son **legado de migracion 1.2.6–1.2.9**. El `uninstall.extras` de Test Module aun declara la unidad `neebles-test-module-session-controller.service` para **retirarla si existiera**, no para instalarla. **No copiar ni ejecutar esa unidad** al crear un modulo nuevo. Su historia integra se conserva en [`docs/history/TEST_MODULE_EVOLUTION.md`](docs/history/TEST_MODULE_EVOLUTION.md).

### Settings vs inicio efectivo

Los strings `tray.visible`, `tray.autostart` y `tray.session_boot_id` son preferencias/metadata, no pruebas de procesos activos. `Show Tray` y `Start Tray with Linux` son opciones diferentes; el reinicio/login de KDE debe comprobar que el proveedor nace solo cuando corresponda y que el popup pide Open una sola vez. Desactivar el autostart debe funcionar sin deshabilitar la apertura manual. No declarar un login probado por haber recibido un Settings ACK.

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
      "commit": "3d265bc62a7ff51ed1c42aecf0158abfa29b3223",
      "version": "1.2.12"
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

The CLI equivalent `neebles modules install test-module` is a **privileged** operation; prefer the Boss UI authorization workflow. A new module must not install the old private session controller; its migration procedure is archived.

After installation, verify the module appears under installed modules and the local manifest declares the expected version:

```bash
neebles modules installed
python3 -m json.tool /opt/neebles/modules/test-module/manifest.json >/dev/null
neebles boss surface-model
```

### Update

Boss UI → Modules → **Update** is the normal governed route. Updating a module's installed source is independent of installing a new Boss product version. If the running app must be closed, follow the transaction's explicit governed Close policy rather than killing an arbitrary PID.

CLI `neebles modules update test-module` is likewise a privileged operation; `--close-running` is a supported explicit update flag. Never force an unreviewed close, purge or rollback on a user's active module simply to produce a green status.

**Legacy migration only:** upgrading an installation from the discontinued 1.2.6–1.2.9 private session controller required explicit user-unit handling. This is **not** the 1.2.12 installation or update procedure. A new module must not install the private controller. See [`docs/history/TEST_MODULE_EVOLUTION.md`](docs/history/TEST_MODULE_EVOLUTION.md) when auditing an old installation.

### Critical Update and localized release notes

The module owns `critical-update/manifest.json`, currently a valid empty instruction list:

```json
[]
```

An empty manifest does **not** mean “no update”: it means there are no additional declared Critical Update instructions for that release. Do not insert no-op commands just to make the list nonempty.

The **published 1.2.12** release carries localized, authenticated notes at:

```text
critical-update/release-notes/es_cl_1_2_12.txt
critical-update/release-notes/en_us_1_2_12.txt
```

Older note pairs remain in the repository for historical diagnosis. A notes file present in GitHub does not retroactively change the exact source pinned in an already-installed MaterialBinding or prove the update modal appeared.

Historical note pairs for 1.2.3–1.2.6 are intentionally retained, so prior changes remain auditable. Boss's generic module-update presentation reads the matching installed source/version/locale notes **for a real version transition**; an initial Install does not falsely display an Update note and reinstalling the same version must not fabricate a new change.

**Release-note authoring law:** record functional changes, security/authority boundaries, explicit user migrations, whether a restart is needed, and what remains unverified. Do **not** hide an optional required systemd user-unit refresh in README only. Locales must agree on facts even when prose differs. A docs-only amendment to notes on GitHub does not retroactively change a previously installed authenticated source or an already-shown update modal.

See the repository's `critical-update/release-notes/` for the actual per-version notes. Earlier 1.2.7 notes remain available in both locales; new updates use the 1.2.12 release notes.

### Uninstall/reinstall

Uninstall is a **Boss-owned transaction**, not a call to an arbitrary module-specific cleanup script. The module describes governed resources in `manifest.json`, and the compatible Boss implementation must verify ownership and route supported cleanup operations through the appropriate Lifecycle Arsenal adapters. The principal runtime and declared Tray are governed independently. Only an authenticated legacy `systemd-user` controller, if actually present, may be considered for governed removal. A successful Uninstall must not leave a module-owned service, its executable process, Tray/Bubblewrap runtime or active controller socket behind.

The current Test Module 1.2.12 retains the declared compatibility policy to stop/disable and retire only the exact module-owned `neebles-test-module-session-controller.service` unit, including its user-service enablement symlink, once the transaction passes its safety gates. **Do not remove unrelated units or kill all `python3` processes.** No module-owned XDG Autostart file is declared by Test Module; that new generic Boss adapter must not invent one. A different module may legitimately use XDG Autostart or other explicitly supported resources. Unknown owners or unverified running resources must fail safely rather than be forcibly removed.

User Settings follow an explicit preserve/remove choice. The transaction does **not** delete shared Essential/dependency pools. Rollback before irreversible commit must restore integrity before restarting services that were active beforehand; failures after commit are not an excuse to reanimate a partly removed installation.

**Certification boundary (1.2.12):** 38 module source tests passed on Ryzen. The developer separately reported working installation, module UI and Tray. Those facts do **not** automatically prove induced rollback, all cleanup-failure cases, every Settings preservation choice, two concurrent Trays or full login/autostart coverage. Record each installed acceptance gate with its own evidence.

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

python3 -m py_compile runtime.py ui/test-module-ui.py tray/tray-provider.py

python3 -m unittest discover -s tests -v
```

Al publicar v1.2.12, la suite de fuente paso **38/38 pruebas** en Ryzen. Son pruebas de fuente y contratos, no de login/reinicio, fallos inducidos o recuperacion instalada. Los recuentos y experimentos antiguos quedan en el historial.

Before publishing, compare the module's installed manifest version, release-note filenames, CUSTOM material metadata, Construction steps, source SHA and Registry version. A script should fail on unexpected dirty files, but must parse Git porcelain status correctly and must not delete other worktree changes.

### B. Installed-system acceptance — Open/Close

| Scenario | Expected evidence |
|---|---|
| Initial Active, closed | Governor `closed`, `open_available=true`; Open buttons available |
| Open from Boss UI | Exactly one authenticated runtime; Launcher and Tray Open disabled |
| Close Tk UI with X | Session unregisters; RuntimeRegistry returns `closed`; all declared controls become available |
| Open from Launcher, then X | Same single-flight and recovery, no extra modal |
| Open from declared Tray Surface, then X | Same single-flight and recovery |
| Open from module Tray popup, then X | Tray Manager authenticates `surface_action`; Governor opens once and popup refreshes canonical availability |
| Manual `neebles modules action test-module open` | All other Open surfaces reflect opening/open; X restores availability |
| Rapid repeated Open clicks | No duplicate authenticated Open runtime |
| Inactive module | Even when `closed`, `open_available=false`; no Open bypass |
| Hide/reopen Tray popup | Fresh canonical status; no stale enabled/disabled flag |
| Tray Manager socket unavailable or invalid response | Popup Open fails closed; no private controller or host CLI fallback |
| GUI/IPC abnormal close | Governor releases dead registration as designed |

Read Governor state using `neebles boss surface-model`, not window-title heuristics. Verify on-screen button behavior separately.

### C. Installed-system acceptance — Uninstall (Test Module 1.2.12 + compatible Boss TXN V5)

Execute on a controlled, recoverable installation. Capture pre/post evidence and the exact installed Boss build SHA; do not assume that the development branch is deployed.

| Scenario | Required evidence |
|---|---|
| Initial state | Installed module manifest, actual process identities, Tray/Bubblewrap ownership and Settings; legacy user unit/socket only if genuinely present |
| `remove_settings=false` | Module and module-owned executable resources are gone; explicitly retained user Settings survive unchanged |
| `remove_settings=true` | Same complete resource retirement; module Settings are removed according to contract |
| Legacy `systemd-user` service (if present) | Only the exactly declared, owner-verified legacy unit is stopped/disabled/removed with no surviving enabled symlink |
| Governed runtime and Tray | Governor/runtime and Tray provider stopped; no module-owned descendant/Bubblewrap process remains; ownership verified before destructive actions |
| Legacy controller socket (if present) | No listener or module-owned socket survives after safe retirement; new installations must not create one |
| XDG Autostart | Not declared for Test Module: no synthetic desktop file, no unrelated entry touched; exercise the generic adapter in a separate owned fixture/module |
| Pre-commit failure | Fail closed; verify original manifest/installation/material/settings integrity and safe recovery of previously active services |
| Post-commit failure | Report `CRITICAL` without attempting to resurrect a partially removed installation |
| Foreign/unknown process | Stop and explain unsafe Uninstall; never kill a process on name matching alone |
| Reinstallation | Exact source/material selection, modern Tray Manager integration and Open/Close/Tray behavior re-verified after a genuine reinstall |

Los experimentos antiguos de 2026-10-13 estan en el historial. Esta matriz requiere evidencia nueva del Boss y el modulo realmente instalados; las 38 pruebas de fuente no sustituyen el Uninstall real.

### D. Other acceptance areas

| Area | Minimum real-system check |
|---|---|
| Commands | Every declared endpoint routes through Boss and respects installed contract/privilege |
| Settings | Option toggles persist/reload; Tray visibility/autostart behave as declared |
| Notifications | Notify action and switch reach Boss presenter; closure callbacks validate identity |
| Tray provider | Icon/provider registration, popup position/dismissal, independent lifetime |
| Desktop startup | No duplicate Boss UI; canonical AuthoritySupply; Tray Manager starts under session authority and module provider autostart follows preferences |
| Update | Published immutable version is selected, installed and correctly reported; localized notes appear only for real version change |
| Security | No host package fallback, unapproved socket grant, foreign module/session identity or direct admin socket in module Tk UI |
| Material | Exact DEB memberships/hashes, manifest entries/modes, RootFS/world, RuntimeLease isolation |
| Failure/recovery | Network interruptions, failed transaction, rollback, clean uninstall/reinstall on a disposable system |
| Integration | Fresh Live image, installed OS after Calamares, multi-module isolation when supported/tested |

The user reported the exercised installed-system procedure working after the final desktop startup repair; **unexecuted rows above remain a test plan**, not automatically signed-off evidence.

---

## 15. Troubleshooting learned from the real installation

### Open del popup Tray permanece deshabilitado (1.2.12)

Boss UI, Launcher y Tray deben consultar la **misma** verdad de Governor. Un error de sincronizacion visual no justifica recrear `test-module-controller.sock` ni ejecutar el CLI administrativo desde el sandbox.

1. Revisar `neebles boss surface-model`: `enabled`, `runtime_state` y `open_available` para la identidad instalada.
2. Confirmar la existencia real del proveedor gobernado por Construction `tray-provider`, con su RootFS, mundo y session authority. El socket productivo es `neebles/tray.sock`.
3. Revisar las respuestas autenticadas `surface_query` y `surface_action` de Boss Tray Manager: `tray_id`, `item_id`, identidad de proceso y estado del item realmente declarado.
4. Si Governor informa `closed/open_available=true` pero el popup sigue deshabilitado, inspeccionar la actualizacion del Surface, los eventos Settings y el provider seleccionado; nunca sustituirlo por un helper host no autenticado.

La migracion 1.2.6–1.2.9 y su controlador privado permanecen íntegros en [`docs/history/TEST_MODULE_EVOLUTION.md`](docs/history/TEST_MODULE_EVOLUTION.md).

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
- The former optional host-user controller was an **obsolete migration mechanism**, not a model for new modules. The current module Tray provider consumes the authorized generic Boss Tray Manager transport. Legacy removal is confined to exact declared owner resources.
- A `session_readonly` socket grant is an intentionally narrow platform capability. It is **not** permission to mount all `/run/user`, the HOME directory, the host D-Bus administrative plane or the unrestricted `neebles` CLI into a module sandbox.
- Governor alone owns Active/Open, one-at-a-time runtime registration, and release of a dead session. Settings are not a second lifecycle database.
- The source SHA, CUSTOM revision, module version, release note locale and Boss product version are **not interchangeable** identifiers.
- A successful update must preserve history and allow diagnosis of old revisions; never rewrite a historical release note to claim a previously absent behavior was already tested.
- A future module with different process lifetime, multiple named RootFS worlds or another language is a new consumer of the generic architecture, not a reason to retrofit this reference's Tk and service behavior into Boss.

---


## 18. Receta integral y puertas de publicacion (1.2.12)

### Ejemplo completo verificable

```text
module repo:              krockzs/neebles-test-module
manifest name:            test-module
manifest version:         1.2.12
manifest schema:          4
custom construction:      runtime/construction/test-module.json
construction steps:       init, fetch, checkout, open-runtime, tray-provider
rootfs selector:          python3.13-tk
world:                    modules.python3.13-tk
Boss Registry version:    1.2.12
settings locale fallback: en_US
Boss default locale:      es_CL
module translation keys:  32 por JSON
```

La identidad `test-module` y el runtime Python/Tk son **ilustrativos**: un modulo nuevo crea su nombre y dependencias, no clona una identidad ya registrada. No instalar ni crear un `test-module-controller.sock`; eso pertenece al historial.

### Gates antes de declarar una entrega GREEN

| Gate | Requerimiento | Evidencia |
|---|---|---|
| Contratos | Manifest, Lifecycle, Surfaces, Commands y Settings JSON validos | Parse JSON + tests propios |
| Material | Essential/delta, archivos, paths, modes, SHA y mundos coincidentes | Validacion de CUSTOM V2/Esbirro |
| Revision | Module SHA exactamente igual al `fetch`/`checkout` y Registry | Comparacion de 40 caracteres |
| Runtime | IPC autenticado, session close, single-flight Governor | Tests + ejecucion controlada |
| Tray opcional | Proveedor bajo Construction, socket grant y login/visible/autostart correctos | Inspeccion de runtime real en KDE |
| Idiomas | UI/Tray/Surface reacciona a `ui.language`; fallback real | Alternar `es_CL → en_US → es_CL` en Boss |
| Transactions | Install, Update, Uninstall, settings preserve/remove, rollback | Prueba de sistema, incluyendo fallos inyectados donde aplique |
| Publicacion | Notas localizadas y artefactos realmente certificados | SHA256SUMS y release, sin recompilar en publicacion |

Comandos de prueba local para **este** repositorio:

```bash
cd /home/thomyorke/NEEBLES/neebles-test-module
python3 -m json.tool manifest.json >/dev/null
python3 -m json.tool lifecycle.json >/dev/null
python3 -m json.tool surfaces.json >/dev/null
python3 -m json.tool contracts/commands.json >/dev/null
python3 -m json.tool languages/manifest.json >/dev/null
python3 -m json.tool settings/default.json >/dev/null
python3 -m json.tool critical-update/manifest.json >/dev/null
python3 -m py_compile runtime.py ui/test-module-ui.py tray/tray-provider.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

**No se deben confundir** las 38 pruebas de fuente registradas en Ryzen, los tests de un modulo nuevo, la compilacion Esbirro, el release de GitHub y el comportamiento observado de la version instalada. Cada uno es un gate distinto.

### Referencias canonicas

- [`manifest.json`](manifest.json) y contratos del modulo: semantica declarada por el consumidor.
- `neebles-custom/README_CUSTOM_V2.md`: paquetes/RootFS/Construction de modulos.
- `neebles-custom/portable/esbirro/README.md`: domesticacion, confinamiento y certificacion.
- `neebles-boss/README.md`: gobernador, RuntimeLease, Tray Manager, Registry y transacciones.
- [`docs/history/TEST_MODULE_EVOLUTION.md`](docs/history/TEST_MODULE_EVOLUTION.md): diagnosticos, migraciones y versiones anteriores, no pasos nuevos.

**Contrato final:** agregar un nuevo modulo es agregar una **declaracion y material autenticado**, no una rama especial para su lenguaje dentro de Boss.
