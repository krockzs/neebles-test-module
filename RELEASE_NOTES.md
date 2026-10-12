# N.E.E.B.L.E.S. Test Module — Release Notes and Integration Closure

**Reference release:** `1.2.7` · **Status:** published module source and CUSTOM V2 / Boss Registry alignment; installed-system workflow reported working after the separate KDE startup repair.

> This file is a developer-facing consolidated **history and handoff**. Boss's **user-facing, authenticated, localized update notes** remain in `critical-update/release-notes/es_cl_<version>.txt` and `en_us_<version>.txt`. This document does **not** create a new functional module release, does **not** replace those installed note files, and does **not** rewrite the history of earlier releases.

## Publication identities (October 2026 reference)

| Component | Version / revision |
|---|---|
| Test Module declared version | `1.2.7` |
| Functional module source SHA | `5db32c4fdec61564415839851c18c092896e11bc` |
| CUSTOM V2 aligned SHA | `3416f29e57785a520aef93e456daf71440f06e7e` |
| Boss Registry selection SHA | `4c729c4d72ee7dbdf8c25a1501826f557d8678e0` |
| Boss 1.0.51 compiled commit | `ebe8f0242c0c826803bbf22711534eb101058d4b` |

**Do not confuse release identities.** Boss Registry selects the immutable module *source* SHA; Boss separately authenticates an exact CUSTOM V2 *material* revision; `1.0.51` is a *Boss product* release, not the Test Module's version.

---

## Español (Chile) — resumen de cambios

### 1.2.7 — Open del Tray sincronizado con Governor

- El controlador opcional consulta `neebles boss surface-model` y devuelve tanto `runtime_state` como `open_available`.
- `closed` **no** basta por sí solo para habilitar Abrir: el módulo debe encontrarse autorizado por Governor.
- Durante `opening` y `open` el botón Abrir se deshabilita y se impiden aperturas duplicadas a través de Governor.
- El popup comienza con Abrir deshabilitado y consulta nuevamente el estado al mostrarse y mientras está visible.
- La unidad systemd optativa del usuario apunta al **código instalado** del módulo, evitando la copia obsoleta de `~/.local/share/neebles/test-module/session-controller.py`.
- El material de Python/Tk, el mundo RootFS y las 2.242 entradas de los manifiestos conservan sus hashes. No se introdujo una dependencia de Boss específica para Test Module.

**Migración obligatoria para quienes instalaron el controlador con 1.2.6:** después de actualizar el módulo a 1.2.7, ejecutar una vez, **sin sudo**:

```bash
python3 /opt/neebles/modules/test-module/tray/install-session-controller.py
systemctl --user show neebles-test-module-session-controller.service \
  -p ActiveState -p SubState -p ExecStart --no-pager
```

`ExecStart` debe apuntar a `/opt/neebles/modules/test-module/tray/session-controller.py`. Después hay que volver a comprobar el inicio de sesión y la sincronización de Open/Close. El reinicio por sí solo **no** migra una unidad antigua.

**Causa del incidente diagnosticado:** Governor devolvía `closed/true` correctamente, pero el controlador antiguo solo respondía `{'ok': True, 'opened': False}` y no entregaba `open_available`, dejando el botón permanentemente Disabled. No se confirmó un defecto nuevo que obligara a publicar 1.2.8.

### 1.2.6 — controlador opcional de sesión

- Nuevo servicio opcional de usuario, puente controlado entre el popup aislado y la apertura gobernada de Test Module.
- API local reducida a `status/open`, socket Unix por usuario y separación del IPC administrativo de Boss.
- Mejoras de popup sin marco, clic exterior, reconciliación del proveedor y preferencias `tray.visible` / `tray.autostart`.
- **Histórico:** la primera versión del instalador copiaba el controlador al HOME; **no usar esa ruta como ejemplo actual**.

### 1.2.5 — preferencias Tray y Surface gobernada

- Switches del módulo para Mostrar Tray e Iniciar Tray con Linux; estado persistido mediante Settings de Boss.
- Ocultar Tray desactiva también su autostart.
- Superficie `open.tray` declarada y sincronizada con Governor, sin inventar un lanzador adicional.
- El proveedor Tray mantiene vida propia respecto de la ventana principal.

### 1.2.4 — presentación y notas localizadas

- Mejor posicionamiento del popup X11 junto al puntero y dentro de la pantalla.
- Release Notes bilingües por versión; Boss las presenta para **actualizaciones reales**, no para instalación inicial.

### 1.2.3 — Close libera la sesión de Open

- `runtime.py` detecta que terminó la interfaz Tk.
- Se envía `unregister` de la sesión autenticada y se cierra el socket IPC.
- Boss publica `runtime_dead` y recupera `closed`, permitiendo abrir nuevamente sin matar el Tray.

### 1.2.2 — antecedente del protocolo Notifications

- El runtime consume respuestas `notification_closed` autenticadas de Notifications protocolo 4 y valida la identidad de módulo y sesión.
- Esta revisión antecede a la serie de Release Notes 1.2.3–1.2.7 conservada en el repositorio.

### Lección de la integración instalada: inicio de Boss en KDE

Durante la validación del Tray también apareció, tras reiniciar KDE Plasma, una ventana de Boss con claves como `app.title` y `config.tray` y con la lista de módulos vacía. La investigación descubrió una ruta de **KDE Session Restore** que lanzaba `/opt/neebles/client/ui/neebles-ui` directamente, sin la variable de autorización `NEEBLES_AUTHORITY_SUPPLY`, en paralelo al autostart oficial `neebles-boss-ui-autostart.service`. La reparación de ese inicio fue reportada como satisfactoria.

