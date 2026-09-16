# N.E.E.B.L.E.S. Test Module

`neebles-test-module` es el módulo canónico de referencia para validar la integración real entre un módulo externo y N.E.E.B.L.E.S. Boss.

Su objetivo no es ofrecer una función de usuario final ni convertirse en una dependencia productiva del ecosistema. Existe para comprobar, de forma pequeña, explícita y reproducible, que los contratos públicos de Boss funcionan como fueron diseñados.

En otras palabras: este repositorio es el ratón de laboratorio de Boss.

Cuando una arquitectura nueva entra a Boss, este módulo permite verificar que un tercero podría utilizarla sin conocer la implementación interna de Boss y sin necesitar privilegios especiales fuera de los contratos declarados.

La versión actual del módulo es **1.2.0** y está alineada con **N.E.E.B.L.E.S. Boss 1.0.7**.

---

## Por qué existe este módulo

Boss gobierna el ecosistema, pero no debe conocer la implementación interna de cada módulo.

Un módulo puede estar escrito en Python, Rust, Go, Node.js, C++, Bash o cualquier otra tecnología. Lo importante es que respete los contratos públicos que Boss expone.

Ese principio es central para N.E.E.B.L.E.S.:

> Boss gobierna; el módulo declara; el módulo ejecuta.

Por eso un módulo de prueba útil no puede limitarse a imprimir `Hello World`.

Debe comportarse como un módulo real y recorrer los mismos caminos que recorrería un módulo de producción:

- instalación desde registry;
- lectura de `manifest.json`;
- resolución de dependencias;
- carga de contratos dinámicos;
- registro de runtime persistente;
- identidad y `session_id`;
- lifecycle;
- invocaciones dinámicas;
- settings persistentes;
- aislamiento de settings;
- subscriptions;
- eventos;
- tray provider;
- notificaciones;
- External;
- Telemetry como autoridad global de Boss;
- cierre limpio del runtime.

La idea es que, si este módulo funciona, Boss está demostrando que un módulo externo puede integrarse utilizando únicamente interfaces públicas.

---

## Qué NO es este módulo

Este repositorio no intenta ser:

- una aplicación final;
- una API paralela a Boss;
- una segunda fuente de configuración;
- un reemplazo del registry;
- un reemplazo de los settings de Boss;
- un sistema de telemetry propio;
- una dependencia obligatoria del sistema;
- una implementación especial que Boss deba conocer por nombre.

Boss no contiene lógica específica para `test-module`.

El módulo debe funcionar porque cumple los mismos contratos que cualquier otro módulo.

Ese detalle es deliberado: si Boss necesitara saber que este módulo es "especial", la prueba perdería valor arquitectónico.

---

## Arquitectura general

El módulo se organiza de la siguiente forma:

    neebles-test-module/
    ├── manifest.json
    ├── README.md
    ├── icon.jpeg
    ├── test-module.sh
    ├── runtime.py
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
    └── ui/
        └── test-module-ui.py

Cada pieza tiene una responsabilidad separada.

`manifest.json` declara el módulo.

`contracts/commands.json` declara comandos dinámicos.

`settings/default.json` define el árbol de settings permitido.

`runtime.py` implementa el runtime persistente del módulo.

`tray/tray-provider.py` implementa el provider del tray.

`ui/test-module-ui.py` implementa una UI mínima de prueba.

`languages/` mantiene las cadenas visibles separadas de la lógica.

---

## Manifest Schema 3

El módulo utiliza `manifest.json` con Schema 3.

Actualmente declara:

- nombre: `test-module`;
- versión: `1.2.0`;
- entrypoint: `test-module.sh`;
- settings: `settings/default.json`;
- contrato dinámico de tipo `commands`;
- dependencias de sistema estructuradas;
- comandos estáticos mínimos;
- tray provider;
- protocolo de notificaciones.

El manifest no describe cómo está implementada internamente cada función.

Describe únicamente lo que Boss necesita conocer para gobernar el módulo.

---

## Dependencias

El módulo declara dependencias de sistema estructuradas en el manifest.

Actualmente utiliza:

- `python3`;
- `python3-tk`.

Cada dependencia declara por separado:

- cómo instalarla;
- cómo verificarla;
- si es requerida.

Boss es responsable de resolver ese contrato mediante su sistema de dependencias.

El módulo no ejecuta `apt` directamente para autocorregirse.

Eso mantiene una sola autoridad de instalación y permite que Boss pueda auditar, reparar y reverificar dependencias de manera coherente.

---

## Launcher y lifecycle

