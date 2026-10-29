# Propuesta: Reducir la persistencia del token de autenticación en web

## Referencia

- Issue: [user-bcp-student21/ai-labs#25](https://github.com/user-bcp-student21/ai-labs/issues/25) — "HU-01: Reducir la persistencia del token de autenticación".
- Hallazgo: `H-WEB-01` (Token de sesión almacenado en almacenamiento accesible desde JavaScript), estado `Pendiente` en `HALLAZGOS.md`.
- Baseline de comportamiento: [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md).

## Por qué importa

El token Bearer permite consultar tareas en nombre del usuario. Mientras esté en un almacenamiento legible por JavaScript del mismo origen, cualquier script que se ejecute en la página puede leerlo. El Issue señala un riesgo potencial de exposición; no afirma que el token haya sido robado.

## Estado actual observado (y discrepancia con el Issue)

El Issue y `docs/ENDPOINTS.md` describen el token en `localStorage` bajo `workshop_token`. En el código de `HEAD` (`40e280d`) ese estado ya no aplica:

- `web/src/app/session/session-token.ts` guarda el token en `sessionStorage` (`workshop_token`).
- `clearSessionToken()` elimina el token de `sessionStorage` y también de `localStorage`, para limpiar restos de versiones anteriores.
- `web/src/app/login/login.component.ts` llama a `saveSessionToken` y **no** escribe el token en `localStorage`; sí escribe `workshop_user` y `workshop_preferences` en `localStorage`.
- `web/src/app/dashboard/dashboard.component.ts` lee el token mediante `readSessionToken()` y envía `Authorization: Bearer <token>`.

Por tanto, el cambio no debe asumir que el token está en `localStorage`. Las specs fijan el comportamiento observable que debe cumplirse y la alternativa de almacenamiento queda como decisión pendiente (ver más abajo). `docs/ENDPOINTS.md` no se modifica en esta propuesta; su descripción de almacenamiento queda desactualizada respecto del código y debe corregirse en una tarea posterior.

## Alcance

- Garantizar que el token de autenticación no se persista en `localStorage` en ningún flujo (login, consulta de tareas, logout).
- Eliminar cualquier token heredado en `localStorage` durante el logout (comportamiento ya presente; debe quedar cubierto por pruebas).
- Decidir y documentar la alternativa de manejo de sesión que reemplace el almacenamiento accesible desde JavaScript (`sessionStorage` sigue siendo legible por JavaScript del mismo origen; la decisión queda abierta en esta propuesta).
- Mantener el flujo observado: login, consulta autenticada de tareas y cierre de sesión.
- Pruebas automatizadas con valores ficticios aislados que cubran los cinco criterios de aceptación del Issue.

## Fuera de alcance

- Cambiar el contrato de `POST /auth/login` ni el de `GET /api/tasks` (ver comportamiento a preservar).
- Cambiar la persistencia de `workshop_user` y `workshop_preferences` en `localStorage`; solo se trata el token.
- Implementar cambios en `api/` o `auth/`, incluida la emisión de cookies desde el backend, salvo que la decisión de diseño lo requiera en una propuesta posterior.
- Corregir CodeQL, Dependency Review, JaCoCo o cualquier quality gate.
- Diseño técnico detallado, tareas (`tasks.md`) y cambios de código: se harán en fases posteriores.

## Comportamiento que debe preservarse

Según `docs/ENDPOINTS.md`:

1. `POST http://localhost:8080/auth/login` con body `{ username, password, client: "angular-workshop" }` y timeout de 5000 ms.
2. Login exitoso: la respuesta contiene `token` truthy; el cliente navega a `/dashboard`. Si falta `token`, muestra "El backend respondió sin token." y no navega.
3. Login fallido: muestra el mensaje de error y no navega.
4. `GET http://localhost:8000/api/tasks?owner=<username>` con `Authorization: Bearer <token>`; sin token, no se solicita la lista y se navega a `/login`.
5. Filtrado de tareas `ARCHIVED` y orden por `priority` en el dashboard.
6. Logout: limpia la sesión local y navega a `/login`. No llama a un endpoint remoto.

El contrato de respuesta de login (`token`, `user`) y el de tareas no cambian. Los códigos HTTP exactos siguen siendo preguntas abiertas en `docs/ENDPOINTS.md`; esta propuesta no los fija.

## Decisiones abiertas

- Alternativa de almacenamiento para el token (por ejemplo, cookie `HttpOnly` emitida por el backend, o memoria de la aplicación sin persistencia). La propuesta no la elige; la spec exige que la decisión esté documentada antes de implementar.
- Si `sessionStorage` cumple el requisito de "no persistir en almacenamiento accesible desde JavaScript" o debe reemplazarse. La spec no lo presupone.
