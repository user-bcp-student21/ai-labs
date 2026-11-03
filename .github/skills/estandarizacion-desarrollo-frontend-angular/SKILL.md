---
name: estandarizacion-desarrollo-frontend-angular
description: Estandarización de desarrollo frontend con Angular. Define lineamientos y estándares del framework (componentes, servicios, rutas, tipado, estado, formularios, seguridad, pruebas y calidad) para generar o revisar código del proyecto web de forma consistente y verificable.
---

# Skill: Estandarización de desarrollo frontend con Angular

## 1) Metadata
- **Skill ID:** estandarizacion-desarrollo-frontend-angular
- **Version:** 0.1.0
- **Purpose:** Estandarizar la forma de desarrollar, modificar y revisar la aplicación frontend en Angular, alineándose con las convenciones del framework y con las reglas del componente `web`.
- **Stack de referencia:** Angular 21 (`@angular/*` 21.2.19), TypeScript 5.9, RxJS 7.8, Vitest 3.2, Node >= 22.12.
- **Audience (roles):** Tech Lead, Frontend, QA, Cyber
- **When to use:** Al crear o modificar componentes, servicios, rutas, formularios o pruebas en `web/`, y al revisar un PR frontend.
- **When NOT to use:** Cambios de backend (`api/`, `auth/`), cambios de infraestructura sin impacto en el frontend, o ediciones triviales como typos.
- **Sensitive inputs:** No incluyas tokens, credenciales, secretos, URLs internas no autorizadas ni datos reales de clientes.
- **Expected output:** Código o revisión en Markdown que cumpla las secciones de Output.

## 2) Inputs
Proporciona la información en este formato:

- **Componente / archivo objetivo:** (por ejemplo `web/src/app/login/`)
- **Tarea:** (crear, modificar, refactorizar o revisar)
- **Restricciones conocidas:** (accesibilidad, rendimiento, compatibilidad de navegador)
- **Riesgos conocidos:** (seguridad, sesión, datos sensibles)
- **Contratos a conservar:** (endpoints como `/auth/login` y `/api/tasks`, claves de almacenamiento, rutas)
- **Team Definition of Done (DoD):** (si está disponible)

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary**
2. **Alcance del cambio**
    - Archivos afectados
    - Fuera del alcance
3. **Contratos preservados**
4. **Estándares aplicados**
    - Arquitectura y componentes
    - Servicios y HTTP
    - Tipado y estado
    - Formularios y plantillas
    - Seguridad
5. **Riesgos y mitigaciones**
6. **Criterios de aceptación (medibles)**
7. **Plan de validación**
    - Pruebas unitarias (Vitest)
    - Build y lint (`ng build`, revisión de tipos)
    - Seguridad (comprobaciones mínimas)
    - Evidencia requerida (qué adjuntar)
8. **Tareas sugeridas por rol**
    - Tech Lead
    - Frontend
    - QA
    - Cyber
9. **Preguntas abiertas**

## 4) Lineamientos y estándares Angular

### 4.1 Arquitectura y componentes
- Usa **componentes standalone** (sin `NgModule` nuevos); el proyecto no debe volver a declarar módulos para funcionalidades nuevas.
- Carga las pantallas de forma **perezosa** con `loadComponent`, como en `web/src/app/app.routes.ts`.
- Cada componente hace una sola cosa: si llama HTTP, maneja sesión y navega a la vez, separa la llamada HTTP a un servicio.
- Usa `changeDetection: ChangeDetectionStrategy.OnPush` en componentes nuevos.
- Usa la sintaxis de control de flujo nueva (`@if`, `@for` con `track`) en lugar de `*ngIf` / `*ngFor`.
- Usa `inject()` para dependencias en lugar de inyección por constructor cuando sea consistente con el archivo.

### 4.2 Nombres y estructura de archivos
- Archivos en `kebab-case` con sufijo de tipo: `nombre.component.ts`, `nombre.service.ts`, `nombre.routes.ts`.
- Un componente por carpeta, con su `.ts`, `.html` y `.css` juntos (como `web/src/app/login/`).
- Los nombres explican el propósito, no el tipo: evita `data`, `temp`, `result2` o `handleStuff`.
- Pruebas junto al código fuente con sufijo `.spec.ts` (como `legacy-format.spec.ts`).

