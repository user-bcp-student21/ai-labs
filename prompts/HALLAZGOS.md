# Hallazgos de ReqFlow

Seguimiento de hallazgos por componente. IDs: H-AUTH-NN, H-API-NN, H-WEB-NN.
Fecha de discovery del componente api: 2026-11-02. Estado inicial: Aprobado.
Este archivo es el único lugar de seguimiento; los demás componentes conservan
sus filas al actualizarse.

## api

### Alcance del discovery

- Solo lectura de `api/`. No se modificó código ni se ejecutaron pruebas en este paso.
- Fuentes: `README.md`, `RETO.md`, `docs/GOOD_PRACTICES.md`, `prompts/api.md`,
  `api/app/main.py`, `api/requirements.txt`, `api/pyproject.toml`, `api/tests/test_api.py`.
- `docs/ENDPOINTS.md` y `docs/TESTING.md` no existen todavía. `PLAN.md` tampoco.
  No se crearon en este paso.

### Contrato observado (derivado del código)

No existe `docs/ENDPOINTS.md`, así que no hay contrato acordado. El contrato
observado es el siguiente. Todas las rutas exigen la cabecera
`Authorization: Bearer <token>` y devuelven 401 si el token no es válido
(`api/app/main.py:26`).

| Método y ruta | Entrada | Salida observada | Evidencia |
|---|---|---|---|
| GET /api/tasks | query `owner` opcional | lista de tareas `{id,title,description,status,owner,priority,createdAt}` | api/app/main.py:67-75 |
| POST /api/tasks | JSON libre: title, description, status, priority, owner | 201 con la tarea creada | api/app/main.py:77-88 |
| GET /api/summary | query `owner` opcional | `{owner,total,byStatus,highPriorityOpen}` | api/app/main.py:90-105 |
| POST /api/requirements | multipart `file` | 201 `{owner,fileName,storedAt,size}` | api/app/main.py:107-112 |
| GET /api/backend-health | ninguna | `{requestedBy,status,body}`; nunca devuelve error HTTP | api/app/main.py:114-121 |

Contrato acordado: Aprobado. Requiere `docs/ENDPOINTS.md` y la aprobación de
la persona responsable antes de cualquier cambio de formato.

### Flujo del token

1. `legacy_identity` toma la cabecera `Authorization`, quita el prefijo
   `Bearer ` y decodifica Base64 (`api/app/main.py:17-19`).
2. Separa el texto en cuatro partes por `|`: usuario, rol, expiración y secreto
   (`api/app/main.py:20-22`).
3. Compara el secreto con la constante embebida `LEGACY_SECRET`
   (`api/app/main.py:14`, `api/app/main.py:22`) y valida la expiración.
4. Devuelve `{username, role}` a las rutas. El rol no se usa en ninguna ruta.
5. Cualquier excepción se convierte en 401 con el detalle interno
   (`api/app/main.py:25-26`).

### Flujo de SQLite y archivos

- `create_app` abre una única conexión SQLite compartida
  (`api/app/main.py:35-36`), crea la tabla `tasks` (`api/app/main.py:37`) e inserta
  tres datos de prueba si está vacía (`api/app/main.py:39-43`).
- Las rutas de tareas construyen SQL concatenando entradas del cliente
  (`api/app/main.py:70`, `api/app/main.py:84`, `api/app/main.py:93`).
- `POST /api/requirements` une el directorio de subida con `file.filename` sin
  normalizar y escribe el contenido completo (`api/app/main.py:109-111`).

### Matriz de seguimiento

