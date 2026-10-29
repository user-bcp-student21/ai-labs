# Plan de remediacion

## web


### Aprobacion huamana
- Karen
- 2026/10/26
- H-WEB-01, H-WEB-02, H-WEB-03, H-WEB-04, H-WEB-05, H-WEB-06


### Alcance y seleccion

Se proponen cambios para `H-WEB-01` y `H-WEB-02`, ambos existentes y en estado `Pendiente` en `HALLAZGOS.md`. Se seleccionan por ser los dos hallazgos de seguridad de mayor prioridad disponibles en la matriz; `H-WEB-01` tiene severidad media y `H-WEB-02` baja. No se cambia el estado de los hallazgos ni se afirma aprobacion humana.

`docs/ENDPOINTS.md` no existe. Se preservara el comportamiento observado: `POST http://localhost:8080/auth/login` con `username`, `password` y `client`; al recibir token, ir a `/dashboard`; consultar `GET http://localhost:8000/api/tasks?owner=<username>` con `Authorization: Bearer <token>`; y cerrar sesion y volver a `/login`. Evidencia actual: `web/src/app/login/login.component.ts:41-50` y `web/src/app/dashboard/dashboard.component.ts:36-43,74-77`. El token y el usuario se guardan hoy en `localStorage` (`web/src/app/login/login.component.ts:47-48`) y el dashboard los lee de ahi (`web/src/app/dashboard/dashboard.component.ts:36-37`).

### H-WEB-01 — Token de sesion en localStorage

- **Hallazgo:** `HALLAZGOS.md`, `H-WEB-01`, Vulnerabilidad, severidad media, estado `Pendiente`.
- **Problema:** el token persiste en `localStorage` y es legible por scripts del mismo origen. En el alcance solo frontend no se puede convertirlo en cookie `HttpOnly` sin soporte y contrato del backend.
- **Cambio propuesto:** crear un servicio de estado del navegador que centralice el acceso a almacenamiento desde login y dashboard. Guardar token y usuario en `sessionStorage`, manteniendo preferencias en `localStorage`; el servicio mantiene la gestion de ambas areas para que los componentes no accedan directamente a `localStorage` o `sessionStorage`. Conservar endpoints, request, respuesta consumida, header Bearer, navegacion y limpieza de sesion. Esto reduce la persistencia entre sesiones del navegador, pero no evita que JavaScript del mismo origen lea el token; registrar ese riesgo residual. `sessionStorage` conserva el estado al recargar la misma pestana, pero no al cerrar la sesion del navegador, por lo que ese cambio de duracion requiere aceptar explicitamente el comportamiento.
- **Archivos a tocar despues de aprobar el plan:** crear `web/src/app/services/browser-state.service.ts`; modificar `web/src/app/login/login.component.ts` y `web/src/app/dashboard/dashboard.component.ts`; crear pruebas en `web/src/app/login/login.component.spec.ts` y `web/src/app/dashboard/dashboard.component.spec.ts`.
- **Caracterizacion antes de tocar codigo de produccion:** con Axios y Router simulados y almacenamiento ficticio, comprobar login exitoso (token y usuario guardados, preferencias preservadas y navegacion a dashboard), dashboard sin token (navega a login), consulta con token (mismo endpoint, owner y header Bearer) y logout (borra token/usuario, conserva preferencias y navega a login). Ejecutar primero contra la implementacion actual; despues adaptar las aserciones de almacenamiento a `sessionStorage` y repetirlas.
- **Riesgo/pendiente:** decidir si se acepta que cerrar el navegador requiera autenticarse de nuevo. Una cookie `HttpOnly` seria una mitigacion mas fuerte frente a lectura desde JavaScript, pero queda fuera del alcance porque no hay contrato acordado ni cambio de backend autorizado.

### H-WEB-02 — Mensaje dinamico renderizado con innerHTML