El manifest declara el comando `open` como:

- `lifecycle: tracked`;
- `launcher: true`;
- sin requerir root.

El usuario puede abrir el módulo con:

    neebles test-module open

Boss inicia el entrypoint y sigue el lifecycle del proceso.

El runtime permanece vivo mientras la UI está abierta.

Cuando la UI se cierra, el runtime envía `unregister` y termina limpiamente.

Si Boss solicita `shutdown`, el runtime responde con `shutdown_ack` antes de terminar.

El runtime también responde a `ping` con `pong`.

---

## Runtime persistente

El runtime se implementa actualmente en Python, pero Python no forma parte del contrato arquitectónico.

Su responsabilidad es conectarse al socket de módulos de Boss:

    /run/neebles/modules.sock

El socket puede ser reemplazado durante pruebas mediante:

    NEEBLES_MODULES_SOCKET

La comunicación usa:

- Unix socket;
- conexión persistente;
- framing binario con longitud de 32 bits;
- JSON UTF-8 como payload;
- límite local de frame de 16 MiB.

La conexión permanece activa durante toda la vida del runtime.

---

## Registro del runtime

Al iniciar, el runtime crea un `session_id` único y envía un mensaje `register`.

Declara:

- protocolo;
- identidad del módulo;
- `session_id`;
- endpoints realmente cargados.

Los endpoints no están duplicados manualmente dentro del runtime.

Se descubren desde:

    contracts/commands.json

Esto evita que el contrato y la implementación mantengan dos listas separadas que puedan divergir.

Boss valida el registro antes de aceptar el runtime.

Entre otras cosas, Boss puede comprobar:

- versión del protocolo;
- identidad instalada;
- estado enabled;
- validez de los endpoints declarados;
- duplicación de runtimes;
- correspondencia entre instalación y contrato.

Sólo después de esa validación Boss responde con `registered`.

---

## Identidad y aislamiento de sesión

Cada mensaje importante del runtime conserva dos identificadores:

- `module`;
- `session_id`.

El runtime valida las respuestas de Boss y rechaza mensajes que no correspondan a su identidad o sesión actual.

Esto evita tratar una conexión persistente como un canal anónimo.

El runtime no asume que cualquier mensaje recibido por el socket le pertenece.

---

## Contratos dinámicos

El archivo:

    contracts/commands.json

declara actualmente ocho comandos dinámicos:

    neebles test-module version
    neebles test-module hello
    neebles test-module notify
    neebles test-module state
    neebles test-module settings
    neebles test-module toggle
    neebles test-module events
    neebles test-module external

Cada comando utiliza lifecycle `runtime` y state mode `preserve`.

Boss traduce el comando visible a un endpoint concreto y entrega una invocación al runtime registrado.

El módulo responde utilizando el mismo:

- `id`;
- `module`;
- `session_id`;
- `contract`;
- `endpoint`.

Esto permite que Boss correlacione invocaciones y respuestas sin conocer la implementación interna del endpoint.

---

## Comando `version`

    neebles test-module version

Devuelve la versión declarada en `manifest.json`.

Su propósito es comprobar:

- resolución de comando dinámico;
- invocación runtime;
- lectura de manifest;
- respuesta estructurada;
- notificación del módulo.

---

## Comando `hello`

    neebles test-module hello

Devuelve una cadena localizada.

Su propósito es comprobar que la implementación interna puede utilizar el sistema de idiomas del propio módulo sin que Boss necesite conocer sus archivos de traducción.

---

## Comando `notify`

    neebles test-module notify

Genera una notificación mediante:

    neebles notify

Sirve para comprobar que un módulo puede usar la infraestructura pública de notificaciones de Boss en lugar de implementar un mecanismo paralelo.

---

## Comando `state`

    neebles test-module state

Devuelve información del runtime, incluyendo:

- estado `ready`;
- `session_id`;
- estado de la UI;
- subscriptions actuales;
- cantidad de eventos retenidos en memoria.

Este comando permite observar el estado del runtime sin acceder directamente a estructuras internas de Boss.

---

## Settings persistentes

El módulo declara su árbol permitido en:

    settings/default.json

Actualmente contiene:

    hardcoded.module
    tray.option1
    tray.option2
    ui

Los valores editables siguen el contrato String utilizado por Boss.

El runtime no modifica directamente archivos dentro de `/opt/neebles/shared/settings`.

Utiliza el protocolo IPC de módulos.

---

## SettingsGet

El comando:

    neebles test-module settings

solicita a Boss:

    tray.option1
    tray.option2

utilizando mensajes `settings_get`.

