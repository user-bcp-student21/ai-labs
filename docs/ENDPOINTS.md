# Endpoints de ReqFlow

Este documento describe los contratos HTTP de cada componente. La sección de `api`
(FastAPI) está completa. Las secciones de `auth` y `web` se añaden en sus propios pasos y
no se han modificado aquí.

Cada respuesta de `api` se verificó contra el código de `api/` y, para los ejemplos, contra
una ejecución real de la aplicación con una base SQLite temporal. Los valores de fecha, `id`
y rutas de los ejemplos son los de esa ejecución; en otro entorno variarán.

## api

### Convenciones comunes

- **Base URL local:** `http://localhost:8000`. La documentación interactiva de FastAPI está en
  `http://localhost:8000/docs` (según `README.md`).
- **Autenticación:** todos los endpoints requieren el header exacto
  `Authorization: Bearer <token>`. El prefijo `Bearer ` distingue mayúsculas y minúsculas
  (`api/app/config.py:10`; `api/app/security.py:40-43`).
- **Token:** JWT firmado con HS256 usando la variable de entorno `WORKSHOP_JWT_SECRET`
  (`api/app/config.py:11`). Debe incluir los claims `exp`, `iat`, `sub` y `role`
  (`api/app/config.py:14`). El emisor debe ser `reqflow-auth` y la audiencia `reqflow-api`
  (`api/app/config.py:12-13`). La validación verifica firma, emisor, audiencia, expiración y
  presencia de claims (`api/app/security.py:46-58`).
- **Identidad:** el usuario de todas las operaciones es el claim `sub` del token verificado
  (`api/app/security.py:58`). El claim `role` se lee, pero hoy ningún endpoint lo usa para
  decidir autorización.
- **Formato de error:** los errores de negocio responden `{"detail": "<mensaje>"}`
  (`api/app/errors.py:12-13`). Los errores de validación de FastAPI/Pydantic responden una lista
  en `detail`, como en el ejemplo de `POST /api/tasks` más abajo.
- **Nombres de campos:** las respuestas usan `camelCase` (`createdAt`, `requestedBy`,
  `byStatus`, `highPriorityOpen`, `fileName`, `storedAt`). Las entradas de `POST /api/tasks` usan
  los nombres de `api/app/schemas.py`.
- **Fechas:** `createdAt` es texto con formato `YYYY-MM-DD HH:MM:SS`, generado por SQLite con
  `datetime('now')` (`api/app/repositories/tasks.py:8`). No incluye zona horaria.

---

### 1. `GET /api/tasks`

**Qué hace:** devuelve las tareas de un owner, ordenadas por `id` ascendente. Por defecto es el
usuario autenticado (`api/app/routes/tasks.py:14-18`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

**Request**

Parámetro de consulta:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string (query) | No | Si se envía, debe ser igual al `sub` del token. Si se omite o va vacío, se usa el `sub`. Otro valor responde 403. |

Sin cuerpo.

Ejemplo:

```http
GET /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Respuesta exitosa:** `200 OK`. Cuerpo: arreglo JSON de tareas (puede estar vacío).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. Puede ser vacía. |
| `status` | string | Uno de `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. |
| `owner` | string | Owner de la tarea (`sub` con el que se creó). |
| `priority` | string | Uno de `LOW`, `MEDIUM`, `HIGH`. |
| `createdAt` | string | Fecha de creación, `YYYY-MM-DD HH:MM:SS`. |

Ejemplo (capturado con el usuario `student`, que tiene dos tareas sembradas):

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:15:57"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:15:57"
  }
]
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Falta el prefijo `Bearer `, la firma no es válida, el token está vencido, el emisor o la audiencia no coinciden o falta un claim requerido. | `{"detail": "Invalid token"}` |
| 403 | `owner` se envía con un valor distinto al `sub` del token. | `{"detail": "Owner differs from the authenticated identity"}` |

Ejemplo 401 (capturado):

```json
{
  "detail": "Invalid token"
}
```

Ejemplo 403 (capturado con `?owner=trainer` usando el token de `student`):

```json
{
  "detail": "Owner differs from the authenticated identity"
}
```

**Notas de seguridad**

- La autorización depende del `sub` del token verificado. Un cliente no puede pedir tareas de
  otro owner: `owner` solo puede repetir su propia identidad, de lo contrario responde 403
  (`api/app/services/tasks.py:12-17`). Esto corrige el IDOR original de H-API-04.
- La consulta usa SQL parametrizado (`api/app/repositories/tasks.py:5`), corrigiendo H-API-01.
- Este endpoint no tiene paginación. La respuesta contiene todas las tareas del owner.

---

### 2. `POST /api/tasks`

