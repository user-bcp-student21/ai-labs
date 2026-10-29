# Diseño: Reducir la persistencia del token de autenticación en web

Estado: borrador pendiente de aprobación humana. No contiene código funcional.

Referencias: [proposal.md](./proposal.md), [spec.md](./specs/web-session-token/spec.md), Issue `user-bcp-student21/ai-labs#25`, hallazgo `H-WEB-01`.

## 1. Contexto técnico

Componente: `web/` (Angular standalone, pruebas con Vitest 3.2.4, `environment: 'node'` en [vitest.config.ts](../../../web/vitest.config.ts)). Sin entorno DOM.

Estado observado en el código de `HEAD` (`40e280d`), fuente de verdad para este diseño:

- [session-token.ts](../../../web/src/app/session/session-token.ts) es el único módulo que accede al token. Guarda, lee y limpia `workshop_token` en `sessionStorage`. `clearSessionToken()` además borra `workshop_token` de `localStorage` como limpieza de versiones anteriores.
- [login.component.ts](../../../web/src/app/login/login.component.ts) llama a `saveSessionToken` tras un login con `token` truthy. Escribe `workshop_user` y `workshop_preferences` en `localStorage`.
- [dashboard.component.ts](../../../web/src/app/dashboard/dashboard.component.ts) llama a `readSessionToken()`. Si no hay token navega a `/login` sin consultar. Si lo hay, envía `GET /api/tasks?owner=<username>` con header `Authorization` de esquema Bearer. Logout ejecuta `clearSessionToken()`, borra `workshop_user` y navega a `/login`.

Discrepancias documentales (no se corrigen en este cambio):

- `HALLAZGOS.md` (H-WEB-01), `HU-01.md`, `PLAN.md` y `docs/ENDPOINTS.md` (líneas 44, 77, 95, 152) describen el token en `localStorage`. Sus referencias de línea no corresponden al `HEAD`.
- Los specs [auth-flow.spec.ts](../../../web/src/app/auth-flow.spec.ts), [login.component.spec.ts](../../../web/src/app/login/login.component.spec.ts) y [dashboard.component.spec.ts](../../../web/src/app/dashboard/dashboard.component.spec.ts) contienen marcadores de conflicto de merge (`<<<<<<< HEAD`, `=======`, `>>>>>>> b8c0b65`) sin resolver. El lado `HEAD` usa `sessionStorage`; el lado `b8c0b65` usa `localStorage`. Mientras existan, ninguna suite de login/dashboard puede ejecutarse.

Implicación: el comportamiento de producción ya cumple gran parte de la spec. El trabajo principal es resolver los specs, caracterizar el comportamiento real y decidir el riesgo residual de `sessionStorage`.

## 2. Goals

- G1. Ningún flujo (login, consulta de tareas, logout) escribe ni deja el token en `localStorage`.
- G2. Logout elimina el token vigente y el heredado en `localStorage`, y una navegación posterior a `/dashboard` no reutiliza la sesión anterior.
- G3. Sin token, el dashboard no envía `GET /api/tasks` y navega a `/login`.
- G4. Con token, la consulta conserva endpoint, parámetro `owner`, header Bearer y forma de la respuesta consumida.
- G5. Cubrir con pruebas los criterios de aceptación del Issue y los escenarios de la spec.
- G6. Entregar el cambio en fases pequeñas, revisables por PR, solo en `web/`.

## 3. Non-goals

- NG1. No emitir ni consumir cookies `HttpOnly`; no modificar `auth/` ni `api/`.
- NG2. No cambiar `workshop_user` ni `workshop_preferences`.
- NG3. No corregir `H-WEB-02` (`[innerHTML]` en el mensaje de login), `H-WEB-03` (separación HTTP/sesión/navegación), `H-WEB-04` (tipado `any`) ni `H-WEB-05` (dependencias).
- NG4. No invalidar el token en el servidor al cerrar sesión; no existe endpoint documentado para ello.
- NG5. No agregar dependencias ni entorno DOM (por ejemplo jsdom o happy-dom) en este cambio.
- NG6. No marcar hallazgos como `Resuelto` ni corregir `docs/ENDPOINTS.md` en este cambio; se hará en una fase documental posterior con evidencia y revisión humana.
- NG7. No crear un servicio nuevo de estado del navegador en esta fase (ver decisión D2).