### 4.3 Servicios y HTTP
- Toda llamada HTTP vive en un servicio; los componentes no construyen URLs.
- Centraliza las URLs de la API y las claves de `localStorage` en constantes en un único archivo; no las repitas en componentes.
- Devuelve tipos explícitos desde los servicios; maneja errores en un único punto.
- Conserva los endpoints existentes (`/auth/login`, `/api/tasks`) y su formato de petición y respuesta.

### 4.4 Tipado y estado
- TypeScript en modo estricto; **prohibido** `any` nuevo. Usa `unknown` y estrechamiento de tipos cuando el dato sea externo.
- Modela las respuestas de la API con `interface` o `type` en un archivo de modelos.
- Usa **signals** (`signal`, `computed`) para estado local de componentes nuevos; usa RxJS para flujos asíncronos y HTTP.
- Evita suscripciones manuales: prefiere `async` pipe, `toSignal` o `takeUntilDestroyed`.

### 4.5 Formularios y plantillas
- Usa **formularios reactivos** o formularios con tipos (`FormGroup` tipado) para formularios nuevos.
- Valida entradas en el formulario antes de enviarlas; no confíes solo en la validación del servidor.
- Usa `@if` para estados de carga y error visibles al usuario.
- Preferir plantillas sin lógica compleja: mueve cálculos a métodos o `computed`.

### 4.6 Código limpio y mantenibilidad
- Guard clauses (retorno anticipado) en lugar de anidar `if` dentro de `if`.
- Sin duplicación: un bloque repetido en dos componentes se extrae a un servicio o función reutilizable.
- Sin valores "mágicos": URLs, claves de almacenamiento, tiempos y límites se nombran como constantes.
- Comenta solo lo que requiera aclaración.

### 4.7 Seguridad
- No insertes HTML no confiable con `innerHTML` o `bypassSecurityTrust*`; deja que Angular sanitice por defecto.
- No guardes secretos reales en el código ni en `environment` versionado; usa variables de entorno en el despliegue.
- Trata el token de sesión como dato sensible: no lo imprimas en consola ni en mensajes de error.
- Restringe el acceso a rutas protegidas con guards y valida la sesión antes de mostrar datos.
- No silencies alertas de auditoría (`npm audit`) ni reglas del linter de seguridad.
- Revisa que `nginx.conf` y las cabeceras no se debiliten al cambiar la configuración.

### 4.8 Accesibilidad y experiencia
- Todo control interactivo tiene etiqueta accesible (`label`, `aria-*` cuando aplique) y es navegable por teclado.
- Muestra estados de carga, vacío y error de forma explícita.

## 5) Constraints
- No inventes requisitos: si falta información, inclúyela bajo **Preguntas abiertas**.
- No introduzcas dependencias nuevas sin justificar su necesidad y su revisión de auditoría.
- No cambies endpoints ni formatos que consuma el frontend sin aprobación explícita.
- No reduzcas quality gates ni cobertura para hacer pasar una prueba.
- Los criterios de aceptación deben ser verificables; no escribas "mejorar el rendimiento" sin una métrica.
- El plan de validación debe incluir al menos un elemento de evidencia concreto, como salida de `vitest`, salida de `ng build` o un checklist revisado.
- Meta de cobertura del código modificado: **85% o superior**.
- Mantén la salida en un máximo de 1-2 páginas.

## 6) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Tiene al menos 3 criterios de aceptación medibles (por ejemplo, cobertura >= 85%, build sin errores, cero `any` nuevos).
- Tiene al menos 3 tareas para Tech Lead, Frontend y QA, o explica por qué un rol no aplica.
- Incluye al menos 2 riesgos con mitigaciones.
- Indica los contratos preservados (endpoints y claves de almacenamiento).
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 7) Validation commands
Ejecuta desde la raíz del repositorio:
- `python tools/lab.py test web`: pruebas del frontend.
- `npm run build` dentro de `web/`: compilación de Angular.
- `npm run test:coverage` dentro de `web/`: cobertura del código modificado.

## 8) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL2.md` versionado.
- Salida de las pruebas y de `ng build` con resultado (aprobado o fallido).
- Reporte de cobertura del código modificado.
- Checklist de la sección 4 revisado para el cambio.
- Tag de versión para el Skill, como `skill-angular-frontend-v0.1.0`.
