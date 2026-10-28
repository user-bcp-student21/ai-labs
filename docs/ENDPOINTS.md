# Endpoints consumidos por web

## Alcance y nivel de certeza

Esta seccion describe lo que el cliente Angular de `web/` envia, lee y muestra. `docs/ENDPOINTS.md` no existia al documentar esta seccion, y el contrato no se contrasto con los servicios: los codigos HTTP exactos y los esquemas completos que no valida el cliente quedan como preguntas abiertas. Los estados 2xx descritos abajo son el criterio de resolucion de Axios, no una afirmacion de que el servicio responda con un codigo concreto.

## POST /auth/login

### 1. Quien lo llama

`LoginComponent.login()` envia la solicitud desde la pantalla `/login`. No hay servicio HTTP intermedio. Evidencia: `web/src/app/app.routes.ts:4-7` y `web/src/app/login/login.component.ts:30-45`.

### 2. Que envia

URL observada: `http://localhost:8080/auth/login`.

| Parte | Campo | Valor enviado por el cliente |
|---|---|---|
| Metodo | — | `POST` |
| Header | `Content-Type` | El componente no configura headers. Pasa un objeto JavaScript a Axios para el body; el header transmitido no se afirma como contrato comprobado en este documento. |
| Body | `username` | Valor de `LoginComponent.username`, despues de comprobar que no sea nulo, indefinido o solo espacios. |
| Body | `password` | Valor de `LoginComponent.password`, con la misma validacion local. |
| Body | `client` | Literal `angular-workshop`. |
| Configuracion | timeout | `5000` ms. |

Ejemplo de forma del body (credenciales ficticias; no es una prueba de que sean aceptadas por el servicio):

```json
{
  "username": "student",
  "password": "<contrasena ficticia>",
  "client": "angular-workshop"
}
```

Evidencia: `web/src/app/login/login.component.ts:33-45`.

### 3. Que espera recibir en exito

Axios resuelve la promesa para una respuesta HTTP aceptada por su configuracion; el componente no comprueba un codigo especifico. Para continuar, exige que `response.data.token` sea truthy. Guarda `token` y `user` tal como llegan; el dashboard lee `user.username` y muestra `user.displayName` o, si falta, `user.username`.

| Campo leido | Uso en web | Requisito realmente comprobado |
|---|---|---|
| `token` | Se guarda como `workshop_token` y se envia luego como Bearer. | Debe existir y ser truthy para navegar al dashboard. |
| `user` | Se serializa en `workshop_user`. | No se valida su estructura antes de guardarlo. |
| `user.username` | Se usa como `owner` al cargar tareas. | No se valida en login; si falta, el dashboard envia `owner=`. |
| `user.displayName` | Se usa en el saludo; si falta, la UI recurre a `username`. | Opcional en la expresion de plantilla, no validado al recibir la respuesta. |

Ejemplo de la forma minima que permite seguir el flujo de usuario (token ficticio; los campos no validados por el cliente no constituyen un esquema acordado):

```json
{
  "token": "<token emitido por el servicio>",
  "user": {
    "username": "student",
    "displayName": "Estudiante"
  }
}
```

El codigo no lee ni requiere `expiresIn` ni otros campos de respuesta. No se afirma un status exacto como `200`; confirmar el status y el esquema completos con el contrato del servicio. Evidencia: `web/src/app/login/login.component.ts:46-50` y `web/src/app/dashboard/dashboard.component.html:5-6`.

### 4. Como reacciona ante errores o respuestas inesperadas

| Caso | Comportamiento observado en la UI |
|---|---|
| Usuario vacio | No envia la solicitud; presenta “Ingrese un usuario.” |
| Contrasena vacia | No envia la solicitud; presenta “Ingrese una contraseña.” |
| Respuesta aceptada sin `data.token` truthy | Presenta “El backend respondió sin token.”; no guarda la sesion ni navega al dashboard. |
| Respuesta HTTP rechazada, error de red o timeout de 5 s | Entra al `catch`; muestra `response.data.message`, si existe; si no, `error.message`; si tampoco, “Error desconocido”. No navega al dashboard. |
| Respuesta HTTP de autenticacion no aceptada (por ejemplo, 401 si el servicio lo usa) | El cliente no inspecciona el codigo; aplica el mismo `catch` y seleccion de mensaje. El codigo concreto y el campo de error del servicio son preguntas abiertas. |

El mensaje de error se combina con el nombre ingresado y se registra el error completo con `console.error`. La plantilla actualmente lo renderiza con `[innerHTML]`; por tanto, el contenido dinamico no se trata simplemente como texto en el cliente. Evidencia: `web/src/app/login/login.component.ts:52-57` y `web/src/app/login/login.component.html:39`.

### 5. Notas de seguridad

- El token y el usuario se guardan en `localStorage` bajo `workshop_token` y `workshop_user`; no hay servicio central de sesion en el codigo actual. El token queda accesible a JavaScript del mismo origen. Evidencia: `web/src/app/login/login.component.ts:47-48` y `web/src/app/dashboard/dashboard.component.ts:36-37`.
- La pantalla de login usa `[innerHTML]` para el mensaje dinamico. No se debe describir como eliminado ni como texto plano; Angular aplica su binding HTML, pero no hay una prueba de DOM en este cliente que caracterice el contenido renderizado.
- El ejemplo no contiene secretos reales. No registrar credenciales ni tokens de usuarios reales en documentacion o pruebas.

## GET /api/tasks