Orden: de mayor a menor severidad. Las filas H-API-01 a H-API-04 corresponden
a RETO.md; H-API-05 a H-API-13 son hallazgos adicionales observados en el
código y no listados en RETO.md. Todos los hallazgos de RETO.md para api
aparecen en el código, así que ninguno se marca "No encontrado".

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Consultas SQL con entradas concatenadas (owner en GET, owner y campos en POST, owner en summary) | Vulnerabilidad | Una comilla en un valor rompe la sentencia o cambia la condición y los valores insertados. Permite leer o escribir filas de otros owners fuera del contrato. Es la causa de inyección SQL. | api/app/main.py:70, api/app/main.py:84, api/app/main.py:93 | alta | Resuelto: SQL parametrizado en api/app/repositories/tasks.py; owner ajeno responde 403 (api/app/services/tasks.py). |
| H-API-02 | api | Se usa directamente `file.filename` al guardar requerimientos, sin límite de tamaño ni de extensión | Vulnerabilidad | Si el nombre contiene separadores o componentes de directorio, la ruta resultante sale del directorio de subida y `write_bytes` escribe fuera de él. Además sobrescribe archivos existentes, carga todo el contenido en memoria y acepta cualquier extensión. | api/app/main.py:109, api/app/main.py:110, api/app/main.py:111, api/app/main.py:112 | alta | Resuelto: nombre reducido con Path.name, extensiones .txt/.md, límite 1 MiB con 413 y escritura exclusiva con 409 (api/app/services/files.py). |
| H-API-03 | api | Token Base64 con secreto embebido en el código, sin firma, emisor ni audiencia | Vulnerabilidad | Base64 no es una firma. Quien lea el código conoce el secreto y puede fabricar tokens con cualquier usuario y rol. La expiración sí se valida, pero no hay emisor, audiencia ni revocación. El secreto también aparece en las pruebas. | api/app/main.py:14, api/app/main.py:17-22, api/tests/test_api.py:10 | alta | Pendiente (revisión local): JWT verificado con PyJWT (api/app/security.py) y secreto desde WORKSHOP_JWT_SECRET, pero el literal del secreto antiguo sigue en api/tests/support.py:10. Coordinación con auth/ pendiente. |
| H-API-04 | api | El cliente elige el owner consultado o creado (query `owner` y campo `owner` del payload) | Vulnerabilidad | El parámetro `owner` reemplaza la identidad del token. Un usuario puede leer el resumen y las tareas de otro owner, y crear tareas a nombre de otro. No hay comprobación de rol. | api/app/main.py:68-70, api/app/main.py:83, api/app/main.py:91-93 | alta | Resuelto: la identidad sale del token; owner distinto responde 403 (api/app/services/tasks.py). |
| H-API-05 | api | SCA: `urllib3 2.5.0` con CVE de descompresión sin límite | Vulnerabilidad | Según GHSA/NVD, CVE-2025-66418 y CVE-2025-66471 afectan versiones anteriores a 2.6.0. El boletín de IBM indica que 2.5.0 también es vulnerable a CVE-2026-21441. Un servidor malicioso puede agotar CPU y memoria. La exposición es acotada: solo `backend-health` la usa, contra una URL fija por configuración. Versión corregida exacta para los tres CVE: Aprobado de confirmar. | api/requirements.txt:4, api/app/main.py:118 | media | Pendiente (revisión local): api/tests/test_dependencies.py valida el entorno instalado, no el pin de api/requirements.txt:4, y no hay evidencia de pip-audit. Cerrar con pip-audit o aprobación de uso de la herramienta. |
| H-API-06 | api | SCA: `python-multipart 0.0.21` con CVE de path traversal y de consumo excesivo de CPU | Vulnerabilidad | CVE-2026-24486 afecta versiones anteriores a 0.0.22, pero solo con las opciones `UPLOAD_DIR` y `UPLOAD_KEEP_FILENAME=True`, que aquí no se usan. La advisory GHSA-mj87-hwqh-73pj (CVE-2026-40347) pide 0.0.26 o superior por DoS en el parseo multipart; el rango exacto afectado está Aprobado de confirmar. El parser multipart lo usa `/api/requirements`. | api/requirements.txt:5, api/app/main.py:108 | media | Pendiente (revisión local): mismo gap que H-API-05; api/requirements.txt:5 no se verifica con pip-audit y el rango exacto de GHSA-mj87-hwqh-73pj sigue sin confirmar. |
| H-API-07 | api | Respuestas de error con detalle interno (adicional, no listado en RETO.md) | Vulnerabilidad | El texto de la excepción llega al cliente en el 401 y en `backend-health`. Puede revelar rutas, URLs internas o detalles de parseo. | api/app/main.py:26, api/app/main.py:121 | media | Resuelto: el 401 usa detalle fijo "Invalid token" y el 502 de backend-health no incluye el error interno (api/app/security.py, api/app/services/health.py). |
| H-API-08 | api | CORS con `allow_origins=["*"]` y `allow_credentials=True` (adicional, no listado en RETO.md) | Vulnerabilidad | Configuración permisiva fija en código, sin lista de orígenes por entorno. Con credenciales habilitadas, cualquier sitio puede hacer peticiones autenticadas desde el navegador. El efecto exacto debe comprobarse en el navegador. | api/app/main.py:49-53 | media | Pendiente (revisión local): orígenes desde WORKSHOP_CORS_ORIGINS sin comodín (api/app/cors.py, api/app/main.py); pruebas en api/tests/test_cors.py (45 passed, cobertura 99,28%). Falta comprobación en navegador y definir la variable en compose.yaml. |
| H-API-09 | api | Captura amplia de excepciones que enmascara fallos (adicional, relacionado con RETO "Calidad") | Bug | En `backend-health` cualquier fallo devuelve HTTP 200 con `status: 0`, por lo que el cliente no distingue una caída de una respuesta válida. En `legacy_identity` la captura amplia convierte cualquier error en 401. | api/app/main.py:25, api/app/main.py:120-121 | media | Resuelto: fallo del backend responde 502 genérico y se capturan solo errores de urllib3 (api/app/services/health.py). |
| H-API-10 | api | Rutas, base de datos, reglas y serialización en un solo archivo y una sola función | Refactor | `create_app` concentra la conexión, la creación de la tabla, la siembra, las rutas y la lógica de resumen. Cualquier cambio en una capa afecta a las demás y dificulta las pruebas aisladas. Es el hallazgo arquitectónico de RETO.md. | api/app/main.py:29, api/app/main.py:56, api/app/main.py:67-121 | media | Resuelto: capas en api/app/routes, services, repositories, config.py y database.py; api/app/main.py solo compone la aplicación. |
| H-API-11 | api | Uso de `dict[str, Any]` crudo en entradas, salidas y serialización | Refactor | Sin modelos Pydantic, el payload no se valida: `str(payload.get(...))` acepta cualquier tipo y convierte `None` en texto. Los contratos no quedan documentados en el código. Es el hallazgo de tipado de RETO.md. | api/app/main.py:78-83, api/app/main.py:91, api/app/main.py:115 | baja | Pendiente (revisión local): la entrada usa Pydantic en api/app/schemas.py, pero las salidas siguen como `dict[str, Any]` en api/app/services/tasks.py:20,24,31,45, api/app/routes/tasks.py:10,16,21,27, api/app/routes/requirements.py:17 y api/app/routes/health.py:11,15. No hay modelos de respuesta. |
| H-API-12 | api | Condicionales anidados en el cálculo de `highPriorityOpen` | Refactor | Tres niveles de `if` para una sola regla (prioridad alta y estado no cerrado). Son difíciles de leer y de probar. Es el hallazgo de condicionales de RETO.md. | api/app/main.py:101-104 | baja | Resuelto: regla extraída a is_open_high_priority con filtro SQL en api/app/services/tasks.py y api/app/repositories/tasks.py. |
| H-API-13 | api | Duplicación de sentencias SQL, columnas y datos de siembra | Refactor | La lista de columnas se repite en tres consultas, las tres sentencias de siembra son casi idénticas y los literales `HIGH`, `DONE` y `ARCHIVED` aparecen sin constante. Un cambio de esquema obliga a editar varios lugares. Es el hallazgo de duplicación de RETO.md. | api/app/main.py:40-42, api/app/main.py:70, api/app/main.py:87, api/app/main.py:101-103 | baja | Pendiente (revisión local): la duplicación persiste. `INSERT_SEED_SQL` (api/app/database.py:10) repite `INSERT_TASK_SQL` (api/app/repositories/tasks.py:8), y la lista de columnas aparece en api/app/database.py:5, api/app/repositories/tasks.py:4 y :8. |