- **Hallazgo:** `HALLAZGOS.md`, `H-WEB-02`, Vulnerabilidad, severidad baja, estado `Pendiente`.
- **Problema:** el componente arma un string que mezcla nombre de usuario, mensaje del backend y etiquetas HTML (`web/src/app/login/login.component.ts:56`); la plantilla lo enlaza con `[innerHTML]` (`web/src/app/login/login.component.html:39`). Angular sanitiza este binding, por lo que no se da por demostrada una explotacion.
- **Cambio propuesto:** representar el mensaje como datos de texto (por ejemplo, titulo y detalle) y construir el formato con elementos estaticos en la plantilla e interpolacion Angular. Conservar los mensajes visibles de validacion, error de autenticacion y respuesta sin token, pero tratar cualquier texto del usuario o backend como texto, no como marcado HTML. No agregar dependencias.
- **Archivos a tocar despues de aprobar el plan:** modificar `web/src/app/login/login.component.ts` y `web/src/app/login/login.component.html`; ampliar `web/src/app/login/login.component.spec.ts`.
- **Caracterizacion antes de tocar codigo de produccion:** con Axios simulado, cubrir usuario/contrasena vacios, respuesta sin token y error del backend; comprobar que el mensaje conserva el contenido visible y que el nombre y el detalle recibidos se mantienen como datos. Agregar un caso con texto ficticio que contenga caracteres de marcado y comprobar que el contenido se conserva literalmente tras el cambio.
- **Riesgo/pendiente de verificacion:** `web/vitest.config.ts` configura `environment: 'node'`; no hay entorno DOM configurado para comprobar el HTML realmente renderizado. Las pruebas unitarias propuestas caracterizan el contenido del mensaje, pero no prueban el comportamiento del sanitizador o del DOM. Antes de exigir esa asercion automatizada, decidir si se habilita un entorno de pruebas de navegador/DOM; no se propone una dependencia nueva sin justificarla.

### Orden de trabajo propuesto

1. Crear y ejecutar las pruebas de caracterizacion descritas para ambos hallazgos, antes de modificar componentes o plantillas. Registrar resultado real asociado a `web` y a `H-WEB-01` / `H-WEB-02`.
2. Resolver la decision de duracion de sesion para `H-WEB-01`; implementar almacenamiento centralizado y migracion a `sessionStorage` solo si se acepta el cambio observado al cerrar el navegador.
3. Separar datos y marcado para `H-WEB-02`; mantener los textos funcionales y verificar el caso de contenido literal.
4. Ejecutar pruebas y build desde `web/`, revisar riesgos restantes y actualizar `HALLAZGOS.md` solo con evidencia real. No marcar como resuelto sin verificaciones y revision humana.

### Estado de evidencia

- `docs/ENDPOINTS.md` no existe; los endpoints y el flujo anteriores son observados en el cliente, no un contrato acordado.
- `web/src/app/login/login.component.spec.ts` y `web/src/app/dashboard/dashboard.component.spec.ts` contienen pruebas de caracterizacion para `H-WEB-01` y `H-WEB-02`, antes de cambios de produccion.
- Ejecucion de caracterizacion: `npm test` con cwd `web/` se ejecuto y pasó; el resultado real está en la actualizacion siguiente. Esta viñeta reemplaza la anotacion anterior de ejecucion pendiente.
- La aprobacion registrada arriba identifica a Karen, fecha 2026/10/26 e incluye `H-WEB-01` y `H-WEB-02`. Las frases anteriores que niegan la aprobacion quedan como texto desactualizado pendiente de reconciliar sin alterar el registro humano.
- No se modifico codigo de produccion. No se ejecuto build.
- Actualizacion (caracterizacion ejecutada, `web`, `H-WEB-01` / `H-WEB-02`):
  - Conflictos de merge de `web/src/app/auth-flow.spec.ts`, `web/src/app/login/login.component.spec.ts` y `web/src/app/dashboard/dashboard.component.spec.ts` resueltos conservando el lado `HEAD` (`sessionStorage`). Verificado: sin marcadores en `web/src`.
  - Comando: `npm test` desde `web/` (Vitest 3.2.4). Antes de añadir casos: 4 archivos, 16 pruebas, pasaron. Despues: 4 archivos, 17 pruebas, pasaron (2026-10-29, ejecución verificada a las 09:32:25).
  - Casos añadidos, solo en specs y sin cambios de produccion: login sin `token` no guarda sesion (`H-WEB-01`); el token no aparece como valor en `localStorage` tras login (criterio 1 de `H-WEB-01`); el dashboard no lee el token desde `localStorage` (criterio 2); logout con token heredado en ambos almacenes (criterio 4); logout seguido de reingreso no reutiliza la sesion (criterio 4, en `auth-flow.spec.ts`).
  - `H-WEB-02`: el caso `student <em>local</em>` en `login.component.spec.ts` solo verifica que el texto del usuario se conserva literal en la cadena del mensaje. No prueba el render en el DOM ni protege frente a XSS; no debe usarse como evidencia de cierre de `H-WEB-02`.
  - Hallazgo: el codigo actual guarda el token en `sessionStorage` (`web/src/app/session/session-token.ts`), no en `localStorage` como describen esta seccion, `HALLAZGOS.md` y `HU-01.md`. La lectura desde JavaScript del mismo origen sigue siendo posible; `H-WEB-01` permanece `Pendiente`.
  - Pendiente: aprobacion humana de la resolucion de conflictos (tarea 0.5 de `openspec/changes/reduce-web-token-persistence/tasks.md`). No se registro aprobacion nueva.
  - La ejecucion pendiente indicada arriba queda resuelta por este registro. No se ejecutaron build ni cobertura en este paso.