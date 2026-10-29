# web-session-token

## ADDED Requirements

### Requirement: El token no se persiste en localStorage

El cliente web MUST NOT escribir el token de autenticación en `localStorage`, en ningún flujo.

#### Scenario: Login exitoso no escribe el token en localStorage
- **WHEN** el usuario envía credenciales válidas y `POST /auth/login` responde con un `token`
- **THEN** `localStorage` no contiene ninguna clave cuyo valor sea ese token
- **AND** la navegación continúa a `/dashboard`

#### Scenario: Token heredado en localStorage es eliminado al cerrar sesión
- **WHEN** existe un token heredado en `localStorage` y el usuario cierra sesión
- **THEN** ese token ya no está en `localStorage`
- **AND** la navegación va a `/login`

### Requirement: La consulta de tareas usa el token sin leerlo desde localStorage

Con una sesión válida, el dashboard MUST enviar `GET /api/tasks` con el header `Authorization: Bearer <token>` y MUST NOT obtener el token desde `localStorage`.

#### Scenario: Consulta autenticada conserva el header Bearer
- **GIVEN** una sesión válida establecida tras el login
- **WHEN** el usuario entra a `/dashboard`
- **THEN** la solicitud a `/api/tasks?owner=<username>` incluye `Authorization: Bearer <token>`
- **AND** el token no se lee desde `localStorage`

### Requirement: Sin sesión no hay consulta de tareas

Si no existe un token de sesión, el dashboard MUST NOT solicitar la lista de tareas y MUST navegar a `/login`.

#### Scenario: Acceso a dashboard sin sesión
- **GIVEN** que no existe un token de sesión
- **WHEN** el usuario entra a `/dashboard`
- **THEN** no se envía ninguna solicitud a `/api/tasks`
- **AND** la navegación va a `/login`

### Requirement: El cierre de sesión invalida el acceso local

Al cerrar sesión, el cliente MUST eliminar el token de sesión y MUST impedir que una consulta posterior reutilice la sesión anterior.

#### Scenario: Consulta posterior al logout no reutiliza la sesión
- **GIVEN** una sesión válida previa al logout
- **WHEN** el usuario cierra sesión y luego intenta entrar a `/dashboard`
- **THEN** el token de la sesión anterior ya no está disponible en el almacenamiento del cliente
- **AND** no se envía ninguna solicitud a `/api/tasks` con ese token
- **AND** la navegación va a `/login`

### Requirement: Los contratos de login y tareas se preservan

El cambio MUST preservar el contrato documentado en `docs/ENDPOINTS.md` para `POST /auth/login` y `GET /api/tasks`, salvo la forma de almacenar el token.

#### Scenario: Login envía el body documentado
- **WHEN** el usuario envía credenciales no vacías
- **THEN** la solicitud es `POST http://localhost:8080/auth/login` con `username`, `password` y `client: "angular-workshop"`
- **AND** usa un timeout de 5000 ms

#### Scenario: Respuesta de login sin token no inicia sesión
- **WHEN** la respuesta de login no contiene `token` truthy
- **THEN** se muestra "El backend respondió sin token."
- **AND** no se navega a `/dashboard`

#### Scenario: Filtrado y orden de tareas se mantienen
- **GIVEN** una respuesta de `/api/tasks` con tareas `ARCHIVED` y no archivadas
- **WHEN** el dashboard procesa la respuesta
- **THEN** las tareas `ARCHIVED` no se muestran
- **AND** las tareas visibles se ordenan por `priority`

### Requirement: Las pruebas no exponen credenciales

Las pruebas y los registros del cambio MUST usar valores ficticios aislados y MUST NOT imprimir ni registrar el valor del token.

#### Scenario: Prueba de login con credenciales ficticias
- **WHEN** se ejecuta la prueba de login exitoso
- **THEN** usa un token y credenciales ficticios
- **AND** ni la salida de la prueba ni los logs contienen el valor del token
