# Plan de corrección de ReqFlow

Plan para los hallazgos de `prompts/HALLAZGOS.md` marcados "Aprobado".
Estado: propuesta. No se modificó código ni se ejecutaron pruebas en este paso.

## api

### Alcance y fuentes

- Hallazgos: H-API-01 a H-API-13 (matriz de `prompts/HALLAZGOS.md`, estado "Aprobado").
- Fuentes leídas: `README.md`, `RETO.md`, `AGENTS.md`, `docs/GOOD_PRACTICES.md`,
  `prompts/HALLAZGOS.md`, `prompts/api.md`, `api/app/main.py`, `api/tests/test_api.py`,
  `api/requirements.txt`, `api/requirements-dev.txt`, `api/pyproject.toml`.
- `docs/ENDPOINTS.md` y `docs/TESTING.md` no existen. El contrato que se preserva es
  el **comportamiento observado** en `api/app/main.py` y `api/tests/test_api.py`.
- Cambios de comportamiento que sí alteran respuestas (autorización por `owner`,
  validación de payload, errores HTTP nuevos) requieren aprobación humana antes de
  implementarse. Se marcan como **Pendiente de aprobación**.

### Pendientes que bloquean la implementación

No son aprobaciones inventadas: son decisiones que siguen abiertas en `prompts/HALLAZGOS.md`
(sección "Aprobados y preguntas abiertas") o dependencias que no se pueden verificar desde `api/`.

1. **Versión de urllib3 (H-API-05).** Evidencia: Red Hat (RHSA-2026:1674 / RHSA-2026:1254)
   indica que CVE-2025-66418, CVE-2025-66471 y CVE-2026-21441 se corrigen con
   **urllib3 ≥ 2.6.3**. Falta confirmación del responsable.
2. **Versión de python-multipart (H-API-06).** Evidencia: GHSA-mj87-hwqh-73pj (CVE-2026-40347)
   indica **≥ 0.0.26**. Falta confirmar que `fastapi==0.128.2` lo acepta (se valida al instalar).
3. **Contrato del token con el responsable de `auth/` (H-API-03).** No se leyó `auth/`
   (fuera de alcance). Cambiar el formato de token rompe el login si `auth/` no cambia a la vez.
4. **Rol y autorización por `owner` (H-API-04).** Decidir si el rol puede consultar otros owners
   o si la regla es fija: solo la identidad del token.
5. **Helper `headers()` en `api/tests/test_api.py:15-16`.** La pregunta 5 de `HALLAZGOS.md`
   dice que no usa `token()`. En la lectura, la línea 16 termina en `role)}`, lo que sugiere
   que sí llama a `token(username, role)`. Verificar con una lectura cruda antes de corregir.
6. **Ejecución base de pruebas.** `python tools/lab.py test api` aún no se ejecutó. Pendiente.

### Orden propuesto

Las pruebas de caracterización van primero. Después, los cambios de estructura, luego
los de seguridad, y al final las dependencias y los refactors de bajo riesgo.

1. Caracterización (H-API-01 a H-API-09 comparten la misma base de pruebas).
2. H-API-10: separar capas (sin cambiar comportamiento).
3. H-API-11: modelos Pydantic (contratos de entrada y salida).
4. H-API-01: SQL parametrizado.
5. H-API-04: autorización ligada a la identidad.
6. H-API-03: verificación real del token.
7. H-API-02: carga segura de archivos.
8. H-API-07, H-API-09: errores genéricos y captura acotada.
9. H-API-08: CORS por configuración.
10. H-API-05, H-API-06: actualizar dependencias.
11. H-API-12, H-API-13: condicionales y duplicación.

### Reglas transversales

- Contrato: rutas `GET /api/tasks`, `POST /api/tasks`, `GET /api/summary`,
  `POST /api/requirements` y `GET /api/backend-health`, mismas formas de respuesta y
  códigos de éxito (200/201), salvo los cambios marcados como pendientes.
- Clean Code (`AGENTS.md` 8-12): una responsabilidad por función; nombres por propósito;
  sin duplicación; retorno anticipado en lugar de anidamiento; constantes con nombre
  (`MAX_UPLOAD_BYTES`, `HEALTH_TIMEOUT_SECONDS`, `TOKEN_TTL_SECONDS`, `STATUS_DONE`).
