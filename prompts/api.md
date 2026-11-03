AMBITO
Workspace ai-labs abierto en su raiz. Lee codigo solo en api/.
Todas las rutas parten de la raiz. Lee README.md, RETO.md y
docs/ generales. Este pedido es de solo lectura; no escribas archivos.
Git se ejecuta desde la raiz; las pruebas propuestas usan cwd api/.
No leas ni modifiques codigo de auth/ ni web/. Usa IDs H-API-NN y componente api.

CONTEXTO
ai-labs expone endpoints de tareas en api/app/main.py: GET /api/tasks,
POST /api/tasks, GET /api/summary y POST /api/requirements, todos protegidos
por legacy_identity (cabecera Authorization). Lee README.md,
RETO.md y docs/ENDPOINTS.md si existe. Localiza la ruta desde cada recurso
HTTP hasta la consulta a SQLite (sqlite3 en create_app). No des por cierta la lista de RETO.md.

OBJETIVO
Determinar si entradas de los endpoints (owner en query, payload JSON de
POST /api/tasks y owner en GET /api/summary) llegan concatenadas a una consulta SQL.

RESTRICCIONES
No edites codigo ni ejecutes ataques contra servicios remotos. Usa solo
codigo y datos ficticios locales (base SQLite temporal con datos sembrados).
Si falta un archivo o no puedes ejecutar una comprobacion, dilo. No cambies
contratos ni leas otros componentes.

CRITERIOS DE ACEPTACION
Identifica el recorrido de cada entrada hasta la consulta con archivo y linea
(referencias iniciales: api/app/main.py:67-71 list_tasks, 77-87 create_task,
90-93 summary). Distingue concatenacion, parametrizacion y cualquier caso no
comprobado. Propone una prueba local con owner valido (student), owner
invalido (inexistente) y entrada con comilla (student' OR '1'='1), con
resultado esperado segun el contrato observado en api/tests/test_api.py.
No afirmes que la prueba paso si solo la propusiste.

FORMATO DE RESPUESTA
Tabla: afirmacion | evidencia archivo:linea | comprobado o hipotesis |
prueba propuesta. Termina con preguntas abiertas y comandos no ejecutados.