Boss:

1. identifica al módulo por su sesión;
2. carga el default declarado por el módulo;
3. carga o crea el estado local persistente;
4. aplica la lógica de settings efectivos;
5. devuelve `settings_value`.

El módulo recibe el valor efectivo, no necesita conocer dónde ni cómo Boss persiste ese estado.

---

## SettingsSet

El comando:

    neebles test-module toggle

lee primero:

    tray.option1

y luego escribe el valor contrario mediante `settings_set`.

Boss realiza la persistencia.

El módulo no escribe directamente el archivo local de settings.

Esto valida una propiedad importante de la arquitectura:

> el módulo posee el significado de su setting, pero Boss posee el mecanismo de persistencia y aislamiento.

Cuando el valor realmente cambia, Boss publica además un evento:

    topic: settings.test-module
    event: changed

---

## Persistent Convergence

Los settings del módulo están diseñados para trabajar con el modelo de convergencia persistente de Boss:

    hardcoded
        >
    local sparse meaningful state
        >
    module defaults

Esto significa que:

- los hardcoded no pueden ser sobrescritos localmente;
- los cambios del usuario sobreviven reinstalaciones compatibles;
- valores iguales al default no necesitan duplicarse como estado local;
- nuevos defaults pueden aparecer sin destruir preferencias compatibles;
- settings eliminados del contrato no permanecen artificialmente como estado válido.

El módulo existe también para comprobar que esta arquitectura funciona desde la perspectiva de un consumidor externo.

---

## Aislamiento de settings

El runtime se suscribe únicamente a:

    settings.test-module

No se suscribe a settings de otros módulos.

Boss rechaza suscripciones del tipo:

    settings.otro-modulo

cuando son solicitadas por `test-module`.

Además, el registry de Boss vuelve a filtrar eventos de settings por propietario incluso si un runtime utiliza una suscripción wildcard.

Esto implementa aislamiento en más de una capa.

El módulo de prueba no intenta evadir ese aislamiento; lo utiliza como parte del contrato esperado.

---

## Subscriptions

Después de recibir `registered`, el runtime envía un mensaje `subscribe`.

Actualmente solicita:

    module.lifecycle
    settings.test-module

Boss responde con `subscribed`.

El runtime verifica que el conjunto aceptado coincide con el solicitado.

Si Boss responde con un conjunto inesperado, el runtime considera que el contrato no fue satisfecho.

---

## Eventos

Los eventos recibidos se almacenan temporalmente en memoria.

El historial utiliza una cola acotada de 64 elementos.

No existe persistencia paralela en disco.

El comando:

    neebles test-module events

devuelve:

- subscriptions activas;
- eventos retenidos.

Esto permite probar eventos sin convertir el test-module en una segunda base de datos del sistema.

---

## `module.lifecycle`

El runtime se suscribe a:

    module.lifecycle

Este topic permite observar eventos de lifecycle que Boss publica para módulos y runtimes.

Entre ellos pueden aparecer eventos relacionados con:

- runtime ready;
- runtime dead;
- instalación;
- actualización;
- enable;
- disable;
- uninstall.

El módulo no decide cuándo ocurre un lifecycle.

Sólo recibe la información que Boss publica.

---

## Tray provider

El manifest declara un tray provider con protocolo 1.

El provider se inicia cuando Boss lo solicita mediante:

    NEEBLES_CALLER=tray-manager

y utiliza el mismo entrypoint general:

    test-module.sh

El script delega entonces en:

    tray/tray-provider.py

El tray provider se conecta al socket del Tray Manager y registra:

- protocolo;
- `tray_id`;
- módulo propietario;
- PID.

---

## Estado del tray

El tray mantiene dos opciones de prueba:

    tray.option1
    tray.option2

Su UI permite:

- activar o desactivar Opción 1;
- activar o desactivar Opción 2;
- ejecutar un botón de prueba.

Cada cambio utiliza settings persistentes de Boss.

El estado visual del tray no es la fuente de verdad.

La fuente de verdad sigue siendo Boss.

---

## Settings desde Tray Manager

El tray provider no accede directamente a los archivos del módulo.

Utiliza mensajes:

    settings_get
    settings_set

hacia el Tray Manager.

El Tray Manager autentica el owner del tray antes de permitir acceso a settings.

Esto demuestra que distintos frontends de un mismo módulo pueden utilizar la misma fuente persistente sin compartir acceso directo al filesystem.

---

## UI del módulo

La UI actual está implementada con Tkinter exclusivamente para mantener la prueba pequeña y fácil de ejecutar.