- Cobertura del código modificado: ≥ 85% (`AGENTS.md`, api, punto 7). Se mide con
  `pytest-cov` ya presente en `api/requirements-dev.txt`.
- Sin secretos reales: el secreto sale del código y se toma de variable de entorno en
  el arranque, con un valor de prueba aislado en los tests.

---

### H-API-01: Consultas SQL con entradas concatenadas

- **Hallazgo:** SQL con `owner`, payload y resumen concatenados (severidad alta, Aprobado).
- **Problema:** `api/app/main.py:70` (`owner` en `GET /api/tasks`), `api/app/main.py:84`
  (campos de `POST /api/tasks`), `api/app/main.py:93` (`owner` en `GET /api/summary`).
  Una comilla rompe la sentencia o cambia la condición (`student' OR '1'='1` devuelve todas las filas).
  `api/app/main.py:87` concatena `lastrowid` (entero, pero sin parametrizar).
- **Cambio propuesto:** repositorio con `?` en todas las consultas: `list_by_owner`,
  `insert_task`, `find_by_id`, `summary_rows_for_owner`. Ninguna ruta toca SQL directamente.
  Se mantiene la misma salida. Con H-API-04, el `owner` deja de ser entrada de consulta
  (ver H-API-04); la parametrización sigue siendo obligatoria como defensa.
- **Archivos:** `api/app/repositories/tasks.py` (nuevo), `api/app/main.py` (retirar SQL).
- **Caracterización antes de tocar:** en `api/tests/test_api.py`, afirmar que `owner=student`
  devuelve 2 tareas y que `owner=inexistente` devuelve lista vacía. Agregar un test de
  seguridad con `owner=student' OR '1'='1` que **falle hoy** (documenta la vulnerabilidad)
  y debe devolver lista vacía tras el cambio.
- **Contrato que se mantiene:** `GET /api/tasks` y `GET /api/summary` con owner válido.

### H-API-02: Carga de archivos sin normalizar nombre, tamaño ni extensión

- **Hallazgo:** `file.filename` usado tal cual; sobrescribe; carga todo en memoria (severidad alta, Aprobado).
- **Problema:** `api/app/main.py:109` une `selected_uploads` con `file.filename`; `:110` lee
  todo el contenido; `:111` lo escribe con `write_bytes`. Un nombre con `../` escribe fuera del
  directorio y uno existente se sobrescribe.
- **Cambio propuesto:** servicio `files.py` con:
  - `safe_filename(name)`: `Path(name).name`, validar contra una lista de caracteres permitidos y
    longitud máxima. Rechazar con 422 si queda vacío o no cumple.
  - Extensión en lista permitida, p. ej. `ALLOWED_EXTENSIONS = {".txt", ".md"}`
    (**Pendiente de aprobación**; el test actual usa `.txt`).
  - Lectura por bloques con límite `MAX_UPLOAD_BYTES` (propuesta 1 MiB, **Pendiente de aprobación**);
    responder 413 al exceder.
  - Si el destino existe, responder 409 y no sobrescribir.
  - Verificación defensiva: `target.resolve()` debe quedar dentro de `upload_dir`.
- **Archivos:** `api/app/services/files.py` (nuevo), `api/app/routes/requirements.py` (nuevo),
  `api/app/main.py`.
- **Caracterización antes de tocar:** `test_uploads_requirement` ya existe con `requirements.txt`
  (debe seguir pasando). Agregar: nombre `../x.txt` no escribe fuera del directorio; segunda
  subida del mismo nombre no sobrescribe; archivo mayor al límite devuelve 413 (falla hoy).
- **Contrato que se mantiene:** 201 con `{owner, fileName, storedAt, size}` para un archivo válido.

### H-API-03: Token Base64 con secreto embebido

- **Hallazgo:** token sin firma, con secreto en código (severidad alta, Aprobado).
- **Problema:** `api/app/main.py:14` define `LEGACY_SECRET`; `:17-22` decodifica Base64 y
  compara el secreto. Quien lee el código puede fabricar tokens. No hay emisor ni audiencia.
  `api/tests/test_api.py:10` repite el secreto.