## 4. Contratos protegidos

Deben permanecer sin cambios. Fuente: [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md) y código actual.

| Contrato | Valor que debe preservarse |
|---|---|
| Login: request | `POST http://localhost:8080/auth/login`, body `{ username, password, client: "angular-workshop" }`, `timeout: 5000`. |
| Login: éxito | `response.data.token` truthy: guarda token y usuario, preferencias, navega a `/dashboard`. |
| Login: sin token | Muestra "El backend respondió sin token."; no navega ni guarda sesión. |
| Login: error | Muestra mensaje de error; no navega. |
| Tareas: request | `GET http://localhost:8000/api/tasks?owner=<username>`; `owner` vacío si no hay usuario; header Bearer. |
| Tareas: 401 o error | Muestra `detail`, `message` o texto por defecto; termina la carga. **No borra el token ni redirige** (ENDPOINTS, sección de error). Contrato no listado en el proposal y debe agregarse a las pruebas. |
| Tareas: filtrado y orden | Excluye `ARCHIVED`; ordena por `priority` con el mismo comparador. |
| Dashboard sin token | No envía solicitud; navega a `/login`. |
| Logout | Borra token y `workshop_user`; conserva `workshop_preferences`; navega a `/login`; no llama a endpoint remoto. |

## 5. Componentes afectados

| Archivo | Impacto en este cambio |
|---|---|
| `web/src/app/session/session-token.ts` | Único punto de cambio de producción previsto (solo si se aprueba D1 o D3). |
| `web/src/app/login/login.component.ts` | Sin cambio previsto en la fase 1; solo se caracteriza. |
| `web/src/app/dashboard/dashboard.component.ts` | Sin cambio previsto en la fase 1; solo se caracteriza. |
| `web/src/app/auth-flow.spec.ts` | Resolver conflicto y agregar caso de logout posterior. |
| `web/src/app/login/login.component.spec.ts` | Resolver conflicto y agregar aserciones de `localStorage` sin token. |
| `web/src/app/dashboard/dashboard.component.spec.ts` | Resolver conflicto; agregar caso de 401 sin limpieza, y logout sin reutilización. |
| `docs/ENDPOINTS.md`, `HALLAZGOS.md`, `HU-01.md`, `PLAN.md` | Fuera de este cambio de código; actualización documental posterior. |

## 6. Decisiones técnicas y alternativas

### D1. Dónde vive el token en el cliente (decisión principal, requiere confirmación humana)

| Opción | Descripción | Ventajas | Desventajas |
|---|---|---|---|
| **A. `sessionStorage` centralizado (recomendada para esta fase)** | Estado actual de `HEAD`. Se conserva `session-token.ts` como acceso único. | Sin cambio de backend ni de contrato. Cumple la spec (no usa `localStorage`). Se borra al cerrar la pestaña. | Sigue siendo legible por JavaScript del mismo origen. Nueva pestaña exige login. |
| B. Solo memoria | Token en variable de módulo; sin persistencia. | Mínima persistencia. | Una recarga de página cierra la sesión y redirige a `/login`. Cambio observable grande. Sigue legible por JS que corra en la página. |
| C. Cookie `HttpOnly` emitida por el backend | El token no es accesible desde JS. | Mitigación real del riesgo de lectura por script. | Requiere cambios en `auth/` y `api/`, CORS con credenciales, política `SameSite` y protección CSRF. Queda fuera de alcance (proposal). Debe ser una propuesta posterior. |
| D. Híbrido memoria + `sessionStorage` | Memoria como fuente y `sessionStorage` para recargas. | Equilibrio. | Más complejidad sin evidencia de necesidad en el alcance actual. |