### Ejecuciones de pruebas

No se ejecutó ninguna prueba en este paso. Ninguna ejecución queda registrada
como válida. Cuando exista `docs/TESTING.md`, cada ejecución debe indicar
componente api, IDs H-API y resultado real.

### Aprobados y preguntas abiertas

1. Confirmar la versión corregida de urllib3 para CVE-2025-66418, CVE-2025-66471 y CVE-2026-21441 (H-API-05).
2. Confirmar el rango afectado de python-multipart por CVE-2026-40347 y elegir la versión mínima (H-API-06).
3. Acordar el contrato del token con el responsable de auth. El cambio de formato afecta a ambos consumidores; no se leyó `auth/` en este paso (H-API-03).
4. Decidir si el rol del token debe autorizar la consulta de otros owners (H-API-04).
5. Revisar `api/tests/test_api.py:14`: el helper `headers()` no usa la función `token()` de la línea 9 y no pudo confirmarse que la cabecera de autenticación sea la esperada. **Corregido:** `headers()` sí llama a `token()` (api/tests/test_api.py:16 antes del cambio); tras la refactorización el helper delega en api/tests/support.py.
6. Ejecutar `python tools/lab.py test api` y registrar la salida real en `docs/TESTING.md` (Aprobado).

### Candidatos de discovery (api) - pendiente de revisión humana

Discovery de solo lectura sobre `api/` (más `compose.yaml` solo para el despliegue de api). Estado de todos: CANDIDATO.
No se creó ningún issue ni se modificó código. Las comprobaciones se hicieron con un script temporal contra una base
SQLite y un directorio de subida en `%TEMP%` (ya eliminados) y un secreto de prueba aislado; no se ejecutó la suite.
Nota: los pins de `urllib3 2.6.3` y `python-multipart 0.0.26` (api/requirements.txt:4-5) ya no coinciden con las
versiones descritas en H-API-05 y H-API-06; no se repiten aquí.