- **Cambio propuesto:** módulo `api/app/security.py` que verifica un JWT HS256 con
  `jwt.decode(token, key, algorithms=["HS256"], audience=..., issuer=...)`. Valida `exp`
  y reconoce claims `sub` y `role`. La clave llega de `WORKSHOP_JWT_SECRET` (sin valor por
  defecto; si falta, el arranque falla). El emisor y la audiencia son constantes con nombre.
  - **Dependencia nueva:** `PyJWT`. Justificación: verifica firma, expiración, emisor y
    audiencia sin implementar criptografía a mano. Alternativa sin dependencia:
    `hmac`/`hashlib` de la biblioteca estándar, con más riesgo de error. Requiere aprobación.
  - **Pendiente de aprobación (bloqueante):** coordinar el formato con el responsable de `auth/`
    (ver pendiente 3). Sin ese acuerdo no se cambia el formato.
- **Archivos:** `api/app/security.py` (nuevo), `api/app/main.py` (retirar `legacy_identity`),
  `api/requirements.txt`, `api/tests/test_api.py` (helper de token).
- **Caracterización antes de tocar:** documentar que hoy un token con el formato Base64 y el
  secreto embebido responde 200. Tras el cambio debe responder 401 (cambio intencional, pendiente).
  Agregar pruebas de token expirado, firma incorrecta, emisor y audiencia incorrectos.
- **Contrato que se mantiene:** cabecera `Authorization` con `Bearer`; 401 ante token inválido.

### H-API-04: El cliente elige el owner consultado o creado

- **Hallazgo:** `owner` en query y payload reemplaza la identidad (severidad alta, Aprobado).
- **Problema:** `api/app/main.py:68-70` (query `owner`), `:83` (`owner` del payload),
  `:91-93` (`owner` del resumen). No hay comprobación de rol; el campo `role` del token no se usa.
- **Cambio propuesto:** las consultas usan siempre `identity["username"]`, nunca un parámetro
  del cliente (regla de `docs/GOOD_PRACTICES.md`, api). Se retira `owner` de la query y del payload.
  - **Pendiente de aprobación:** la opción alternativa es responder 403 si `owner` difiere de la
    identidad, en lugar de ignorarlo. Elegir una antes de implementar. Decidir también si el rol
    `ADMIN`, si existe, puede consultar otros owners (pendiente 4).
