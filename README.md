# N.E.E.B.L.E.S. Test Module

`neebles-test-module` es el módulo canónico de referencia para demostrar que un módulo externo puede integrarse a N.E.E.B.L.E.S. utilizando únicamente los contratos públicos del ecosistema.

No es una aplicación final ni una dependencia productiva obligatoria.

Su función principal es servir como:

- consumidor real del contrato de Boss;
- módulo de certificación;
- referencia de comunicación para módulos futuros;
- plantilla conceptual para comprobar ownership, IPC, Lifecycle, Settings, Surfaces, Tray y Notifications.

La regla arquitectónica es:

> Boss gobierna; el módulo declara; cada owner conserva su verdad.

La versión actual del módulo es **1.2.0** y utiliza **Module Schema 4**, alineada con el contrato cerrado de **N.E.E.B.L.E.S. Boss 1.0.15**.

---

## Rol arquitectónico

Boss no contiene conocimiento específico de `test-module`.

El módulo puede estar implementado en Python hoy y ser reemplazado mañana por Rust, Go, Node.js, C++, C u otra tecnología sin exigir cambios en Boss mientras conserve los mismos contratos públicos.

Por eso este repositorio no define arquitectura de Boss.

Lo consume.

`neebles-test-module` existe para demostrar que:

- instalación y actualización pertenecen al Governor;
- material físico pertenece a CUSTOM;
- Platform Authority pertenece al sistema;
- BUILD materializa;
- Boss autentica, gobierna y enruta;
- Lifecycle ejecuta contratos declarativos;
- Settings persiste una única verdad canónica;
- UI y Tray son consumidores de esa verdad;
- Notifications utiliza el canal gobernado de Boss;
- Runtime IPC conserva identidad y sesión;
- las superficies no inventan functional state.

---

## Estructura

La estructura relevante actual es:

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

No existe Local Installer productivo.

No existe `manifest.commands` top-level.

No existe arquitectura de aplicaciones basada en apt/dpkg dentro del módulo.

No existe fallback de host como autoridad.

---

## Manifest Schema 4

`manifest.json` declara:

- `schema: 4`;
- identidad `test-module`;
- versión `1.2.0`;
- entrypoint `runtime.py`;
- Lifecycle en `lifecycle.json`;
- Surfaces en `surfaces.json`;
- Commands contract en `contracts/commands.json`;
- Tray provider `tray/tray-provider.py`;
- Tray protocol 1;
- Notifications protocol 4;
- Settings contract en `settings/default.json`.

Boss conoce únicamente estas superficies públicas.

No conoce la implementación interna de Python.

---

## Lifecycle

`lifecycle.json` enlaza las acciones generales del Governor:

    governor.install   -> install
    governor.update    -> update
    governor.uninstall -> uninstall
    governor.enable    -> enable
    governor.disable   -> disable

El Test Module no declara actualmente objetos Lifecycle adicionales.

Eso es deliberado.

El estado global Active/Inactive del módulo pertenece a Boss Modules y al Governor.

No existe un objeto artificial `main`.

`OPEN` tampoco significa activar el módulo.

`OPEN` abre el programa principal.

Las cinco transiciones actuales poseen `operations: {}` porque este módulo no necesita ejecutar trabajo específico adicional durante esas fases.

Una transición vacía es válida.

Lifecycle no ejecuta operaciones ficticias sólo para demostrar infraestructura.

Boss dispone del límite genérico:

    boss.workspace_execution
        ->
    construction.step

para módulos que sí necesiten ejecutar Domestic Construction mediante `subject + step`.

El Test Module no obliga a utilizarlo cuando no existe trabajo real que realizar.

---

## Surfaces

`surfaces.json` contiene actualmente una única superficie propia:

    open.launcher

Su acción es:

    open

y representa el acceso al programa principal.

No existe `main.ui`.

No existe un booleano funcional de Active/Inactive duplicado dentro de las superficies.

La visibilidad del launcher pertenece a Boss Settings.

El estado global del módulo pertenece al Governor.

La apertura de la UI es estado efímero del programa.

Son verdades distintas.

---

## Commands contract

`contracts/commands.json` declara actualmente diez comandos:

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

`open` es el launcher canónico.

Los demás utilizan Lifecycle `runtime`.

Ningún endpoint declara root.

Los endpoints internos actuales son:

    ui.open
    test.version
    test.hello
    test.notify
    test.state
    test.settings
    test.setting
    test.toggle
    test.events
    test.external

