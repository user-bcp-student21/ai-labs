## Business context (brief)
La aplicación web de login y tablero (`web/`) crece y el equipo necesita
estandarizar cómo se desarrolla el frontend Angular para que los cambios
sean consistentes, revisables y seguros.

## Feature request / user story
Como desarrollador frontend, quiero lineamientos y estándares de Angular
aplicados a un cambio concreto en la pantalla de login (`web/src/app/login/`)
para que el componente separe la llamada HTTP en un servicio, use tipos
explícitos y mantenga el contrato de `/auth/login`.

## Expected impact
Reducir a cero los `any` nuevos y los componentes que llaman HTTP directamente
en el cambio, y alcanzar 85% o más de cobertura en el código modificado.

## Scope (in/out)
In: extracción de la llamada HTTP de login a un servicio, modelos tipados de
petición y respuesta, centralización de la clave de sesión y de la URL base,
pruebas de caracterización con Vitest.
Out: cambios en `api/` o `auth/`, rediseño visual, nuevas rutas, cambios en
`nginx.conf` y nuevas dependencias.

## Known technical constraints
Angular 21.2.19 con componentes standalone y rutas `loadComponent`, TypeScript
en modo estricto, Vitest 3.2, Node >= 22.12. Debe conservarse el endpoint
`POST /auth/login` y el formato de su respuesta.

## Known risks
Exposición del token de sesión en consola o mensajes de error; cambios en la
clave de `localStorage` que cierren sesiones activas; regresión en la
redirección entre `/login` y `/dashboard`.

## Dependencies
Contrato del servicio `auth` (`POST /auth/login`) y ruta `/dashboard` existente.

## Team Definition of Done (DoD)
Pruebas de Vitest en verde, `npm run build` sin errores, cobertura del código
modificado de 85% o más, sin secretos en el código y PR revisado.