No es una recomendación tecnológica para módulos reales.

La UI descubre los comandos leyendo:

    contracts/commands.json

No contiene una lista hardcodeada paralela.

Por cada comando muestra:

- el comando completo;
- un botón de ejecución;
- stdout;
- stderr;
- exit code.

La UI ejecuta siempre:

    neebles test-module <command>

Es decir, incluso estando dentro del propio módulo, vuelve a atravesar Boss.

Eso es intencional.

La UI no invoca funciones internas de `runtime.py`.

Así se comprueba el recorrido real que utilizaría cualquier cliente externo.

---

## External

El comando:

    neebles test-module external

existe exclusivamente para validar la ruta de diagnósticos External.

El runtime genera deliberadamente un mensaje `error` sin `id`.

Boss interpreta ese mensaje como un error espontáneo del runtime.

Boss puede construir entonces un evento External de tipo error.

La ruta conceptual es:

    test-module
        ->
    Module IPC
        ->
    Boss
        ->
    External boundary

El módulo no implementa transporte remoto.

El módulo tampoco decide si el evento puede salir del sistema.

---

## Telemetry

Telemetry pertenece a Boss.

El módulo no puede habilitarla.

El módulo sólo puede producir un evento que potencialmente alcance External.

La autoridad global es:

    telemetry.enabled

Por diseño:

    Telemetry OFF
        ->
    Boss bloquea la transmisión External

    Telemetry ON
        ->
    Boss permite que el evento atraviese la frontera External configurada

El test-module nunca modifica ese setting.

Eso es importante porque un módulo no debe poder concederse a sí mismo permiso para transmitir datos fuera del sistema.

---

## External no significa transporte remoto implementado

La prueba `external` valida que el módulo puede producir correctamente un evento hacia la frontera External de Boss.

No implica que exista actualmente un transporte remoto productivo configurado.

Boss conserva la autoridad sobre cualquier transporte futuro.

Esto mantiene separadas dos responsabilidades:

- producir un evento External;
- transportar ese evento a infraestructura remota.

---

## Notificaciones

El módulo utiliza:

    neebles notify

para demostrar que puede apoyarse en servicios transversales de Boss.

Las cadenas visibles del runtime se obtienen desde los archivos de idiomas del módulo.

Actualmente se soportan:

- `es_CL`;
- `en_US`.

El idioma solicitado puede llegar mediante:

    NEEBLES_LANGUAGE

El módulo normaliza variantes con locale y fallback al idioma default.

---

## `test-module.sh`

`test-module.sh` es el entrypoint declarado en el manifest.

Tiene tres responsabilidades simples.

Cuando el caller es Tray Manager:

    NEEBLES_CALLER=tray-manager

ejecuta el tray provider.

Cuando recibe:

    open

ejecuta el runtime persistente.

Cuando recibe:

    default

muestra información mínima del módulo.

Toda la funcionalidad dinámica moderna viaja por contratos de Boss, no por una lista creciente de casos Bash.

---

## Por qué el runtime no es un daemon independiente

El módulo podría implementar un daemon propio, pero eso debilitaría la prueba.

Queremos comprobar que el lifecycle gobernado por Boss es suficiente.

Boss conoce:

- qué módulo está instalado;
- qué comando abre el runtime;
- qué proceso está vivo;
- qué sesión se registró;
- qué endpoints declaró;
- cómo detenerlo.

El módulo conserva libertad interna detrás de ese contrato.

---

## Por qué el módulo usa Python

Python fue elegido por velocidad de iteración y legibilidad.

No existe ninguna dependencia arquitectónica de Boss hacia Python.

La misma implementación podría reemplazarse por:

- Rust;
- Go;
- Node.js;
- C++;
- otro lenguaje.

Mientras se mantengan:

- manifest;
- contratos;
- protocolos;
- framing;
- identidad;
- lifecycle;
- settings;
- subscriptions;

Boss no debería requerir cambios.

Esa posibilidad de reemplazo es una de las cosas que este módulo pretende demostrar.

---

## Motivación arquitectónica

N.E.E.B.L.E.S. busca evitar que el orquestador se transforme en una colección de excepciones especiales.

Boss no debe aprender cómo trabaja cada módulo.

Debe aprender a exigir contratos.

El test-module funciona como prueba continua de esa idea.

Cuando Boss incorpora una capacidad transversal nueva, hay una pregunta útil:

> ¿puede `neebles-test-module` utilizarla sin agregar lógica específica dentro de Boss?

Si la respuesta es sí, la frontera arquitectónica probablemente está bien ubicada.

