# N.E.E.B.L.E.S. Schema 3 Reference Module

Este repositorio es el módulo de referencia canónico para el contrato de módulos
N.E.E.B.L.E.S. Schema 3.

Su objetivo no es definir cómo debe estar implementado internamente un módulo.
Su objetivo es demostrar qué necesita declarar un módulo para integrarse con Boss.

## Principio

Boss conoce contratos, no detalles internos.

El módulo mantiene control sobre:

- su implementación;
- su lenguaje y archivos de traducción;
- sus dependencias declaradas;
- sus procesos;
- sus textos de notificación;
- su tecnología interna.

Boss gobierna:

- instalación y actualización;
- validación del manifest;
- dependencias declaradas;
- lifecycle;
- launcher;
- autorización;
- negociación del idioma global;
- transporte y política de notificaciones.

## Estructura

```text
.
├── manifest.json
├── README.md
├── icon.jpeg
├── languages/
│   ├── manifest.json
│   ├── es_CL.json
│   └── en_US.json
├── test-module.sh
└── test-module-gui.py
```

## Contratos demostrados

### Schema

`manifest.json` usa Schema 3.

### Entrypoint

`test-module.sh` es el único entrypoint declarado.

### Lifecycle

El comando `default` es `oneshot`.

El comando `open` es `tracked`.

Boss puede seguir y detener el proceso tracked sin conocer que internamente el módulo usa Python y Tkinter.

### Launcher

Sólo el comando `open` declara `launcher: true`.

Un módulo Schema 3 puede tener como máximo una acción de launcher.

### Idiomas

El módulo mantiene su propio `languages/manifest.json` y sus propios archivos de traducción.

Idiomas incluidos:

- `es_CL`
- `en_US`

Si Boss entrega `NEEBLES_LANGUAGE`, ese valor es autoritativo.

Un `NEEBLES_LANGUAGE` explícito vacío o no soportado es un error.

Si Boss no entrega idioma, el módulo puede descubrir el locale del sistema.

Si el locale del sistema no está soportado, se usa `languages/manifest.json.default`.

### Identidad

Boss entrega `NEEBLES_MODULE`.

Si la variable está definida, debe coincidir exactamente con el nombre declarado por el manifest.

Una identidad explícita vacía o distinta es un error.

### Notificaciones

El módulo declara `notifications.protocol = 1`.

El módulo posee y traduce `title` y `message`.

Boss sólo gobierna transporte, severidad, configuración global e identidad.

### Dependencias

Las dependencias del sistema se declaran en el manifest.

Boss resuelve e instala esas dependencias sin conocer la implementación interna del módulo.

## Regla arquitectónica

Agregar una tecnología interna nueva al módulo no debe requerir modificar Boss.

Comportamiento nuevo = código nuevo.

Conocimiento nuevo = datos nuevos.
