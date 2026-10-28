# Hallazgos

## web

### Flujo observado (no contrastado con contrato acordado)

`docs/ENDPOINTS.md` no existe. El codigo de `web/` muestra este flujo: el login envia `POST http://localhost:8080/auth/login` con `username`, `password` y `client`; si la respuesta incluye token, guarda token, usuario y preferencias en `localStorage` y navega a `/dashboard`. El dashboard lee token y usuario; sin token navega a `/login`. Con token, consulta `GET http://localhost:8000/api/tasks?owner=<username>` con `Authorization: Bearer <token>`. Al cerrar sesion elimina token y usuario, conserva preferencias y vuelve a `/login`. Este es comportamiento observado en el cliente, no un contrato acordado ni verificado contra los servicios.

### Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-WEB-01 | web | Token de sesion almacenado en `localStorage` | Vulnerabilidad | El token queda accesible a JavaScript del mismo origen; una vulnerabilidad de script en la aplicacion podria exponerlo. El riesgo esta confirmado por el almacenamiento, no se ha demostrado robo ni impacto en un servicio. | web/src/app/login/login.component.ts:47; web/src/app/dashboard/dashboard.component.ts:36,75 | media | Pendiente |
| H-WEB-02 | web | Mensaje dinamico renderizado con `[innerHTML]` | Vulnerabilidad | El mensaje incorpora el nombre ingresado y un mensaje de error antes de renderizarse como HTML. Angular sanitiza este binding; no se comprobo una explotacion, pero conviene separar texto y marcado para evitar depender de contenido dinamico en un sink HTML. | web/src/app/login/login.component.ts:56; web/src/app/login/login.component.html:39 | baja | Pendiente |
| H-WEB-03 | web | Componentes mezclan HTTP, sesion y navegacion | Refactor | Login y dashboard hacen llamadas HTTP, acceden a `localStorage` y navegan directamente. Esto duplica responsabilidades y dificulta probar o cambiar el flujo sin acoplar componentes a transporte y sesion. | web/src/app/login/login.component.ts:5,41-50; web/src/app/dashboard/dashboard.component.ts:5,36-43,74-77 | baja | Pendiente |
| H-WEB-04 | web | Tipado `any` y validacion anidada | Refactor | `any` en estado, respuestas y errores debilita la comprobacion de tipos; la validacion anidada de usuario y contrasena dificulta seguir los caminos de error. La duplicacion mencionada por RETO no se confirma en el flujo revisado. | web/src/app/login/login.component.ts:16-20,33-46,54; web/src/app/dashboard/dashboard.component.ts:23-27,43-54,65; web/src/app/utils/legacy-format.ts:1 | baja | Pendiente |
| H-WEB-05 | web | Dependencias candidatas a auditoria SCA | Sugerencia | `axios` y `lodash` estan declaradas en las versiones que RETO pide investigar. Sin ejecutar auditoria de dependencias no se confirma una CVE, su aplicabilidad ni una vulnerabilidad explotable. | web/package.json:19-20 | baja | Pendiente |
| H-WEB-06 | web | Pruebas cubren solo una utilidad | Refactor | El inventario encontrado contiene un unico spec con un caso para `formatTaskLabel`; no hay caracterizacion de login, persistencia del token, carga del dashboard ni cierre de sesion. No se ejecuto la suite ni se midio cobertura. | web/src/app/utils/legacy-format.spec.ts:4-7 | baja | Pendiente |
| H-WEB-07 | web | Duplicacion de logica indicada por RETO | Sugerencia | No se encontro un bloque de logica repetido que permita confirmar este candidato en el flujo revisado; la separacion de responsabilidades y el uso de `any` si estan respaldados por las filas anteriores. | web/src/app/login/login.component.ts:32-60; web/src/app/dashboard/dashboard.component.ts:32-78 | baja | No encontrado |

### Evidencia pendiente

- `docs/ENDPOINTS.md` no existe; falta contrastar el flujo observado con el contrato acordado.
- La suite de pruebas con cobertura no se ejecuto porque se omitio la llamada a la herramienta. No hay resultado de pruebas ni porcentaje de cobertura registrado.
- No se ejecuto auditoria SCA; estado de advisories y aplicabilidad pendientes.

### Candidatos de discovery (web)

#### H-WEB-08 — El dashboard parsea el usuario almacenado fuera del manejo de errores
- Componente: `web`.
- Estado: `CANDIDATO`.
- Tipo: Bug.
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:37,41-42`.
- Impacto: si `workshop_user` contiene JSON invalido, `JSON.parse` puede rechazar `ngOnInit` antes de entrar al `try/catch`; no se ejecuta la ruta de redireccion por falta de token ni el estado de error del dashboard.
- Prioridad propuesta: media.
- Contrato potencialmente afectado: comportamiento de `/dashboard` cuando la sesion local esta corrupta; el comportamiento esperado para ese estado no esta acordado.
- Como validarlo: prueba unitaria con `workshop_user` malformado y verificaciones de rechazo/estado actual; acordar el comportamiento seguro esperado y probar que no quede una excepcion sin manejar.

#### H-WEB-09 — El valor de `owner` se concatena sin codificacion de query
- Componente: `web`.
- Estado: `CANDIDATO`.
- Tipo: Bug.
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:43`; el login solo comprueba que username no sea vacio en `web/src/app/login/login.component.ts:33-38`.
- Impacto: si un username permitido contiene caracteres reservados de URL, la concatenacion puede cambiar como se interpreta la query y el valor de `owner` recibido por el servicio.
- Prioridad propuesta: baja.
- Contrato potencialmente afectado: parametro `owner` de `GET /api/tasks`; el conjunto de caracteres permitidos para username no esta especificado en el codigo inspeccionado.
- Como validarlo: prueba con un username ficticio que contenga separadores de query, analiza la URL resultante con `URL`/`URLSearchParams` y confirma el contrato de caracteres permitidos antes de decidir el comportamiento esperado.

#### H-WEB-10 — La consulta de tareas no configura un timeout local
- Componente: `web`.
- Estado: `CANDIDATO`.
- Tipo: Bug.
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:25,43-45,65-70`; no se encontro configuracion de Axios global en `web/src/`.
- Impacto: si la solicitud queda pendiente sin resolverse ni rechazarse, `loading` permanece verdadero y la plantilla mantiene el estado de carga.
- Prioridad propuesta: media.
- Contrato potencialmente afectado: disponibilidad y tiempo de espera de `GET /api/tasks`; no hay timeout acordado para este endpoint.
- Como validarlo: revisar una prueba con transporte controlado que mantenga la promesa pendiente; si se acuerda un limite, verificar que la UI termine la carga y presente el error al vencerlo.