- **Archivos:** `api/app/routes/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo),
  `api/app/main.py`.
- **Caracterización antes de tocar:** documentar que `GET /api/tasks?owner=trainer` con token de
  `student` devuelve tareas de `trainer` (comportamiento actual). Tras el cambio: tareas de `student`
  o 403, según la decisión. Documentar también que `POST /api/tasks` con `owner` en el payload
  guarda el `owner` enviado; tras el cambio guarda la identidad.
- **Contrato que se mantiene:** `owner` en la respuesta refleja al dueño real de los datos.

### H-API-05: urllib3 2.5.0 con CVE de descompresión sin límite

- **Hallazgo:** SCA, severidad media, Aprobado.
- **Problema:** `api/requirements.txt:4` fija `urllib3==2.5.0`; `api/app/main.py:118` la usa en
  `backend-health`. Un servidor malicioso puede agotar CPU y memoria.
- **Cambio propuesto:** `urllib3==2.6.3` (versión mínima confirmada por Red Hat para los tres CVE;
  ver pendiente 1). Confirmar con `pip-audit` al implementar; herramienta de desarrollo, no se agrega
  a `requirements.txt`. Pendiente la aprobación del responsable.
- **Archivos:** `api/requirements.txt`.
- **Caracterización antes de tocar:** `backend-health` aún no tiene prueba. Agregar una con un servidor
  local de prueba en `AUTH_HEALTH_URL` y comprobar `status` y `body` con la forma actual.
- **Contrato que se mantiene:** `{requestedBy, status, body}`.

### H-API-06: python-multipart 0.0.21 con CVE de DoS

- **Hallazgo:** SCA, severidad media, Aprobado.
- **Problema:** `api/requirements.txt:5` fija `python-multipart==0.0.21`; lo usa `/api/requirements`
  (`api/app/main.py:108`). GHSA-mj87-hwqh-73pj (CVE-2026-40347) se corrige en 0.0.26.
  CVE-2026-24486 no aplica porque las opciones `UPLOAD_DIR` y `UPLOAD_KEEP_FILENAME` no se usan.
- **Cambio propuesto:** `python-multipart==0.0.26`, validando la compatibilidad con
  `fastapi==0.128.2` al instalar (pendiente 2).
- **Archivos:** `api/requirements.txt`.
- **Caracterización antes de tocar:** `test_uploads_requirement` debe seguir pasando sin cambios.
- **Contrato que se mantiene:** igual al de H-API-02 para un archivo válido.

### H-API-07: Detalle interno en las respuestas de error

- **Hallazgo:** adicional, severidad media, Aprobado.
- **Problema:** `api/app/main.py:26` pone `str(error)` en el 401; `api/app/main.py:121` pone
  `str(error)` en `backend-health`.
- **Cambio propuesto:** respuesta genérica (`"Invalid token"`) y `logging.getLogger(__name__).exception(...)`
  en el servidor. En `backend-health`, `body` deja de incluir `str(error)` y se registra el error.
  Se conserva la forma de la respuesta.
- **Archivos:** `api/app/security.py`, `api/app/routes/health.py` (nuevo).
- **Caracterización antes de tocar:** documentar el `detail` actual del 401 (incluye texto de
  excepción). Tras el cambio, el `detail` debe ser exactamente `"Invalid token"`. Probar que el
  log se escribe (con `caplog`).
- **Contrato que se mantiene:** 401 con `detail` presente; `backend-health` sin 5xx nuevos.

### H-API-08: CORS permisivo con credenciales

- **Hallazgo:** adicional, severidad media, Aprobado.
- **Problema:** `api/app/main.py:49-53` usa `allow_origins=["*"]` con `allow_credentials=True`.
  Hipótesis (por verificar en el navegador): Starlette refleja el origen de la petición cuando
  hay comodín y credenciales, lo que permite peticiones autenticadas desde cualquier sitio.
- **Cambio propuesto:** lista de orígenes desde `WORKSHOP_CORS_ORIGINS` (separados por coma), sin
  comodín. El valor por defecto de desarrollo y el origen real del frontend deben confirmarse con
  `compose.yaml` y el despliegue (fuera de `api/`; **pendiente**).
- **Archivos:** `api/app/config.py` (nuevo), `api/app/main.py`.
- **Caracterización antes de tocar:** prueba de preflight con un origen permitido y otro no permitido,
  documentando el encabezado `access-control-allow-origin` actual.
- **Contrato que se mantiene:** mismos métodos y cabeceras; solo cambia la lista de orígenes.

### H-API-09: Captura amplia que enmascara fallos

- **Hallazgo:** bug, severidad media, Aprobado.
- **Problema:** `api/app/main.py:120-121` devuelve HTTP 200 con `status: 0` ante cualquier fallo.
  `api/app/main.py:25` convierte cualquier error en 401.
- **Cambio propuesto:** en `security.py` capturar solo `ValueError` (incluye `binascii.Error`
  y el `int()` del `exp`). En `backend-health` capturar `urllib3.exceptions.HTTPError`
  (incluye timeouts). **Pendiente de aprobación:** la alternativa es responder 502 con
  mensaje genérico en lugar de 200 con `status: 0`. Esta decisión cambia el contrato y debe aprobarse.
- **Archivos:** `api/app/security.py`, `api/app/routes/health.py`.
- **Caracterización antes de tocar:** probar `backend-health` contra un puerto cerrado y documentar
  la respuesta actual (200, `status: 0`). Probar un token con base64 inválido (401).
- **Contrato que se mantiene:** si se aprueba la opción A, el contrato no cambia.

### H-API-10: Rutas, base de datos, reglas y serialización en un solo archivo

- **Hallazgo:** refactor, severidad media, Aprobado.
- **Problema:** `create_app` (`api/app/main.py:29-125`) concentra conexión, esquema, siembra,
  rutas, reglas y serialización.
- **Cambio propuesto:** módulos por capa:
  - `api/app/config.py`: rutas, secreto, orígenes, límites (constantes).
  - `api/app/database.py`: conexión, esquema y siembra.
  - `api/app/schemas.py`: modelos Pydantic (H-API-11).
  - `api/app/security.py`: verificación de token (H-API-03/07/09).
  - `api/app/repositories/tasks.py`: SQL parametrizado (H-API-01).
  - `api/app/services/tasks.py`: reglas y resumen.
  - `api/app/services/files.py`: carga segura (H-API-02).
  - `api/app/routes/tasks.py`, `requirements.py`, `health.py`: rutas finas.
  - `api/app/main.py`: `create_app(db_path, upload_dir)` solo cablea dependencias.
  Se conserva `create_app(db_path=..., upload_dir=...)`, la variable `app = create_app()` y las
  variables de entorno `WORKSHOP_DB_PATH`, `WORKSHOP_UPLOAD_DIR`, `AUTH_HEALTH_URL`, porque son
  la interfaz de configuración actual (`api/tests/test_api.py` usa `create_app` con rutas).
  Revisar `api/Dockerfile` antes de implementar para confirmar el comando de arranque (no leído).
- **Archivos:** los de la lista anterior; `api/Dockerfile` solo se revisa (no se cambia).
- **Caracterización antes de tocar:** la suite actual de `api/tests/test_api.py` (4 pruebas) más
  las pruebas de H-API-01 a H-API-09 deben pasar **sin cambios de expectativa** antes de separar capas.
- **Contrato que se mantiene:** las mismas rutas y firmas de `create_app`.

### H-API-11: Uso de `dict[str, Any]` crudo

- **Hallazgo:** refactor, severidad baja, Aprobado.
- **Problema:** `api/app/main.py:78-83` lee `payload` como `dict`. `str(payload.get(...))` acepta
  cualquier tipo y convierte `None` en `"None"`. Respuestas en `:91` y `:115` sin modelo.
- **Cambio propuesto:** modelos Pydantic:
  - `TaskCreate`: `title` (str), `description` (str, default `""`), `status` (default `"TODO"`),
    `priority` (default `"MEDIUM"`). `owner` se retira del modelo (H-API-04).
  - Enumeraciones para `status` (`TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`) y `priority`
    (`LOW`, `MEDIUM`, `HIGH`), tomadas del código y de la siembra (`api/app/main.py:40-42`).
  - Respuestas: `TaskOut`, `SummaryOut`, `RequirementOut`, `BackendHealthOut`.
  - **Pendiente de aprobación:** restringir valores (422 ante `status` desconocido) y exigir
    `title` no vacío cambia el contrato. Confirmar antes de aplicar; por defecto se aceptan los
    valores actuales.
- **Archivos:** `api/app/schemas.py` (nuevo), `api/app/routes/*.py`.
- **Caracterización antes de tocar:** documentar que `POST /api/tasks` sin `description` guarda
  `""` y que un `title` numérico se guarda como texto (comportamiento actual).
- **Contrato que se mantiene:** nombres de campos de salida (`createdAt`, `byStatus`, etc.).

### H-API-12: Condicionales anidados en `highPriorityOpen`

- **Hallazgo:** refactor, severidad baja, Aprobado.
- **Problema:** `api/app/main.py:101-104` tiene tres niveles de `if` para una regla.
- **Cambio propuesto:** función pura `is_open_high_priority(priority, status)` que devuelva
  `priority == PRIORITY_HIGH and status not in CLOSED_STATUSES`, con `CLOSED_STATUSES = {STATUS_DONE, STATUS_ARCHIVED}`.
  El contador usa esa función.
- **Archivos:** `api/app/services/tasks.py`.
- **Caracterización antes de tocar:** prueba de `summary` con una tarea HIGH en cada estado
  (TODO cuenta; DONE y ARCHIVED no cuentan) y una MEDIUM abierta (no cuenta).
- **Contrato que se mantiene:** `highPriorityOpen` con el mismo valor.

### H-API-13: Duplicación de SQL, columnas y datos de siembra

- **Hallazgo:** refactor, severidad baja, Aprobado.
- **Problema:** la lista de columnas se repite en tres consultas (`api/app/main.py:70`, `:87`);
  las tres sentencias de siembra son casi idénticas (`api/app/main.py:40-42`); `HIGH`, `DONE` y
  `ARCHIVED` aparecen como literales (`:70`, `:101-103`).
- **Cambio propuesto:** constante `TASK_COLUMNS` y función `as_task` en un solo lugar;
  `SEED_TASKS` como lista de tuplas con `executemany`; constantes de estado y prioridad compartidas
  con H-API-11.
- **Archivos:** `api/app/database.py`, `api/app/repositories/tasks.py`, `api/app/config.py`.
- **Caracterización antes de tocar:** prueba de siembra (2 tareas para `student`, 1 para `trainer`).
- **Contrato que se mantiene:** datos sembrados idénticos.

---

### Riesgos y verificación pendiente

- Ninguna prueba de este plan se ha ejecutado. El resultado base de `python tools/lab.py test api`
  queda pendiente (pendiente 6).
- Los cambios marcados "Pendiente de aprobación" no se implementan hasta que el responsable los apruebe.
- Los CVE de H-API-05 y H-API-06 se confirmarán con `pip-audit` al implementar.

---

## Ejecución (implementación de api)

Aprobaciones usadas: H-API-01, 07, 10, 12 y 13 sin decisión pendiente; urllib3 2.6.3;
python-multipart 0.0.26; owner ajeno 403; error de backend 502 genérico; PyJWT; carga de
archivos aprobada (.txt/.md, 1 MiB); CORS sin cambios (H-API-08 pendiente); esquemas restrictivos
aprobados (H-API-11). Pendiente 6 cerrado con la ejecución de abajo.

### Registro de ejecuciones (componente api)

| Fase | Comando (cwd `api/`) | IDs | Resultado |
|------|----------------------|-----|-----------|
| Base (código original) | `python tools/lab.py test api` | H-API-01..13 | 4 passed, 91.07% cobertura |
| Antes de cambiar (pruebas de corrección y caracterización nuevas) | `.venv\Scripts\python.exe -m pytest -p no:warnings -o addopts="" -rfE -q` | H-API-01..13 | 14 failed, 20 passed (fallos esperados de corrección y de versiones) |
| Después de cambiar | `.venv\Scripts\python.exe -m pytest -p no:warnings -o addopts="" -rfE -q` | H-API-01..13 | 33 passed |
| Después, comando oficial | `python tools/lab.py test api` | H-API-01..13 | 33 passed, cobertura total 98.47% (mínimo 85%) |

Nota: `pip-audit` no está instalado; la confirmación de CVE queda pendiente (ver abajo).

### Evidencia por hallazgo

- **H-API-01 (SQL):** caracterización de conteos y siembra antes/después; corrección con `O'Brien` y
  inyección por owner (fallaban antes con error SQLite, pasan después). Código: api/app/repositories/tasks.py.
- **H-API-02 (archivos):** caracterización de nombre y tamaño (201) antes/después; corrección de
  traversal, sobrescritura (409), `.exe` (422) y 1 MiB+1 (413): fallaban antes, pasan después.
  Código: api/app/services/files.py.
- **H-API-03 (JWT):** caracterización de token legado antes (aceptado) y después (401, cambio aprobado).
  Corrección de JWT firmado, token forjado y expirado: fallaba antes con 401, pasa después.
  Código: api/app/security.py.
- **H-API-04 (owner):** caracterización de owner igual a identidad; corrección de owner ajeno en
  listado, resumen y creación (403): fallaba antes, pasa después. Código: api/app/services/tasks.py.
- **H-API-05 y H-API-06 (dependencias):** prueba de versión en api/tests/test_dependencies.py
  fallaba antes (urllib3 2.5.0 y python-multipart 0.0.21) y pasa después con 2.6.3 y 0.0.26.
- **H-API-07 (detalle de error):** prueba de detalle exacto del 401 fallaba antes; pasa después.
- **H-API-08 (CORS):** la prueba de caracterización `test_cors_preflight_reflects_any_origin_with_credentials`
  pasa antes y después. Sin cambio, según decisión. Pendiente.
- **H-API-09 (captura amplia):** caracterización de relay del upstream pasa antes y después; la
  prueba de backend inalcanzable pasa a 502 genérico (fallaba antes). Código: api/app/services/health.py.
- **H-API-10 (capas):** la suite completa pasa después; api/app/main.py solo compone la aplicación.
- **H-API-11 (Pydantic):** título numérico y estado desconocido responden 422; título vacío 422. Código: api/app/schemas.py.
- **H-API-12 (condicionales):** caracterización de `summary` (total 7, highPriorityOpen 3) pasa antes y después.
- **H-API-13 (duplicación):** la siembra y la suite completa pasan después. Código: api/app/database.py.

### Desviaciones del plan

1. Formato del token: legado Base64 ahora responde 401 (cambio aprobado). Requiere que `auth/` emita JWT
   con iss `reqflow-auth`, aud `reqflow-api` y el secreto compartido. No verificado (otro componente).
2. Título numérico responde 422 en vez de guardarse como texto (aprobado con H-API-11).
3. Owner vacío en POST toma la identidad del token (antes se guardaba "").
4. Backend inalcanzable responde 502 genérico (aprobado); el PLAN decía "sin 5xx nuevos", queda superado.
5. Decodificación del cuerpo upstream con `errors="replace"`.
6. Los enums de estado y prioridad viven en api/app/schemas.py, no en config.py.
7. Se corrigió la prueba de CORS: con `allow_credentials=True`, Starlette refleja el origen y no envía `*`.
   La hipótesis original quedó refutada; se mantiene el comportamiento observado.

### Pendientes abiertos

- Coordinar con `auth/` el formato y los claims del JWT (H-API-03).
- Desplegar `WORKSHOP_JWT_SECRET`; sin él, la aplicación no arranca (RuntimeError al importar).
- Lista de orígenes CORS del frontend (H-API-08 sigue abierto).
- Ejecutar `pip-audit` para confirmar CVE de H-API-05 y H-API-06 (no instalado).
- Advertencias no bloqueantes: `@app.on_event("shutdown")` está deprecado (api/app/main.py:39) y la
  clave de prueba de 30 bytes en la prueba de token forjado dispara InsecureKeyLengthWarning.
- Aprobación humana de los cambios de contrato listados en Desviaciones: pendiente de confirmar por el responsable.

## Revisión local del diff (api)

Revisión sobre el diff local de `api/` contra `main`. Rama actual: `main`; el encargo esperaba `day1/prompting`,
no se cambió de rama. Sin cambios de código en esta revisión.

### Bloqueantes (regresan a "Pendiente" en HALLAZGOS.md)

- **H-API-05 y H-API-06 (dependencias).** `api/tests/test_dependencies.py` valida el entorno instalado vía
  `importlib.metadata`, no el pin de `api/requirements.txt:4-5`. No hay evidencia de `pip-audit`, así que los
  rangos de CVE siguen sin confirmar.
- **H-API-11 (tipado).** Las salidas siguen como `dict[str, Any]`: `api/app/services/tasks.py:20,24,31,45`,
  `api/app/routes/tasks.py:10,16,21,27`, `api/app/routes/requirements.py:17`, `api/app/routes/health.py:11,15`.
  La entrada sí usa Pydantic (`api/app/schemas.py`); la salida no.
- **H-API-13 (duplicación).** `INSERT_SEED_SQL` (`api/app/database.py:10`) repite `INSERT_TASK_SQL`
  (`api/app/repositories/tasks.py:8`). La lista de columnas aparece en `api/app/database.py:5`,
  `api/app/repositories/tasks.py:4` y `:8`. Un cambio de esquema toca cuatro lugares.

### Importantes (no bloquean el cierre de los demás)

- `api/tests/support.py:10` conserva `LEGACY_SECRET = "WORKSHOP_SECRET_2026"`. Es un valor de prueba, pero es el
  literal nombrado en H-API-03.
- `api/app/security.py` no valida que `sub` y `role` sean cadenas no vacías. Verificado: `sub` como objeto
  responde 401, pero `sub: ""` responde 200 con 0 tareas (owner vacío aceptado). Faltan pruebas de `alg=none`
  (verificado: 401 ya en el comportamiento) y de `sub` ausente o no textual.
- Sin longitud mínima para `WORKSHOP_JWT_SECRET` (`api/app/security.py`, `load_jwt_secret`).
- `storedAt` expone la ruta absoluta del servidor (`api/app/services/files.py:25`). Verificado en la respuesta
  `POST /api/requirements`: `C:\...\up\a.txt`. Conviene devolver solo el nombre.
- `api/app/services/health.py` lee el cuerpo upstream completo en memoria (`response.data`) sin tope de tamaño.
- `api/tests/test_security.py` fija el comportamiento CORS que refleja `https://evil.example` con credenciales.
  Debe invertirse al resolver H-API-08.
- Literales de estado HTTP (201, 401, 403, 409, 413, 422, 502) y `+ 1` en `api/app/routes/requirements.py`,
  contra la regla 12 de AGENTS.md.
- `api/app/main.py`: `app = create_app()` a nivel de módulo crea `./data` y `./uploads` y abre la base al importar.

### Sugerencias

- El 422 por defecto de Pydantic repite valores de entrada (alcance de H-API-07).
- SQLite con `check_same_thread=False` y una sola conexión compartida desde rutas síncronas (preexistente).
- `Path(...).name` no sanitiza otros caracteres; falta prueba de límite exacto de 1 MiB.
- `test_dependencies` debería leer `requirements.txt` en lugar del entorno.

### Documentos consultados

README.md, RETO.md, docs/GOOD_PRACTICES.md, prompts/HALLAZGOS.md, prompts/PLAN.md, prompts/api.md, AGENTS.md.
No existen docs/ENDPOINTS.md ni docs/TESTING.md.

## Segunda revisión local del diff (api)

Fecha: 2026-11-02. Rama actual: `main`, no `day1/prompting`. `git diff main -- api/` solo muestra
3 archivos modificados; los archivos nuevos aparecen en `git status --short` y se revisaron aparte.
Ejecución: `api\.venv\Scripts\python.exe -m pytest -p no:warnings -q --cov=app` con cwd `api/`
(componente api, IDs H-API-01 a H-API-13): 33 pasadas, cobertura total 98 %.

### Bloqueantes (regresan a "Pendiente")

- H-API-03: el literal del secreto antiguo `WORKSHOP_SECRET_2026` sigue en api/tests/support.py:10.
  El hallazgo cita el secreto embebido en el código y en las pruebas; la prueba lo sigue usando.
  Corrección: usar un valor de prueba que no sea el secreto antiguo y comprobar con búsqueda que el
  literal no queda en api/.

### Importantes (no regresan)

- Consumo de memoria: api/app/services/health.py:13 lee el cuerpo completo del backend y
  api/app/routes/health.py:18 lo devuelve al cliente. No hay límite de tamaño.
- Fuga de información en la subida: api/app/services/files.py:25 devuelve `storedAt` con la ruta
  absoluta del servidor, y el directorio de subida es compartido entre owners, así que el 409 de
  api/app/services/files.py:23 revela nombres de archivos de otros owners.
- Token: api/app/security.py:58 acepta `sub` vacío; `resolve_owner` (api/app/services/tasks.py:13)
  trata "" como identidad. Solo emite el secreto, pero conviene exigir `sub` no vacío.
- CORS: api/app/main.py:29 sigue con `allow_origins=["*"]`. H-API-08 permanece "Aprobado" y
  api/tests/test_security.py:69 fija la reflexión de cualquier origen; debe invertirse al corregir.

### Sugerencias

- api/app/repositories/tasks.py:2 importa `Path` sin usarlo. El componente api no tiene linter
  configurado; conviene añadirlo solo si se aprueba como herramienta de desarrollo.
- Los 422 de FastAPI devuelven el `input` enviado (ver docs/ENDPOINTS.md); no hay manejador de
  `RequestValidationError` en api/app/main.py.

### Estado tras esta revisión

- Resuelto (verificados): H-API-01, 02, 04, 07, 09, 10, 12.
- Pendiente: H-API-03 (nuevo, bloqueante), 05, 06, 11, 13.
- Aprobado (abierto): H-API-08.

### Documentos consultados

prompts/HALLAZGOS.md y prompts/PLAN.md (secciones de api), y el código de api/. No releí README.md,
RETO.md, docs/GOOD_PRACTICES.md ni docs/ENDPOINTS.md en esta pasada; las observaciones se basan en el
código citado.