**No es un cambio funcional de Test Module 1.2.7 ni corresponde atribuirlo al instalador del controlador sin evidencias.** Se documenta en el README como diagnóstico de integración y como recomendación para evitar dos autoridades de inicio distintas.

### Alcance de verificación

La publicación de Test Module, CUSTOM V2 y Registry fue comprobada; las nueve pruebas unitarias de 1.2.7 pasaron; Boss 1.0.51 fue compilado y publicado; el usuario reportó el flujo instalado funcionando tras la reparación. **No** se declaran automáticamente certificados todos los escenarios Fresh Live, VM limpia, rollback, desinstalación/reinstalación, multi-RootFS o múltiples módulos simultáneos. Consultar `README.md`, sección 14, antes de afirmar aceptación completa.

---

## English — release summary

### 1.2.7 — Tray Open uses canonical Governor projection

- The optional session controller queries `neebles boss surface-model` and returns both `runtime_state` and `open_available`.
- `closed` alone is insufficient to allow another Open: Governor must explicitly report availability.
- `opening` and `open` disable the popup action; Governor remains the single-flight authority.
- The popup starts fail-closed and refreshes authoritative status when shown and while visible.
- The opt-in systemd user service now executes the **installed module controller**, instead of an outdated HOME-directory snapshot.
- The certified Python/Tk RootFS and material inventory remain unchanged, including 2,242 integrity entries.

**Mandatory one-time migration from the 1.2.6 helper** (run as the desktop user, **without sudo**, after the module update):

```bash
python3 /opt/neebles/modules/test-module/tray/install-session-controller.py
systemctl --user show neebles-test-module-session-controller.service \
  -p ActiveState -p SubState -p ExecStart --no-pager
```

Verify `ExecStart` now uses `/opt/neebles/modules/test-module/tray/session-controller.py`, then verify the next login/reboot and Open/Close recovery. A reboot alone does not rewrite the previous user unit.

**Observed incident:** Governor was already reporting `closed/true`, but the old helper returned only `{'ok': True, 'opened': False}` without `open_available`, so the popup remained disabled. The incident did not establish the need for a functional 1.2.8 release.

### 1.2.6 — optional user-session controller

A narrow user-owned Unix-socket helper enabled a sandboxed module Tray popup to request only `status/open`, without directly accessing Boss administrative IPC. It also introduced popup and reconciliation improvements. Its old HOME-copy installation model is historical and **not** the current template.

### 1.2.5 — module Settings and governed Tray Surface

Module-owned `tray.visible` and `tray.autostart` Settings, synchronized governed `open.tray`, and a Tray provider independent from the foreground window. Hiding Tray disables its autostart preference.

### 1.2.4 — popup placement and localized update notes

Improved pointer-relative X11 positioning with screen clamping, and localized module update notes shown after a real version transition rather than on initial install.

### 1.2.3 — UI Close releases Open

The runtime detects when its Tk child exits, unregisters its authenticated Module IPC session and closes its socket, allowing Boss to publish `runtime_dead` and restore Open availability without stopping the unrelated Tray provider.

### 1.2.2 — Notifications history

The runtime handles authenticated `notification_closed` callbacks from Notifications protocol 4 with module/session validation. This predates the retained per-version 1.2.3–1.2.7 note series.

### Separate KDE startup integration lesson

A KDE Session Restore entry was observed directly launching Boss `neebles-ui` without `NEEBLES_AUTHORITY_SUPPLY`, while Boss's official autostart also existed. That produced unresolved UI translation keys and an empty module list despite intact language files. The user later reported successful repair. This is a **Boss/KDE startup orchestration lesson**, not a newly proven Test Module functional regression. The README documents safe diagnosis without deleting user session files or loosening security boundaries.

### Verification boundary

The 1.2.7 source passed nine unit tests and was published; CUSTOM V2 and Boss Registry were aligned; Boss 1.0.51 was published and installed; the user reported successful integrated operation. Fresh Live, clean VM, rollback and multi-module isolation should be recorded separately when actually exercised.

---

## Localized update notes shipped for each release

| Version | Chilean Spanish | English (US) |
|---|---|---|
| 1.2.3 | `critical-update/release-notes/es_cl_1_2_3.txt` | `critical-update/release-notes/en_us_1_2_3.txt` |
| 1.2.4 | `critical-update/release-notes/es_cl_1_2_4.txt` | `critical-update/release-notes/en_us_1_2_4.txt` |
| 1.2.5 | `critical-update/release-notes/es_cl_1_2_5.txt` | `critical-update/release-notes/en_us_1_2_5.txt` |
| 1.2.6 | `critical-update/release-notes/es_cl_1_2_6.txt` | `critical-update/release-notes/en_us_1_2_6.txt` |
| 1.2.7 | `critical-update/release-notes/es_cl_1_2_7.txt` | `critical-update/release-notes/en_us_1_2_7.txt` |

**Publishing rule:** preserve historical authenticated note files. A future functional version must add its own Spanish/English pair and update the manifest, immutable source selection, CUSTOM V2 Construction/material version and Boss Registry. A docs-only amendment does not manufacture a new module version or trigger a new update modal.