El runtime descubre sus endpoints desde este contrato.

No mantiene una segunda lista manual.

---

## Runtime IPC

`runtime.py` es actualmente la implementación del runtime persistente.

Python es una decisión de implementación, no una dependencia arquitectónica de Boss.

El runtime:

- se conecta al Module IPC de Boss;
- genera un `session_id`;
- registra identidad y endpoints;
- valida la identidad de las respuestas;
- mantiene una conexión persistente;
- se suscribe a topics permitidos;
- atiende invocaciones;
- procesa eventos;
- responde a shutdown;
- realiza unregister al salir.

Las subscriptions actuales incluyen:

    module.lifecycle
    settings.test-module

Boss conserva el ownership de autenticación, aislamiento y routing.

---

## OPEN y UI

El comando:

    neebles test-module open

resuelve el endpoint:

    ui.open

El runtime crea la UI únicamente cuando corresponde.

La UI no es la fuente de verdad de Settings.

Al abrirse recibe desde el runtime los valores canónicos actuales de:

    features.option1
    features.option2

La UI puede solicitar cambios, pero primero persiste mediante Boss y sólo después refleja el valor canónico aceptado.

Esto aplica la regla:

> persist first, project later.

El estado visual local nunca sustituye la verdad persistente de Boss.

---

## Settings

`settings/default.json` declara actualmente:

    hardcoded.module
    ui
    features.option1
    features.option2

Los settings de las features son:

    features.option1
    features.option2

No pertenecen al namespace Tray.

Tray y UI son dos consumidores distintos de las mismas preferencias del módulo.

El archivo persistente local pertenece al mecanismo de Settings de Boss.

El módulo no lo modifica directamente.

---

## Convergencia realtime

Cualquier writer autorizado puede modificar un setting canónico:

    Boss / CLI
    UI
    Tray
    futuros consumidores

La regla es:

    writer
      ->
    Boss Settings
      ->
    persistencia canónica
      ->
    evento settings.<module>/changed
      ->
    proyección a consumidores

El evento informa del cambio.

No es la fuente de verdad.

UI y Tray convergen inmediatamente al valor aceptado por Boss.

---

## Persistencia

La instalación crea Settings locales desde el default sólo cuando todavía no existen.

Una reinstalación con Settings preservados no sobrescribe el archivo existente.

Un update puede reconciliar el contrato con nuevos defaults sin destruir preferencias compatibles.

Un uninstall puede:

- preservar Settings;
- eliminar Settings cuando se solicita explícitamente.

La elección pertenece al flujo gobernado por Boss.

---

## Tray

El manifest declara:

    tray/tray-provider.py

como provider del Tray Manager.

El Tray provider:

- registra identidad y PID;
- recibe órdenes del Tray Manager;
- utiliza SettingsGet/SettingsSet gobernados;
- mantiene `features.option1`;
- mantiene `features.option2`;
- recibe `settings_changed`;
- vuelve a consultar la verdad canónica durante reload;
- publica su estado visual al manager.

El Tray no define el estado global Active/Inactive del módulo.

Al desactivar el módulo, Boss corta su comportamiento funcional según el Governor.

La configuración visual de las superficies continúa perteneciendo a Boss.

---

## Notifications

Notifications utiliza protocol 4.

El runtime no ejecuta un CLI secundario para notificar.

Envía directamente por Module IPC:

    type: default_notification

incluyendo:

- módulo;
- session_id;
- severity;
- icon relativo al módulo;
- title;
- message;
- timeout;
- replace_id.

Boss responde con:

    notification_ack

o con un error gobernado.

El icono declarado por el módulo es relativo:

    icon.jpeg

Nunca una ruta absoluta privada del host.

---

## External y Telemetry

`test.external` permite comprobar la frontera External de Boss.

El módulo puede producir un diagnóstico.

Eso no le concede autoridad para habilitar Telemetry ni para decidir el transporte exterior.

Telemetry continúa siendo autoridad global de Boss.

Producir un evento y autorizar su salida son responsabilidades separadas.

---

## Material y Preinstall

Las dependencias físicas del Test Module no viven como lógica apt/dpkg dentro del manifest.

CUSTOM conserva y declara el material del módulo.

Actualmente el material certificado contiene:

    47 DEBs

CUSTOM mantiene:

