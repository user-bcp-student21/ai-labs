# Tareas: Reducir la persistencia del token de autenticación en web

Referencias: [proposal.md](./proposal.md), [specs/web-session-token/spec.md](./specs/web-session-token/spec.md), [design.md](./design.md). Issue `user-bcp-student21/ai-labs#25`, hallazgo `H-WEB-01`.

Alcance: solo `web/`. Git y OpenSpec se ejecutan desde la raíz de `ai-labs`; las pruebas se ejecutan desde `web/` (o con `python tools/lab.py test web` desde la raíz). Día 1: solo ramas locales; sin push, sin tags, sin PR.

Decisiones tomadas por el diseño y tratadas como aprobadas:
- D1-A: `sessionStorage` centralizado en `session-token.ts`.
- D2: `session-token.ts` como único punto de acceso; no se crea `browser-state.service.ts`.

Excluido de este checklist por no estar aprobado: D3-b (limpieza de `localStorage` en login), D1-C (cookie `HttpOnly`), `H-WEB-02`, invalidación del token en servidor.

Dependencias: 0 → 1 → 2 → 3 → 4. Cada grupo debe quedar verde antes de pasar al siguiente.

## 0. Prerrequisitos: resolver conflictos de merge en los specs

Sin cambios de producción. Resolver con el lado `HEAD`, coherente con el código actual.

- [x] 0.1 Resolver los marcadores en [auth-flow.spec.ts](../../../web/src/app/auth-flow.spec.ts) conservando el lado `HEAD` (`sessionStorage`).
  - Verificación: sin líneas `<<<<<<<`, `=======` ni `>>>>>>>` en el archivo.
- [x] 0.2 Resolver los marcadores en [login.component.spec.ts](../../../web/src/app/login/login.component.spec.ts) con el mismo criterio.
  - Verificación: igual que 0.1.
- [x] 0.3 Resolver los marcadores en [dashboard.component.spec.ts](../../../web/src/app/dashboard/dashboard.component.spec.ts) con el mismo criterio.
  - Verificación: igual que 0.1.
- [x] 0.4 Confirmar que no quedan marcadores en `web/src`.
  - Verificación: búsqueda de `^(<<<<<<<|=======|>>>>>>>)` en `web/src` sin resultados.
- [x] 0.5 Revisión humana de la resolución de los tres archivos.
  - Criterio: aprobación explícita antes de continuar. No se asume aprobación.
  - Aprobación: indicada por el usuario en esta sesión (2026-10-29, "aprobado, corrígelo todo"). La resolución se commitió localmente en `main` (`116c836`).

## 1. Caracterización: pruebas antes de cualquier cambio funcional

Solo se modifican archivos de prueba. Los casos siguen [design.md](./design.md), sección 8.

- [x] 1.1 Ejecutar `npm test` desde `web/` con los specs resueltos y registrar el resultado real.
  - Criterio de salida: todas las pruebas existentes en verde. Si alguna falla, detenerse y analizar: el comportamiento real difiere de la spec.
- [x] 1.2 C1 (login exitoso): en `login.component.spec.ts` o `auth-flow.spec.ts`, comprobar que el token queda en `sessionStorage` y que ninguna clave de `localStorage` contiene su valor.
  - Verificación: la prueba pasa con código sin cambios.
- [x] 1.3 C2 (login sin token): comprobar el mensaje exacto "El backend respondió sin token.", que no hay navegación y que no se guarda token.
  - Verificación: la prueba pasa.
- [x] 1.4 C3 (dashboard sin token): comprobar que no hay `axios.get` y que se navega a `/login`.
  - Verificación: la prueba pasa.
- [x] 1.5 C4 (consulta con token): comprobar URL con `owner`, header Bearer y que el token no se lee desde `localStorage` (espía sobre `getItem` con la clave del token).
  - Verificación: la prueba pasa.
- [x] 1.6 C5 (401 sin limpieza): comprobar que se muestra `error`, que el token se conserva y que no hay navegación.
  - Verificación: la prueba pasa.
- [x] 1.7 C6 (logout con token heredado): sembrar `workshop_token` en `localStorage` y en `sessionStorage`; tras logout, ambos sin token, `workshop_preferences` conservado y navegación a `/login`.
  - Verificación: la prueba pasa.
