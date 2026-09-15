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