- membership;
- integridad SHA;
- pool compartido;
- Domestic Construction declaration.

Boss ejecuta Preinstall antes de Lifecycle durante install/update.

La regla del pool es:

    DEB existente + SHA correcto
        -> reutilizar

    DEB faltante
        -> obtener desde CUSTOM canónico

    DEB existente + SHA incorrecto
        -> RED
        -> no sobrescribir silenciosamente

Uninstall no elimina el pool compartido.

No existe refcount ni GC productivo para esos artefactos.

---

## Domestic Construction

CUSTOM mantiene la declaración:

    runtime/construction/test-module.json

La declaración describe construction mediante identidades y authorities.

Boss dispone del adapter Lifecycle genérico:

    artillery:
        boss.workspace_execution

    objective:
        construction.step

y acepta únicamente:

    munition.subject
    munition.step

Boss resuelve el resto mediante:

- Domestic Construction;
- AuthoritySupply;
- Materialized Runtime;
- Workspace Execution.

Lifecycle no conoce Python, Git, Qt ni las rutas privadas del módulo.

---

## Critical Update

`critical-update/manifest.json` representa canónicamente la ausencia de instrucciones Critical Update mediante un array JSON vacío (`[]`).

Eso declara explícitamente que la release no requiere instrucciones Critical Update.

No se inventa una operación sólo para poblar el archivo.

---

## Certificación del módulo

La certificación del Test Module se divide en capas.

### Adaptación contractual

Point 9 adapta el módulo al contrato cerrado de Boss.

Entre otras cosas certifica:

- Schema 4;
- Commands contract dinámico;
- Lifecycle final;
- SurfaceContent;
- Module IPC;
- Notifications protocol 4;
- Settings ownership;
- Tray ownership;
- Preinstall;
- CUSTOM material;
- Domestic Construction;
- ausencia de rutas legacy productivas.

### Certificación funcional

Point 10 demuestra el comportamiento completo del módulo:

    install
      ->
    enable
      ->
    UI
      ->
    settings
      ->
    tray
      ->
    notifications
      ->
    disable
      ->
    enable
      ->
    update
      ->
    uninstall
      ->
    reinstall

La aceptación de una ISO N.E.E.B.L.E.S. instalada en VM pertenece a una fase posterior.

No se simula una aceptación de VM desde el host de desarrollo.

---

## Evidencia certificada hasta ahora

La regresión realtime posterior al cleanup de Surface/Lifecycle comprobó:

- Runtime + UI + Tray;
- Boss -> UI + Tray;
- UI -> Boss + Tray;
- Tray -> Boss + UI;
- persistencia después de reinicio;
- cero rewrite inesperado.

La matriz transaccional del Governor comprobó:

- install;
- Preinstall con 47 DEBs reutilizados;
- disable;
- enable;
- disable/re-enable;
- update;
- preservación de Settings;
- uninstall preservando Settings;
- reinstall reutilizando Settings byte-for-byte;
- uninstall eliminando Settings;
- persistencia del pool compartido;
- source productivo intacto.

Estas pruebas no equivalen todavía a la aceptación final de VM.

---

## Fronteras de ownership

Resumen:

    CUSTOM
        conserva y declara material

    OS
        define Platform Authority

    BUILD
        materializa

    Boss
        gobierna, autentica, persiste y enruta

    Lifecycle
        ejecuta contratos declarativos

    Test Module
        consume contratos e implementa comportamiento

El Test Module jamás debe obligar a Boss a conocer su tecnología privada.

---

## Uso como plantilla

El valor de este repositorio no está en copiar su Tkinter, Python o diseño visual.

La plantilla real es la forma en que se conecta al ecosistema:

- Manifest;
- Commands;
- Lifecycle;
- Surfaces;
- Settings;
- Module IPC;
- Tray protocol;
- Notifications;
- ownership;
- authority;
- persistencia.

Los módulos reales pueden tener tecnologías y funcionalidades completamente distintas.

Lo que reutilizan es el contrato de comunicación.

---

## Principio final

Si un futuro módulo puede:

- instalarse;
- declararse;
- comunicarse;
- persistir;
- abrir superficies;
- publicar notificaciones;
- activar/desactivar comportamiento;
- actualizarse;
- desinstalarse;

sin introducir conocimiento específico dentro de Boss, entonces la frontera arquitectónica está funcionando.

Ése es el propósito de N.E.E.B.L.E.S. Test Module.
