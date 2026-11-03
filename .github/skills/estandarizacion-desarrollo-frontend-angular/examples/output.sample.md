# Estandarización de desarrollo frontend con Angular -> Output

## 1. Summary
Aplicar los lineamientos de Angular al cambio de login en `web/`: extraer la
llamada HTTP a un servicio tipado, eliminar `any` nuevos, centralizar la URL
base y las claves de `localStorage`, y cubrir el cambio con pruebas de Vitest.
El endpoint `POST /auth/login` y su formato de respuesta se conservan.

## 2. Alcance del cambio
### Archivos afectados (propuestos)
- `web/src/app/login/login.component.ts`: quitar la llamada HTTP directa con `axios`, tipar campos y delegar en el servicio.
- `web/src/app/login/login.component.html`: revisar cómo se muestra `message` si contiene HTML armado con datos del usuario.
- `web/src/app/auth/auth.service.ts` (nuevo): encapsula `POST /auth/login` y devuelve un tipo explícito.
- `web/src/app/auth/auth.models.ts` (nuevo): tipos de petición y respuesta (`token`, `user`).
- `web/src/app/auth/auth.constants.ts` (nuevo): URL base y claves `workshop_token`, `workshop_user`, `workshop_preferences`.
- `web/src/app/login/login.component.spec.ts` (nuevo): pruebas de caracterización del flujo.

### Fuera del alcance
- Cambios en `api/` o `auth/` (backend Java).
- Rediseño visual, nuevas rutas y cambios en `nginx.conf`.
- Nuevas dependencias. `axios` y `lodash` se mantienen salvo decisión posterior.

## 3. Contratos preservados
- `POST /auth/login` con cuerpo `{ username, password, client: 'angular-workshop' }` y timeout de 5000 ms.
- Respuesta esperada con `token` y `user`.
- Claves de `localStorage`: `workshop_token`, `workshop_user`, `workshop_preferences`.
- Redirección a `/dashboard` tras un login exitoso.

## 4. Estándares aplicados
### Arquitectura y componentes
- El componente solo maneja estado de formulario, mensajes y navegación.
- Componente standalone y `ChangeDetectionStrategy.OnPush` en el cambio.
- Guard clauses para validar usuario y contraseña antes de llamar al servicio.

### Servicios y HTTP
- `AuthService` concentra la petición y el manejo de errores en un único punto.
- La URL base sale de `auth.constants.ts`; ningún componente construye URLs.

### Tipado y estado
- Se eliminan los `any` de `username`, `password`, `busy`, `message`, `preferences` y de la respuesta.
- Estado local con `signal`. Se reemplaza el `any` de `error` por `unknown` con estrechamiento.

### Formularios y plantillas
- Validación de campos vacíos en el formulario antes de enviar.
- Estados de carga (`busy`) y de error visibles en la plantilla.

### Seguridad
- No se registra el token ni la respuesta completa en consola; el `console.error` se reemplaza por un mensaje sin datos sensibles.
- El nombre de usuario que aparece en el mensaje de error se muestra como texto, no como HTML concatenado.
- `preferences` se carga con validación del tipo esperado en lugar de `merge` sobre datos no confiables.

## 5. Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Exposición del token en consola o mensajes | Eliminar logs con datos sensibles y cubrirlo con una prueba que verifique que no se registra. |
| Cambio de clave de `localStorage` cierra sesiones activas | Mantener las claves exactas definidas en `auth.constants.ts` y probarlas. |
| Regresión en la redirección `/login` → `/dashboard` | Prueba de caracterización del flujo de éxito y de error. |
| Inyección HTML en el mensaje de error | Mostrar el texto como contenido escapado; no construir HTML con el nombre de usuario. |

## 6. Criterios de aceptación (medibles)
- Cero `any` nuevos en los archivos modificados (verificable con búsqueda de `any` en `web/src/app/login` y `web/src/app/auth`).
- `POST /auth/login` se invoca desde `AuthService`; ningún componente llama HTTP directamente.
- Cobertura del código modificado de 85% o más en `npm run test:coverage`.
- `npm run build` termina sin errores.
- Login exitoso guarda las tres claves de `localStorage` y navega a `/dashboard` (prueba verde).
- Un login fallido muestra mensaje de error sin imprimir el token en consola (prueba verde).

## 7. Plan de validación
### Pruebas unitarias
- Vitest: `AuthService` con respuesta válida, respuesta sin token y error de red.
- Vitest: `LoginComponent` con campos vacíos, éxito y fallo.

### Build y lint
- `npm run build` dentro de `web/`.
- Búsqueda de `any` nuevos en los archivos modificados.

### Pruebas funcionales
- Ejecutar `python tools/lab.py test web` desde la raíz.

### Seguridad (comprobaciones mínimas)
- Verificar que no hay secretos ni URLs internas nuevas en el código.
- Verificar que el mensaje de error no interpreta HTML del nombre de usuario.
- Ejecutar `npm run audit:workshop` sin nuevas vulnerabilidades moderadas sin revisar.

### Evidencia requerida
- Salida de `vitest run --coverage` con porcentaje del código modificado.
- Salida de `npm run build` con resultado.
- Lista de archivos modificados y resultado de la búsqueda de `any`.

## 8. Tareas sugeridas por rol
### Tech Lead
- Aprobar la separación en `AuthService` y los tipos propuestos.
- Confirmar el contrato de respuesta de `POST /auth/login`.
- Revisar el PR y verificar la evidencia de cobertura.

### Frontend
- Crear `auth.service.ts`, `auth.models.ts` y `auth.constants.ts`.
- Refactorizar `login.component.ts` para usar el servicio y eliminar `any`.
- Escribir las pruebas de Vitest del servicio y del componente.

### QA
- Verificar login exitoso, login fallido y campos vacíos en el navegador.
- Confirmar que la sesión persiste tras recargar `/dashboard`.

### Cyber
- Revisar el manejo del token y de los mensajes de error.
- Revisar el resultado de `npm run audit:workshop`.

## 9. Preguntas abiertas
- ¿`lodash/merge` debe conservarse para las preferencias o se reemplaza por una fusión tipada?
- ¿El contrato de `user` en la respuesta está documentado en `docs/ENDPOINTS.md`?
- ¿`login.component.html` muestra `message` como HTML? Hay que confirmarlo antes de cambiar la plantilla.
- ¿Se mantiene el timeout de 5000 ms o cambia con el servicio?