#### H-API-14 - compose.yaml no define WORKSHOP_JWT_SECRET: el contenedor api no arranca
- Estado: CANDIDATO
- Evidencia: `compose.yaml:7-19` (servicio `api` sin `WORKSHOP_JWT_SECRET`); `api/app/security.py:26-30`
  (`RuntimeError` si falta); `api/app/main.py:22,46` (`create_app()` se ejecuta al importar el módulo).
  Comprobado: `load_jwt_secret()` sin la variable devuelve `RuntimeError: WORKSHOP_JWT_SECRET must be set`.
- Impacto: `docker compose up` deja api caído; web y `/api/backend-health` dejan de funcionar en el despliegue documentado.
- Prioridad propuesta: alta
- Contrato potencialmente afectado: despliegue/arranque (`compose.yaml`), no los endpoints. Cualquier valor debe ser de
  entorno, sin secretos reales en el repositorio.
- Cómo validarlo: `docker compose up --build api` y revisar los logs (sin Docker: `python -c "from app.main import app"`
  en `api/` con la variable sin definir). Tras el cambio, el contenedor debe quedar en ejecución y aceptar un JWT firmado
  con el mismo secreto que `auth/` (coordinar con H-API-03).

#### H-API-15 - Claims `sub` y `role` del JWT sin validar contenido
- Estado: CANDIDATO
- Evidencia: `api/app/security.py:54,58` (`require` solo exige presencia; `Identity(username=claims["sub"], ...)`);
  `api/app/services/tasks.py:13-14` (owner vacío cae a la identidad). Comprobado con un token válido y `sub=""`:
  `GET /api/tasks` responde 200 con `[]`, `POST /api/tasks` responde 201 con `owner=""`; con `sub="   "` responde 200 y
  con `role=""` responde 200. `role` no se usa en ninguna ruta.
- Impacto: un token firmado con identidad vacía o en blanco se acepta y escribe tareas con owner vacío, que los
  usuarios reales no pueden consultar. Depende de que `auth/` emita tokens así; la firma sigue siendo necesaria.
- Prioridad propuesta: media
- Contrato potencialmente afectado: `Authorization` (401 vs 200) y `owner` de `POST /api/tasks`; `docs/ENDPOINTS.md`
  no define reglas para `sub` y `role`.
- Cómo validarlo: pruebas en `api/tests/test_security.py` con `sub` vacío, en blanco, ausente y no textual, y `role`
  vacío; esperado según el contrato que apruebe la persona responsable (propuesta: 401 con "Invalid token").

#### H-API-16 - `storedAt` expone la ruta absoluta del servidor
- Estado: CANDIDATO
- Evidencia: `api/app/services/files.py:25` (`str(target)`); `api/app/routes/requirements.py:19-20`. Comprobado:
  `POST /api/requirements` devolvió `storedAt` con la ruta absoluta del directorio temporal.
- Impacto: filtra la estructura de directorios del servidor a cualquier usuario autenticado; es la misma clase de
  fuga que H-API-07 resolvió para errores.
- Prioridad propuesta: baja
- Contrato potencialmente afectado: campo `storedAt` de la respuesta 201 de `POST /api/requirements`, consumido
  potencialmente por web. Cambiarlo exige aprobación y revisar `docs/ENDPOINTS.md`.
- Cómo validarlo: prueba que suba `requirements.txt` y verifique que `storedAt` no contiene el directorio de subida
  (por ejemplo, solo el nombre). Revisar antes si `web/` usa el campo (fuera del alcance de este discovery).

#### H-API-17 - Archivos subidos sin separación por usuario
- Estado: CANDIDATO
- Evidencia: `api/app/services/files.py:19-21` (`upload_dir / safe_name`, modo `xb`; el owner no participa en la ruta);
  `api/app/routes/requirements.py:19-20` (el owner solo se añade a la respuesta). Comprobado: `student` sube `a.txt` y
  `trainer` subiendo `a.txt` recibe 409.
- Impacto: todos los usuarios comparten un único espacio de nombres. Un usuario puede bloquear nombres de otro
  (ocupa `requirements.txt`) y no hay vínculo entre archivo e identidad, contra el principio de autorización ligada
  a la identidad. No se comprobó lectura ajena: no existe endpoint de descarga.
- Prioridad propuesta: media
- Contrato potencialmente afectado: `POST /api/requirements` (409 por nombre repetido y `storedAt`).
- Cómo validarlo: prueba con dos identidades que suban el mismo nombre; esperado según decisión: 201 para ambos
  (subdirectorio por `sub` saneado) o 409 documentado. Mantener las pruebas de traversal, extensión y 1 MiB.
