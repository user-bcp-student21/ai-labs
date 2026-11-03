## Alcance del análisis (componentes, rutas o carpetas)
`web/src/app/login/`, `web/src/app/dashboard/`, `web/src/app/app.routes.ts` y `web/nginx.conf`.
Fuera del alcance: backend (`auth/`, `api/`), infraestructura y rediseño visual.

## Stack y versiones (framework, router, cliente HTTP)
Angular 21.2.19 (componentes standalone), `@angular/router` 21.2.19, axios y lodash (`merge`).

## Mecanismo de autenticación (cookie, token en memoria, token en almacenamiento del navegador)
Token Bearer devuelto por `POST /auth/login`, guardado en `localStorage` (`workshop_token`, `workshop_user`) y enviado en el header `Authorization` a `/api/tasks`.

## Fuentes de contenido no confiable (entrada de usuario, respuestas de API, parámetros de URL)
Campo `username` del formulario de login, mensaje de error del backend, datos de tareas (`title`, `description`) y `user.username` usado como parámetro `owner` en la consulta.

## Políticas de seguridad vigentes (CSP, CORS, cabeceras, estándares internos)
No hay CSP ni cabeceras de seguridad definidas en `nginx.conf`. Estándar interno: no ocultar alertas de seguridad ni reducir quality gates.

## Archivos o fragmentos de código a revisar
- `web/src/app/login/login.component.ts`: mensajes HTML con `username` y respuesta del backend, escritura en `localStorage`, `merge` de preferencias.
- `web/src/app/login/login.component.html`: renderizado de `message`.
- `web/src/app/dashboard/dashboard.component.ts`: lectura del token, URL con `owner`, logout.
- `web/src/app/dashboard/dashboard.component.html`: renderizado de datos de tareas.
- `web/src/app/app.routes.ts`: ruta `dashboard` sin guard.
- `web/nginx.conf`: cabeceras de respuesta.

## Known risks / hallazgos previos
Posible XSS por mensajes HTML con el usuario; token en `localStorage`; ruta `dashboard` sin guard; ausencia de CSP; `merge` sobre datos de `localStorage` (prototype pollution).

## Dependencias
Contrato de `/auth/login` y `/api/tasks` (no debe cambiar) y pruebas existentes en `web/` (`python tools/lab.py test web`).

## Definition of Done del equipo (DoD)
Reporte con severidad, archivo y línea, evidencia redactada y mitigación por hallazgo; pruebas de sanitización y guardas de ruta; cobertura del código modificado ≥ 85%; PR revisado.