- [x] 1.8 C7 (logout y reingreso): tras logout, `ngOnInit` del dashboard no llama a `axios.get` y navega a `/login`.
  - Verificación: la prueba pasa; añadir en `auth-flow.spec.ts`.
- [x] 1.9 C8 (filtrado y orden): `ARCHIVED` excluido y orden por `priority`.
  - Verificación: la prueba pasa.
- [x] 1.10 Ejecutar `npm test` desde `web/` y comprobar con `git diff --stat -- web/src` que solo cambian archivos `*.spec.ts`.
  - Criterio de salida: verde y sin cambios de producción. Registrar el resultado real.

## 2. Implementación incremental

Solo si la caracterización lo requiere o si queda un acceso directo al token fuera de `session-token.ts`.

- [x] 2.1 Buscar accesos directos al token fuera del módulo de sesión: `workshop_token` y `sessionStorage`/`localStorage` en `web/src`.
  - Verificación: el resultado documenta cada acceso encontrado. Si no hay accesos fuera de `session-token.ts`, esta fase termina sin cambios.
- [ ] 2.2 Si 2.1 encuentra accesos directos, escribir primero una prueba en rojo que lo demuestre.
  - Verificación: la prueba falla antes del cambio.
- [ ] 2.3 Migrar cada acceso encontrado a `session-token.ts` con el cambio mínimo.
  - Verificación: la prueba de 2.2 pasa; el resto de pruebas se mantienen verdes.
- [ ] 2.4 Si F1 o F2 revelan un defecto real frente a la spec, corregirlo en `session-token.ts` con prueba roja previa.
  - Verificación: la prueba de caracterización correspondiente pasa sin romper otras.
  - Alcance: no tocar login ni dashboard salvo necesidad demostrada por una prueba.
- [x] 2.5 Revisar que no se añadió código de limpieza de `localStorage` en login, ni servicios nuevos, ni dependencias.
  - Verificación: `git diff -- web/package.json` vacío; sin archivos nuevos en `web/src` fuera de specs.

## 3. Validación

- [x] 3.1 Ejecutar `npm test` desde `web/`.
  - Criterio: verde. Registrar el resultado real.
- [x] 3.2 Ejecutar `npm run test:coverage` desde `web/`.
  - Criterio: cobertura de `session-token.ts`, `login.component.ts` y `dashboard.component.ts` de 85 % o más (meta de AGENTS para código modificado). Si el archivo no cambió, se mide igual y se registra la cifra real.
- [x] 3.3 Ejecutar `npm run build` desde `web/`.
  - Criterio: build sin errores.
- [x] 3.4 Ejecutar `python tools/lab.py test web` desde la raíz.
  - Criterio: mismo resultado que los pasos anteriores. Registrar la salida real.
- [x] 3.5 Registrar evidencia en el documento general de evidencias de la raíz, con componente `web` y `H-WEB-01`, conservando las secciones existentes.
  - Verificación: incluir comando exacto y resultado real (pasó o falló). No afirmar resultados no ejecutados.
- [ ] 3.6 Revisión humana de los resultados y del riesgo residual de `sessionStorage` (R1 de [design.md](./design.md)).
  - Criterio: aprobación explícita antes de integrar.

## 4. Documentación posterior

Solo después de validar y de la revisión humana (3.6).

- [ ] 4.1 Corregir en [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md) las menciones de `localStorage` para el token (líneas 44, 77, 95 y 152) con la evidencia real de `session-token.ts`.
  - Verificación: no quedan menciones de `localStorage` para `workshop_token`; `workshop_user` y `workshop_preferences` no se modifican.
- [ ] 4.2 Actualizar la evidencia de `H-WEB-01` en `HALLAZGOS.md` y `HU-01.md` con las referencias reales, sin cambiar el estado.
  - Verificación: `H-WEB-01` sigue en `Pendiente`.
- [ ] 4.3 No marcar `H-WEB-01` como resuelto. El riesgo residual de `sessionStorage` permanece registrado.
  - Verificación: revisión de la tabla de `HALLAZGOS.md`.

## Fuera de este checklist

- D3-b: limpieza de `localStorage` en login. Requiere aprobación nueva.
- D1-C: cookie `HttpOnly` emitida por el backend. Requiere propuesta propia y cambios en `auth/` y `api/`.
- `H-WEB-02`, `H-WEB-03`, `H-WEB-04`, `H-WEB-05`: cambios separados.
- Invalidación del token en servidor al cerrar sesión.