Recomendación: opción A en esta fase, con aceptación explícita del cambio de duración (el dato se pierde al cerrar la pestaña) y registro del riesgo residual. Si el equipo exige eliminar la lectura desde JavaScript, la ruta es la opción C en una propuesta separada.

### D2. Punto de acceso al almacenamiento

- Alternativa del PLAN: crear `web/src/app/services/browser-state.service.ts`.
- Decisión propuesta: mantener `session-token.ts` como único acceso al token. Ya centraliza la lógica, y un servicio nuevo sería churn sin beneficio para este hallazgo. La separación HTTP/sesión/navegación pertenece a `H-WEB-03`.
- Trade-off: diverge del PLAN; debe registrarse en la revisión.

### D3. Limpieza del token heredado en `localStorage` (decisión opcional)

- Estado actual: la limpieza ocurre solo en logout. Un usuario que nunca cierra sesión conserva el token heredado en `localStorage` indefinidamente.
- Opción a (base): mantener solo la limpieza en logout, tal como exige la spec.
- Opción b: además, eliminar `workshop_token` de `localStorage` al guardar un login exitoso. Es barato y no cambia contratos, pero agrega comportamiento no exigido por la spec.
- Recomendación: opción b si el humano la aprueba; de lo contrario, opción a y registrar el riesgo.

### D4. Esquema de autorización

Se mantiene el esquema Bearer tal como está. No se cambia el formato del header.

## 7. Estrategia incremental

Cada fase es un PR o commit revisable. Ninguna fase cambia comportamiento antes de tener caracterización verde.

**F0. Resolver los conflictos de los specs (sin tocar producción).**
- Resolver los tres archivos con el lado `HEAD` (`sessionStorage`), coherente con el código actual.
- Confirmar con revisión humana que el lado `HEAD` es el deseado antes de cerrar la fase.

**F1. Caracterización contra el código actual.**
- Ejecutar `python tools/lab.py test web` (o `npm test` desde `web/`).
- Criterio de salida: todas las pruebas de caracterización en verde, sin modificar producción.
- Si alguna falla, detenerse: el comportamiento real difiere de la spec y debe analizarse antes de continuar.

**F2. Aserciones de la spec que faltan.**
- Login: el token no aparece como valor en ninguna clave de `localStorage`.
- Logout: se elimina `workshop_token` de `sessionStorage` y de `localStorage`; `workshop_preferences` se conserva.
- Logout seguido de `ngOnInit` del dashboard: no hay `axios.get`, navega a `/login`.
- 401: no borra el token ni redirige (contrato de ENDPOINTS).
- Respuesta de login sin `token`: mensaje exacto y sin navegación.
- Filtrado `ARCHIVED` y orden por `priority`.
- Criterio de salida: estas pruebas pasan sin cambios de producción. Si alguna falla, el defecto se documenta en un PR aparte antes de tocar producción.

**F3. Ajustes de producción (solo si se aprueban D1 o D3).**
- Cambios limitados a `session-token.ts`. Sin cambios en login ni dashboard salvo necesidad demostrada por las pruebas.

**F4. Verificación.**
- Pruebas y build de `web/`.
- Cobertura del código modificado: meta de 85 % o más (AGENTS, sección web).
- Revisión humana y pruebas reales antes de cualquier integración. Día 1: solo ramas locales, sin push.

**F5. Documentación (posterior).**
- Corregir `docs/ENDPOINTS.md` (almacenamiento y contrato 401) y las referencias de `HALLAZGOS.md` con evidencia real.
- No marcar `H-WEB-01` como resuelto: el riesgo residual permanece.

## 8. Pruebas de caracterización necesarias antes de modificar comportamiento