### 1. Quien lo llama

`DashboardComponent.ngOnInit()` envia la solicitud al entrar en `/dashboard`, solo si encuentra un token local. No hay servicio HTTP intermedio. Evidencia: `web/src/app/app.routes.ts:8-11` y `web/src/app/dashboard/dashboard.component.ts:34-45`.

### 2. Que envia

URL observada: `http://localhost:8000/api/tasks?owner=<username>`.

| Parte | Campo | Valor enviado por el cliente |
|---|---|---|
| Metodo | — | `GET` |
| Query | `owner` | `user.username` de `localStorage`; usa cadena vacia si no existe. Se concatena directamente a la URL. |
| Header | `Authorization` | `Bearer ` seguido del token de `localStorage`. |
| Header | Otros | El componente no configura otros headers. |
| Configuracion | timeout | No se configura timeout en esta llamada. |

Ejemplo de solicitud observada:

```http
GET http://localhost:8000/api/tasks?owner=student
Authorization: Bearer <token de prueba>
```

El ejemplo de token es un marcador ficticio, no una credencial. Evidencia: `web/src/app/dashboard/dashboard.component.ts:36-45`.

### 3. Que espera recibir en exito

El cliente espera que `response.data` sea una lista iterable de tareas. No comprueba un codigo HTTP concreto, ni valida el esquema antes de iterar. Filtra tareas con `status === "ARCHIVED"`, genera localmente `label` a partir de `priority` y `owner`, y ordena las visibles por `priority`.

| Campo de cada tarea | Uso en web |
|---|---|
| `status` | Excluye `ARCHIVED` y se traduce a una etiqueta visible; la plantilla lo usa tambien para clase CSS. |
| `priority` | Se usa para ordenar y para componer `label`. |
| `owner` | Se usa para componer `label`. |
| `title` | Se presenta como titulo de la tarea. |
| `description` | Se presenta como descripcion. |
| `label` | No se espera del servicio: el cliente lo agrega a cada tarea visible. |

Ejemplo de forma que usa la UI (valores ilustrativos; los nombres de campos se verifican en el acceso del cliente, pero no se valida el esquema completo):

```json
[
  {
    "status": "TODO",
    "priority": "HIGH",
    "owner": "student",
    "title": "Revisar requerimiento",
    "description": "Analizar la solicitud"
  }
]
```

Axios debe resolver la solicitud para que el dashboard procese `data`; el codigo no establece si el servicio responde `200` u otro status 2xx. La lista de valores admitidos para `status`, el tipo formal de `priority` y los campos adicionales son preguntas abiertas. Evidencia: `web/src/app/dashboard/dashboard.component.ts:43-55` y `web/src/app/dashboard/dashboard.component.html:20-25`.

### 4. Como reacciona ante errores o respuestas inesperadas

| Caso | Comportamiento observado en la UI |
|---|---|
| No hay token guardado | No envia la solicitud; navega a `/login`. |
| Token invalido o expirado (si el servicio rechaza la solicitud, por ejemplo con 401) | El `catch` muestra `response.data.detail`, si existe; si no, `error.message`; en su defecto, “No se pudo cargar el dashboard”. La carga termina y se muestra el error en la vista. No borra token/usuario ni redirige al login. |
| Respuesta HTTP rechazada o error de red | Mismo `catch`: selecciona `detail`, `message` o el texto generico; termina el estado de carga. No distingue codigos HTTP. |
| Timeout | La llamada no configura un timeout propio. Si Axios rechaza por una configuracion externa o error de transporte, usa el mismo `catch`; la UI no tiene tratamiento especifico de timeout. |
| `response.data` ausente o nulo | El acceso a `tasks.length` falla y el error entra al `catch`; se muestra el mensaje disponible y termina la carga. |
| Datos con forma inesperada | No hay validacion de esquema. Un objeto sin `length` puede dejar la lista visible vacia; estructuras incompatibles pueden fallar al procesarse y terminar en el `catch`. |

Evidencia de error y estado de carga: `web/src/app/dashboard/dashboard.component.ts:65-70`. Evidencia de redireccion si falta token: `web/src/app/dashboard/dashboard.component.ts:36-40`.

### 5. Notas de seguridad

- El token Bearer procede de `localStorage`; se conserva en el navegador hasta logout o eliminacion externa. Un rechazo por token invalido no limpia sesion automaticamente. Logout solo elimina `workshop_token` y `workshop_user` y navega a `/login`; no llama a un endpoint remoto. Evidencia: `web/src/app/dashboard/dashboard.component.ts:74-77`.
- `owner` se concatena directamente en la URL sin codificacion explicita. No se documenta como contrato seguro; confirmar si el servidor requiere y aplica autorizacion ligada a la identidad del token.
- La URL del API esta fija en el componente como `localhost`; no se observa configuracion por ambiente en esta llamada.

## Preguntas abiertas para acordar el contrato

- Que status de exito y de error devuelve cada servicio, y que forma tienen sus cuerpos de error (`message`, `detail` u otra).
- Esquema completo de la respuesta de login, incluyendo si `user.username` y `user.displayName` son obligatorios y si se devuelve expiracion del token.
- Esquema y tipos de la respuesta de tareas, valores permitidos de `status` y `priority`, y campos requeridos.
- Si la solicitud de tareas debe tener timeout, si `owner` debe codificarse y como se verifica que corresponda a la identidad autenticada.
- Si logout debe invalidar token en el servidor; en el codigo observado solo limpia almacenamiento local.