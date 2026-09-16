# N.E.E.B.L.E.S. Test Module

Módulo de referencia para validar el ciclo completo de integración con N.E.E.B.L.E.S. Boss.

## Objetivo

Este módulo existe para comprobar, con una implementación mínima, que Boss puede:

- instalar, actualizar y desinstalar un módulo desde el registry;
- descubrir su launcher y abrir su UI;
- cargar contratos dinámicos;
- registrar un runtime persistente;
- ejecutar comandos por Konsole y desde la UI propia;
- mostrar notificaciones generadas por el módulo;
- administrar un tray provider propio del módulo.

La implementación interna usa Bash, Python y Tkinter sólo como ejemplo. El contrato con Boss no depende de esos lenguajes.

## Estructura

```text
.
├── manifest.json
├── README.md
├── icon.jpeg
├── test-module.sh
├── runtime.py
├── contracts/
│   └── commands.json
├── ui/
│   └── test-module-ui.py
├── tray/
│   └── tray-provider.py
└── languages/
    ├── manifest.json
    ├── es_CL.json
    └── en_US.json
```

## Launcher

Boss descubre `open` desde el bloque Schema 3 compatible del manifest. Esa acción levanta el runtime persistente y la UI del módulo.

```bash
neebles test-module open
```

Mientras la UI permanece abierta, el runtime queda registrado en Boss y atiende los endpoints declarados por `contracts/commands.json`.

## Comandos dinámicos

```bash
neebles test-module version
neebles test-module hello
neebles test-module notify
neebles test-module state
```

Los mismos comandos aparecen como botones dentro de la UI. Cada ejecución atraviesa Boss y genera una notificación visible.

## Tray

El manifest declara el tray nativo de Boss con protocolo 1. Boss administra el ciclo de vida del provider.

Al abrir el tray del módulo, el provider muestra una UI mínima con:

- Opción 1 ON/OFF;
- Opción 2 ON/OFF;
- Botón de prueba.

Cada interacción genera una notificación y publica el estado actualizado al Tray Manager.

## Regla arquitectónica

Boss conoce contratos, identidad, lifecycle y transporte. El módulo conoce su implementación interna.

Cambiar Python por Rust, Go, Node.js, C++ u otro lenguaje no debe requerir modificar Boss mientras se mantengan los mismos contratos y protocolos.


## Contrato final Boss 1.0.7

Desde la versión 1.2.0, el módulo de prueba valida también los contratos persistentes actuales de Boss.

Al registrarse, el runtime declara los endpoints cargados desde `contracts/commands.json` y se suscribe a:

- `module.lifecycle`
- `settings.test-module`

La suscripción de settings pertenece exclusivamente al propio módulo. Boss conserva la autoridad sobre el aislamiento entre módulos.

### Settings IPC

El runtime usa directamente el protocolo persistente de módulos para leer y escribir settings:

neebles test-module settings
neebles test-module toggle

`settings` lee `tray.option1` y `tray.option2` mediante `SettingsGet`.

`toggle` lee y modifica `tray.option1` mediante `SettingsGet` + `SettingsSet`. La persistencia pertenece a Boss y el cambio genera el evento `settings.test-module / changed`.

### Eventos

neebles test-module events

Devuelve los eventos recibidos por el runtime desde las suscripciones activas.

El runtime mantiene sólo un historial acotado de diagnóstico en memoria. No crea una segunda fuente persistente de estado.

### External

neebles test-module external

Genera deliberadamente un error de runtime sin `id` para comprobar la ruta Module IPC -> Boss -> External.

El módulo sólo produce el evento. No decide si puede atravesar la frontera External.

La autoridad global sigue perteneciendo a `telemetry.enabled` en Boss:

- Telemetry OFF: Boss bloquea la transmisión External.
- Telemetry ON: Boss permite que el evento alcance la frontera External configurada.

El módulo nunca puede activar Telemetry por sí mismo.

### Descubrimiento dinámico

La UI obtiene la lista visible de comandos desde `contracts/commands.json`.

Agregar o retirar un endpoint del contrato ya no requiere mantener una segunda lista manual dentro de la UI.