| # | Caso | Archivo | Aserción clave |
|---|---|---|---|
| C1 | Login exitoso | login.component.spec.ts / auth-flow.spec.ts | Token en `sessionStorage`; ninguna clave de `localStorage` contiene el token; navega a `/dashboard`. |
| C2 | Login sin token | login.component.spec.ts | Mensaje "El backend respondió sin token."; sin navegación; sin token guardado. |
| C3 | Dashboard sin token | dashboard.component.spec.ts | Sin `axios.get`; navega a `/login`. |
| C4 | Consulta con token | dashboard.component.spec.ts / auth-flow.spec.ts | URL con `owner`, header Bearer, token no leído de `localStorage`. |
| C5 | 401 sin limpieza | dashboard.component.spec.ts | `error` mostrado; token conservado; sin navegación. |
| C6 | Logout con token heredado | dashboard.component.spec.ts | Token eliminado de ambos almacenes; preferencias conservadas; navega a `/login`. |
| C7 | Logout y reingreso al dashboard | auth-flow.spec.ts | Tras logout, sin `axios.get`, navega a `/login`. |
| C8 | Filtrado y orden | dashboard.component.spec.ts | `ARCHIVED` excluido; orden por `priority`. |

Los valores son ficticios (`fake-token`, `student`). Las aserciones no deben imprimir el valor del token en logs; los fallos de Vitest pueden mostrarlo, por lo que se prefieren valores de prueba sin relación con credenciales reales.

## 9. Riesgos y trade-offs

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R1 | `sessionStorage` sigue legible por JavaScript del mismo origen. | El riesgo de H-WEB-01 no se elimina por completo. | Registrar riesgo residual. La mitigación real es D1-C y depende de `auth/` y `api/`. |
| R2 | `H-WEB-02` (`[innerHTML]` con nombre ingresado) es un vector de ejecución de script en el mismo origen. | Facilita la lectura del token pese a D1-A. | Fuera de alcance; debe tratarse en su propio cambio y se menciona como dependencia. |
| R3 | Cambio de duración: al cerrar la pestaña se pierde la sesión; una nueva pestaña no la comparte. | Cambio observable para el usuario. | Aceptación explícita en la decisión D1. |
| R4 | Token heredado en `localStorage` persiste hasta logout. | Exposición prolongada de un token antiguo. | D3-b, si se aprueba. |
| R5 | Logout no invalida el token en el servidor. | Un token copiado sigue siendo válido hasta su expiración. | Fuera de alcance; la expiración y la revocación no están documentadas (ENDPOINTS, preguntas abiertas). |
| R6 | Los specs con conflictos no son ejecutables. | Resolver al lado incorrecto alteraría la caracterización. | F0 con revisión humana; `HEAD` como referencia de producción. |
| R7 | Pruebas que pasan sin cambios de producción dan falsa confianza en la migración. | No se verifica el almacenamiento real. | Aserciones explícitas por clave y almacén (C1, C6). |
| R8 | Documentación desfasada (`localStorage`). | Revisores pueden diseñar sobre un estado falso. | F5; este diseño toma el código como fuente de verdad. |
| R9 | Entorno `node` sin DOM. | No se prueba el render real del mensaje de login. | Coherente con NG5; la verificación de DOM se trata en otro cambio. |

## 10. Rollback

- Cada fase es un commit o PR independiente. Revertir la fase restaura el comportamiento anterior.
- No hay migración de datos ni cambio de backend. Los tokens se reemiten en el siguiente login.
- Revertir F3 solo elimina la limpieza adicional o el cambio de almacenamiento; no requiere limpieza manual, porque las claves afectadas se eliminan en logout.
- Volver a `localStorage` reintroduce H-WEB-01. Solo debe hacerse con justificación explícita y registrada.
- Durante el Día 1 el rollback es local (ramas `day1/prompting`, `main`, `checkpoint/day1`); no hay push ni PR.

## 11. Validación de este documento

Este entregable es documental. No se ejecutaron pruebas ni build. Las pruebas de F1 y F2 no se han ejecutado; el resultado real debe registrarse en la fase correspondiente y no afirmarse aquí.
