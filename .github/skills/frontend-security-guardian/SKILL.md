---
name: frontend-security-guardian
description: Analiza código frontend para identificar vulnerabilidades XSS, exposición de tokens, almacenamiento inseguro, URLs manipulables y configuraciones CSP, generando un reporte trazable con severidad, evidencia y mitigaciones.
---

# Skill: Frontend Security Guardian

## 1) Metadata
- **Skill ID:** frontend-security-guardian
- **Version:** 0.1.0
- **Purpose:** Identificar riesgos de seguridad en el código frontend (XSS, exposición de tokens, almacenamiento inseguro, URLs manipulables y configuración CSP) y producir un reporte trazable con evidencia y mitigaciones.
- **Audience (roles):** Frontend, Cyber, Tech Lead, QA
- **When to use:** Antes de abrir un PR que toque autenticación, sesión, renderizado de contenido, rutas, llamadas HTTP o cabeceras de seguridad del frontend; también en revisiones periódicas de seguridad.
- **When NOT to use:** Análisis de backend o infraestructura sin componente frontend, incidentes P1 de producción (usar el proceso de respuesta a incidentes) o cambios puramente cosméticos sin impacto en datos ni en el DOM.
- **Sensitive inputs:** No incluyas tokens reales, contraseñas, claves de API, URLs internas no autorizadas ni datos de clientes en el reporte. Redacta cualquier valor sensible encontrado (por ejemplo, `token=<REDACTADO>`).
- **Expected output:** Markdown estructurado mediante la sección Output a continuación.

## 2) Inputs
Proporciona la información en este formato:

- **Alcance del análisis (componentes, rutas o carpetas):**
- **Stack y versiones (framework, router, cliente HTTP):**
- **Mecanismo de autenticación (cookie, token en memoria, token en almacenamiento del navegador):**
- **Fuentes de contenido no confiable (entrada de usuario, respuestas de API, parámetros de URL):**
- **Políticas de seguridad vigentes (CSP, CORS, cabeceras, estándares internos):**
- **Archivos o fragmentos de código a revisar:**
- **Known risks / hallazgos previos (si existen):**

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary** (alcance revisado, número de hallazgos por severidad y veredicto general)
2. **Scope**
    - Dentro del alcance
    - Fuera del alcance
3. **Supuestos**
4. **Hallazgos por categoría**
    - XSS (inyección de HTML, uso de `innerHTML`, `bypassSecurityTrust*`, `eval`, plantillas dinámicas)
    - Exposición de tokens (tokens en URLs, logs, consola, mensajes de error o variables globales)
    - Almacenamiento inseguro (`localStorage` / `sessionStorage` para credenciales o datos sensibles, cookies sin atributos de seguridad)
    - URLs manipulables (redirecciones abiertas, `returnUrl` sin validar, parámetros de ruta usados sin sanitizar, enlaces `target="_blank"` sin `rel="noopener"`)
    - Configuración CSP (directivas ausentes o permisivas como `unsafe-inline` y `unsafe-eval`, orígenes comodín, falta de `frame-ancestors`, `object-src`, `base-uri`)
    - Cada hallazgo debe incluir: ID, severidad, archivo y línea, evidencia redactada, impacto y mitigación
5. **Riesgos y mitigaciones**
6. **Criterios de aceptación (medibles)**
7. **Plan de validación**
    - Revisión estática (búsqueda de patrones inseguros y reglas de linter)
    - Pruebas unitarias y de componentes para sanitización y guardas de ruta
    - Pruebas funcionales (flujos de login, logout, expiración de sesión y redirecciones)
    - Verificación de cabeceras CSP en la respuesta HTTP real
    - Evidencia requerida (qué adjuntar)
8. **Tareas sugeridas por rol**
    - Frontend
    - Cyber
    - Tech Lead
    - QA
9. **Preguntas abiertas**

## 4) Constraints
- Analiza solo el código y la configuración proporcionados; no inventes hallazgos ni asumas archivos que no hayas visto.
- Marca cada hallazgo como **confirmado** (evidencia directa en el código) o **sospechoso** (requiere validación adicional).
- No incluyas secretos, tokens ni datos sensibles en el reporte; redáctalos siempre.
- No propongas herramientas fuera del stack permitido ni dependencias nuevas sin justificarlas.
- No silencies alertas: no sugieras desactivar reglas de linter, escáneres o CSP para "resolver" un hallazgo.
- Los criterios de aceptación deben ser verificables; no escribas "mejorar la seguridad" sin una condición medible.
- Las severidades deben usar la escala Crítica, Alta, Media o Baja, con justificación breve.
- Mantén la salida en un máximo de 2 páginas para que siga siendo usable.

## 5) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Cubre las cinco categorías: XSS, exposición de tokens, almacenamiento inseguro, URLs manipulables y CSP (o indica explícitamente por qué una categoría no aplica).
- Cada hallazgo tiene severidad, ubicación (archivo y línea), evidencia redactada y mitigación.
- Tiene al menos 3 criterios de aceptación medibles.
- Tiene al menos 2 riesgos con mitigaciones.
- Tiene al menos 3 tareas para cada rol central: Frontend, Cyber y QA, o explica por qué un rol no aplica.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL.md` versionado en `.github/skills/frontend-security-guardian/`.
- Listado de archivos revisados y patrones buscados.
- Reporte de hallazgos con severidad, ubicación y estado (confirmado o sospechoso).
- Salida de las pruebas de sanitización, guardas de ruta y validación de URLs cuando existan.
- Captura o salida de las cabeceras CSP obtenidas de la respuesta HTTP.
- Tag de versión para el Skill, como `skill-frontend-security-guardian-v0.1.0`.