Si la respuesta requiere que Boss conozca detalles privados del módulo, la abstracción debe revisarse.

---

## Bondades de mantener un módulo canónico de referencia

Tener este repositorio separado aporta varias ventajas.

### 1. Contrato observable

La documentación de Boss puede describir una API, pero este módulo demuestra cómo consumirla realmente.

### 2. Evita acoplamiento accidental

Si una función sólo puede utilizarse desde código interno de Boss, este módulo lo revela rápidamente.

### 3. Facilita regresiones

Después de modificar Boss se puede reinstalar o actualizar este módulo y comprobar si continúa funcionando.

### 4. Sirve como ejemplo para futuros módulos

Un desarrollador no necesita copiar internals de Boss.

Puede observar:

- manifest;
- contracts;
- runtime;
- tray;
- settings;
- subscriptions.

### 5. Obliga a separar autoridad

El módulo prueba que determinadas responsabilidades pertenecen a Boss:

- instalación;
- dependencia;
- settings persistentes;
- aislamiento;
- lifecycle;
- Telemetry.

Mientras otras pertenecen al módulo:

- comportamiento;
- UI;
- significado de settings;
- lógica del endpoint.

### 6. Reduce rutas especiales

Cuanto más pueda validarse mediante este módulo, menos razones existen para introducir caminos ad hoc dentro de Boss.

---

## Flujo completo esperado

Una integración real puede resumirse así:

    registry
        ->
    Boss instala test-module
        ->
    Boss valida manifest
        ->
    Boss resuelve dependencias
        ->
    Boss carga contracts
        ->
    usuario ejecuta neebles test-module open
        ->
    Boss inicia lifecycle tracked
        ->
    runtime conecta modules.sock
        ->
    runtime Register
        ->
    Boss valida identidad + endpoints
        ->
    Boss Registered
        ->
    runtime Subscribe
        ->
    Boss Subscribed
        ->
    UI abre
        ->
    usuario ejecuta comandos
        ->
    Boss Invoke
        ->
    runtime Response
        ->
    settings / events / notifications / External
        ->
    cierre UI
        ->
    Unregister
        ->
    Boss retira runtime del registry

Ese recorrido es el propósito central de este repositorio.

---

## Qué debe certificar una prueba integrada

La certificación integrada con Boss debe comprobar, al menos:

1. instalación o actualización del módulo;
2. resolución de `python3` y `python3-tk`;
3. preservación de settings compatibles;
4. apertura mediante launcher;
5. registro del runtime;
6. aceptación del protocolo;
7. aceptación de endpoints;
8. subscriptions;
9. `version`;
10. `hello`;
11. `notify`;
12. `state`;
13. lectura de settings;
14. escritura de settings;
15. evento `settings.test-module`;
16. recepción de `module.lifecycle`;
17. tray provider;
18. persistencia entre cierre y reapertura;
19. productor External;
20. autoridad Telemetry de Boss;
21. shutdown/unregister;
22. reinstalación;
23. actualización;
24. uninstall con y sin preservación de settings.

---

## Relación con N.E.E.B.L.E.S. OS

El módulo no depende de una personalización privada de N.E.E.B.L.E.S. OS.

Depende de los contratos públicos que Boss ofrece dentro del ecosistema.

En una certificación integrada, N.E.E.B.L.E.S. OS aporta el entorno real donde deben coexistir:

- Boss;
- servicios;
- sockets;
- ownership;
- dependencias;
- registry;
- módulos;
- settings;
- tray;
- UI.

El módulo permite recorrer esa integración desde el punto de vista de un consumidor externo.

---

## Versionado

La versión actual es:

    1.2.0

La versión `1.2.0` representa la alineación con los contratos persistentes actuales de Boss 1.0.7:

- subscriptions;
- module lifecycle events;
- module settings IPC;
- settings event isolation;
- External producer path;
- descubrimiento dinámico de endpoints.

Cambios futuros del módulo deben aumentar su versión cuando modifiquen el contrato o comportamiento observable utilizado para certificación.

---

## Principio final

`neebles-test-module` debe permanecer pequeño comparado con Boss.

Su valor no está en tener muchas funciones.

Su valor está en recorrer correctamente las fronteras importantes.

Si mañana cambia completamente su implementación interna pero sigue funcionando sin modificar Boss, entonces el contrato está cumpliendo su propósito.

Ese es el rol del módulo dentro de N.E.E.B.L.E.S.:

> ser una implementación externa suficientemente real para demostrar que Boss gobierna por contratos y no por conocimiento privado de sus módulos.