**Qué hace:** crea una tarea para el usuario autenticado y la devuelve con su `id` y su fecha
de creación (`api/app/routes/tasks.py:20-23`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

**Request**

Cuerpo JSON (`Content-Type: application/json`), modelo `TaskCreate` de `api/app/schemas.py`:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | Sí | Título. Debe tener al menos 1 carácter. Un número no se acepta: responde 422. |
| `description` | string | No | Descripción. Por defecto `""`. |
| `status` | string (enum) | No | Uno de `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. Por defecto `TODO`. |
| `priority` | string (enum) | No | Uno de `LOW`, `MEDIUM`, `HIGH`. Por defecto `MEDIUM`. |
| `owner` | string o null | No | Si se envía, debe ser igual al `sub` del token. Si es `null`, se omite o va vacío, se usa el `sub`. Otro valor responde 403. |

Ejemplo:

```json
{
  "title": "Nueva tarea",
  "description": "Detalle",
  "status": "TODO",
  "priority": "HIGH"
}
```

**Respuesta exitosa:** `201 Created`. Cuerpo: la tarea creada.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador asignado por la base. |
| `title` | string | Título guardado. |
| `description` | string | Descripción guardada. |
| `status` | string | Estado guardado. |
| `owner` | string | Siempre el `sub` del token (o el `owner` enviado si coincide). |
| `priority` | string | Prioridad guardada. |
| `createdAt` | string | Fecha de creación, `YYYY-MM-DD HH:MM:SS`. |

Ejemplo (capturado):

```json
{
  "id": 4,
  "title": "Nueva tarea",
  "description": "Detalle",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:15:57"
}
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Igual que en `GET /api/tasks`. | `{"detail": "Invalid token"}` |
| 403 | `owner` del cuerpo es distinto al `sub` del token. | `{"detail": "Owner differs from the authenticated identity"}` |
| 422 | `title` vacío o ausente, `status` o `priority` fuera de los valores permitidos, o tipos incorrectos. | Lista de errores de validación (ver ejemplo). |

Ejemplo 422 (capturado con `title: ""` y `status: "NOPE"`):

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {"min_length": 1}
    },
    {
      "type": "enum",
      "loc": ["body", "status"],
      "msg": "Input should be 'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'",
      "input": "NOPE",
      "ctx": {"expected": "'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'"}
    }
  ]
}
```

Ejemplo 403 (capturado con `owner: "trainer"` usando el token de `student`):

```json
{
  "detail": "Owner differs from the authenticated identity"
}
```

**Notas de seguridad**

- El cliente no elige el owner. Si envía un `owner` distinto del `sub`, la petición se rechaza
  con 403 (`api/app/services/tasks.py:12-17`). Antes, el valor del cliente se guardaba tal cual
  (H-API-04).
- Los datos llegan validados por Pydantic antes de tocar la base (`api/app/schemas.py`). Un
  `status` o `priority` desconocido responde 422 (H-API-11).
- El 422 de validación repite en `input` el valor enviado. Esto está registrado como
  sugerencia pendiente y no es un error de contrato.

---

### 3. `GET /api/summary`

**Qué hace:** resume las tareas de un owner: total, conteo por estado y número de tareas de
prioridad `HIGH` que siguen abiertas (`api/app/services/tasks.py:31-39`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

**Request**

Parámetro de consulta:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string (query) | No | Igual que en `GET /api/tasks`: si se envía, debe ser el `sub` del token; otro valor responde 403. |

Sin cuerpo.

**Respuesta exitosa:** `200 OK`. Cuerpo: objeto con el resumen.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Owner resumido (el `sub` del token). |
| `total` | integer | Número de tareas del owner. |
| `byStatus` | objeto | Clave: estado. Valor: cantidad de tareas en ese estado. Solo aparecen los estados con al menos una tarea. |
| `highPriorityOpen` | integer | Tareas con `priority = HIGH` y `status` distinto de `DONE` y `ARCHIVED`. |

Ejemplo (capturado con el usuario `student`):

```json
{
  "owner": "student",
  "total": 3,
  "byStatus": {
    "TODO": 2,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 2
}
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Igual que en `GET /api/tasks`. | `{"detail": "Invalid token"}` |
| 403 | `owner` se envía con un valor distinto al `sub` del token. | `{"detail": "Owner differs from the authenticated identity"}` |

Ejemplo 403 (capturado con `?owner=trainer` usando el token de `student`):

```json
{
  "detail": "Owner differs from the authenticated identity"
}
```

**Notas de seguridad**

- Igual que `GET /api/tasks`: el resumen solo cubre la identidad del token (H-API-04).
- El resumen cuenta por SQL parametrizado (`api/app/repositories/tasks.py:7`).

---

### 4. `POST /api/requirements`

**Qué hace:** guarda un archivo de requisitos (`.txt` o `.md`) en el directorio de subidas del
servidor y devuelve el nombre final y el tamaño (`api/app/routes/requirements.py:14-22`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

**Request**

Cuerpo `multipart/form-data`:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | Archivo a guardar. La extensión (sin distinguir mayúsculas) debe ser `.txt` o `.md`. Tamaño máximo: 1 MiB (1 048 576 bytes). |

El nombre se normaliza: solo se conserva la última parte de la ruta. Por ejemplo,
`../requisitos.md` se guarda como `requisitos.md` (`api/app/services/files.py:28-32`). Los
nombres `""`, `.` o `..` se rechazan.

Ejemplo (`curl`):

```bash
curl -X POST http://localhost:8000/api/requirements \
  -H "Authorization: Bearer <token>" \
  -F "file=@requisitos.md;type=text/markdown"
```

**Respuesta exitosa:** `201 Created`. Cuerpo: resultado del guardado.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario que subió el archivo (el `sub` del token). |
| `fileName` | string | Nombre final guardado, ya normalizado. |
| `storedAt` | string | Ruta absoluta donde quedó guardado en el servidor. |
| `size` | integer | Tamaño del contenido en bytes. |

Ejemplo (capturado; `storedAt` depende del directorio de subidas del entorno):

```json
{
  "owner": "student",
  "fileName": "requisitos.md",
  "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\tmp6mqyx36f\\up\\requisitos.md",
  "size": 6
}
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Igual que en `GET /api/tasks`. | `{"detail": "Invalid token"}` |
| 409 | Ya existe un archivo con ese nombre en el directorio de subidas (compartido por todos los owners). | `{"detail": "A file with this name already exists"}` |
| 413 | El contenido supera 1 MiB. | `{"detail": "File exceeds the upload size limit"}` |
| 422 | El nombre normalizado está vacío, es `.` o `..`, o la extensión no es `.txt` ni `.md`. | `{"detail": "File name or extension is not allowed"}` |

Ejemplo 409 (capturado con el mismo nombre dos veces):

```json
{
  "detail": "A file with this name already exists"
}
```

Ejemplo 422 (capturado con `a.exe`):

```json
{
  "detail": "File name or extension is not allowed"
}
```

Ejemplo 413 (capturado con 1 MiB + 1 byte):

```json
{
  "detail": "File exceeds the upload size limit"
}
```

**Notas de seguridad**

- El nombre nunca se usa tal cual: se normaliza y se limita a `.txt` o `.md`
  (`api/app/services/files.py:28-32`). Esto corrige la path traversal de H-API-02.
- El tamaño se verifica leyendo como máximo 1 MiB + 1 byte (`api/app/routes/requirements.py:18`),
  para no cargar un archivo grande en memoria.
- La escritura usa creación exclusiva (`api/app/services/files.py:21`, `open("xb")`); un nombre repetido responde 409 y no
  sobrescribe el archivo anterior.
- El campo `storedAt` expone la ruta absoluta del servidor. Esto es un riesgo pendiente
  (ver sección de riesgos).
- Los archivos no están separados por owner: todos los usuarios comparten el directorio de
  subidas. Esto es una pregunta abierta.

---

### 5. `GET /api/backend-health`

**Qué hace:** consulta el endpoint de salud del servicio de autenticación y devuelve su
respuesta junto con el usuario que hizo la consulta (`api/app/routes/health.py:11-18`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

**Request**

Sin parámetros ni cuerpo. La URL de la consulta sale de la variable de entorno
`AUTH_HEALTH_URL`; si no existe, se usa `http://localhost:8080/q/health`
(`api/app/config.py:8`). El cliente no puede cambiar esa URL.

**Respuesta exitosa:** `200 OK`. Cuerpo: resultado de la consulta upstream.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario que hizo la consulta (el `sub` del token). |
| `status` | integer | Código HTTP que respondió el servicio upstream. Puede ser distinto de 200; la respuesta del endpoint sigue siendo 200. |
| `body` | string | Cuerpo del upstream decodificado como UTF-8, con caracteres inválidos reemplazados. Es texto, no JSON parseado. |

Ejemplo (capturado con un servicio de prueba local que responde 200):

```json
{
  "requestedBy": "student",
  "status": 200,
  "body": "{\"status\":\"UP\",\"checks\":[]}"
}
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Igual que en `GET /api/tasks`. | `{"detail": "Invalid token"}` |
| 502 | El upstream no es alcanzable o la consulta falla (incluye timeout de 3 segundos). | `{"detail": "Backend health endpoint is unreachable"}` |

Ejemplo 502 (capturado con `AUTH_HEALTH_URL` apuntando a un puerto cerrado):

```json
{
  "detail": "Backend health endpoint is unreachable"
}
```

**Notas de seguridad**

- El cliente no puede elegir la URL de la consulta: evita usar la API como proxy hacia destinos
  arbitrarios (SSRF).
- Un error de red responde 502 con un mensaje genérico. El detalle de la excepción no sale al
  cliente (`api/app/services/health.py:11-12`).
- El cuerpo del upstream se devuelve completo y sin límite de tamaño. Esto es un riesgo
  pendiente.

---

## Contrato observado, contrato acordado y riesgos pendientes

**Contrato observado.** Lo que hace el código actual y lo descrito arriba.

**Contrato acordado.** Cambios aprobados en `prompts/PLAN.md` y ya reflejados en el código:

- Token legado Base64 → 401. Antes era aceptado.
- `owner` distinto del `sub` → 403 en `GET /api/tasks`, `GET /api/summary` y `POST /api/tasks`.
  Antes el cliente elegía el owner.
- Backend inalcanzable → 502 con mensaje genérico. Antes había un 5xx con detalle.
- Título numérico, `status` o `priority` desconocidos y título vacío → 422.
- `POST /api/requirements`: nombre normalizado, solo `.txt`/`.md`, máximo 1 MiB, 409 si existe.

**Riesgos pendientes** (registrados en `prompts/HALLAZGOS.md` y `prompts/PLAN.md`):

- **CORS (H-API-08, pendiente de revisión humana):** los orígenes permitidos salen de
  `WORKSHOP_CORS_ORIGINS` (lista separada por comas; `*` se rechaza al arrancar). Si falta o está
  vacía se usan `http://localhost:4200` y `http://127.0.0.1:4200`, solo para desarrollo. Un origen
  no listado no recibe `access-control-allow-origin` (el preflight responde 400). Starlette sigue
  añadiendo `access-control-allow-credentials` a esa respuesta 400. Falta definir la variable en
  `compose.yaml` y comprobar el efecto en un navegador real.
- **Formato del JWT:** el emisor y la audiencia (`reqflow-auth` y `reqflow-api`) y el secreto
  compartido deben coincidir con `auth/`. No se verificó contra `auth/`.
- **Ruta absoluta en `storedAt`:** expone la ruta del servidor en la respuesta.
- **Cuerpo de `backend-health` sin límite:** el upstream se lee completo en memoria.
- **Validación de claims:** `sub` vacío o no textual no se valida con reglas propias. Un `sub`
  vacío responde 200 con owner vacío en las consultas (verificado en la revisión).
- **Dependencias:** `urllib3` y `python-multipart` están fijados, pero la confirmación de CVE
  con `pip-audit` está pendiente.

## Preguntas abiertas

1. ¿El frontend necesita algún origen concreto en CORS? El valor por defecto asume `http://localhost:4200` y `http://127.0.0.1:4200` (H-API-08); falta confirmar los orígenes de otros entornos.
2. ¿`auth/` emite tokens con `iss`, `aud`, `exp`, `iat`, `sub` y `role` tal como los requiere
   esta API? No se ha verificado.
3. ¿Debe el directorio de subidas separarse por owner? Hoy todos comparten el mismo espacio y
   un nombre repetido responde 409 aunque lo haya subido otro usuario.
4. ¿El claim `role` debe dar acceso a tareas de otros owners (por ejemplo, para un rol
   `TRAINER`)? Hoy no lo usa ningún endpoint.
5. ¿La respuesta de `storedAt` debe seguir existiendo? Si el cliente no la necesita, convendría
   quitarla.
6. ¿Hace falta documentar el 422 de FastAPI cuando falta el campo `file` en la subida? No se
   capturó en esta ejecución; sigue el mismo formato de lista que el ejemplo de `POST /api/tasks`.
7. ¿`status` de `backend-health` debe ser siempre 200 o reflejar el estado upstream? Hoy refleja
   el código upstream dentro de un 200.

## Documentos consultados

- `README.md` (puertos, documentación en `/docs`, referencias de componentes).
- `RETO.md` (sección api: hallazgos sembrados y contratos a preservar).
- `docs/GOOD_PRACTICES.md` (sección api: Pydantic, capas, autorización por identidad, archivos).
- `prompts/PLAN.md` y `prompts/HALLAZGOS.md` (contratos acordados y estado de los hallazgos).
- Código de `api/`: `app/main.py`, `app/config.py`, `app/security.py`, `app/errors.py`,
  `app/schemas.py`, `app/routes/*.py`, `app/services/*.py`, `app/repositories/tasks.py`,
  `app/database.py`.
- Respuestas capturadas con una instancia temporal de la API y una base SQLite temporal. No se
  modificó el código ni la base del repositorio.
