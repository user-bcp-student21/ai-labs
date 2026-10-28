# Pruebas de web

## Alcance

Las pruebas caracterizan el flujo que `docs/ENDPOINTS.md` describe para la implementacion actualmente presente en `web/`: login, almacenamiento local de sesion, consulta de tareas y errores que la UI presenta. Axios, el almacenamiento del navegador, Router, NgZone y ChangeDetectorRef se simulan; no se llama a servicios reales ni se certifica su contrato HTTP.

IDs relacionados: `H-WEB-01` (sesion/token caracterizados, no corregidos), `H-WEB-02` (mensaje/error caracterizado, no corregido) y `H-WEB-06` (ampliacion de pruebas). Ejecutar estas pruebas no marca ningun hallazgo como Resuelto.

## Matriz de casos

| flujo | caso | tipo | resultado esperado |
|---|---|---|---|
| Login → tareas | Login con token y usuario; el dashboard consulta tareas con el token guardado. (`web/src/app/auth-flow.spec.ts`) | Camino feliz | POST al login; token y usuario en almacenamiento; navegacion a dashboard; GET de tareas con `owner` y header Bearer; tarea visible y carga terminada. |
| Login | Credenciales no vacias y respuesta con token. (`web/src/app/login/login.component.spec.ts`) | Camino feliz | Envía body y timeout observados, persiste token/usuario/preferencias y navega a dashboard. |
| Tareas | Respuesta con tareas, una archivada. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Camino feliz / borde | Excluye `ARCHIVED`, calcula etiqueta y termina la carga. |
| Login | Usuario vacio. (`web/src/app/login/login.component.spec.ts`) | Borde | Mensaje de usuario requerido; no llama al endpoint. |
| Login | Contrasena vacia. (`web/src/app/login/login.component.spec.ts`) | Borde | Mensaje de contrasena requerida; no llama al endpoint. |
| Login | Respuesta aceptada sin token. (`web/src/app/login/login.component.spec.ts`) | Borde | Muestra el mensaje de respuesta sin token; no navega. |
| Login | Servicio no disponible, rechazo de red simulado. (`web/src/app/login/login.component.spec.ts`) | Error | Muestra nombre de usuario y `Network Error`; no persiste sesion ni navega. |
| Login | Rechazo de timeout de 5000 ms simulado. (`web/src/app/login/login.component.spec.ts`) | Error | Muestra el mensaje de timeout, limpia `busy` y no navega. |
| Tareas | No hay token. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Borde | No consulta tareas y navega a login. |
| Tareas | Token invalido; rechazo 401 simulado con `data.detail`. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Error | Muestra `detail`, termina carga y, segun comportamiento actual, conserva token y no redirige. |
| Tareas | Servicio no disponible, error de red simulado. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Error | Muestra el mensaje de transporte y termina carga. |
| Tareas | Rechazo de timeout simulado. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Error | Muestra el mensaje de timeout y termina carga. La llamada actual no configura timeout propio. |
| Tareas | Respuesta sin `data`. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Respuesta inesperada | Muestra el error producido al procesar la respuesta y termina carga. |
| Sesion | Cerrar sesion. (`web/src/app/dashboard/dashboard.component.spec.ts`) | Camino de salida | Elimina token/usuario, conserva preferencias y navega a login. |

## Codigo de los tests

Los siguientes bloques corresponden a los archivos ejecutados.

### `web/src/app/auth-flow.spec.ts`

```typescript
import type { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardComponent } from './dashboard/dashboard.component';
import { LoginComponent } from './login/login.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

describe('login-to-tasks flow', () => {
  let storedValues: Map<string, string>;
  let navigate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storedValues = new Map();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storedValues.get(key) ?? null,
      setItem: (key: string, value: string) => storedValues.set(key, value),
      removeItem: (key: string) => storedValues.delete(key)
    });
    navigate = vi.fn().mockResolvedValue(true);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('logs in, stores the token, and loads tasks with that bearer token', async () => {
    const router = { navigate } as unknown as Router;
    const login = new LoginComponent(router);
    login.username = 'student';
    login.password = 'fake-password';
    vi.mocked(axios.post).mockResolvedValue({
      data: {
        token: 'fake-token',
        user: { username: 'student', displayName: 'Student' }
      }
    } as never);
    const tasks = [
      { id: 1, owner: 'student', priority: 'HIGH', status: 'TODO', title: 'Task', description: 'Fake task' }
    ];
    vi.mocked(axios.get).mockResolvedValue({ data: tasks } as never);

    await login.login();

    expect(storedValues.get('workshop_token')).toBe('fake-token');
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);

    const changeDetector = { detectChanges: vi.fn() } as unknown as ChangeDetectorRef;
    const zone = { run: (callback: () => void) => callback() } as unknown as NgZone;
    const dashboard = new DashboardComponent(router, changeDetector, zone);
    await dashboard.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith('http://localhost:8000/api/tasks?owner=student', {
      headers: { Authorization: 'Bearer fake-token' }
    });
    expect(dashboard.visibleTasks).toHaveLength(1);
    expect(dashboard.visibleTasks[0].title).toBe('Task');
    expect(dashboard.loading).toBe(false);
  });
});
```

### `web/src/app/login/login.component.spec.ts`

```typescript
import type { Router } from '@angular/router';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LoginComponent } from './login.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

describe('LoginComponent characterization', () => {
  let storedValues: Map<string, string>;
  let router: Router;
  let navigate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storedValues = new Map();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storedValues.get(key) ?? null,
      setItem: (key: string, value: string) => storedValues.set(key, value),
      removeItem: (key: string) => storedValues.delete(key)
    });
    navigate = vi.fn().mockResolvedValue(true);
    router = { navigate } as unknown as Router;
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('rejects a missing username without calling the endpoint', async () => {
    const component = new LoginComponent(router);
    await component.login();
    expect(component.message).toBe('<strong>Ingrese un usuario.</strong>');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('rejects a missing password without calling the endpoint', async () => {
    const component = new LoginComponent(router);
    component.username = 'student';
    await component.login();
    expect(component.message).toBe('<strong>Ingrese una contraseña.</strong>');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('stores the login response and preferences before navigating to dashboard', async () => {
    const component = new LoginComponent(router);
    component.username = 'student';
    component.password = 'fake-password';
    component.preferences = { theme: 'dark', showTips: true, compact: false };
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'fake-token', user: { username: 'student' } }
    } as never);

    await component.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'fake-password', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storedValues.get('workshop_token')).toBe('fake-token');
    expect(storedValues.get('workshop_user')).toBe('{"username":"student"}');
    expect(storedValues.get('workshop_preferences')).toBe(JSON.stringify(component.preferences));
    expect(navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.busy).toBe(false);
  });

  it('shows the missing-token response without navigating', async () => {
    const component = new LoginComponent(router);
    component.username = 'student';
    component.password = 'fake-password';
    vi.mocked(axios.post).mockResolvedValue({ data: {} } as never);
    await component.login();
    expect(component.message).toBe('<strong>El backend respondió sin token.</strong>');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('includes the username and backend message in a failed login message', async () => {
    const component = new LoginComponent(router);
    component.username = 'student <em>local</em>';
    component.password = 'fake-password';
    vi.mocked(axios.post).mockRejectedValue(
      Object.assign(new Error('request failed'), {
        response: { data: { message: 'fake authentication error' } }
      })
    );
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    await component.login();

    expect(component.message).toBe(
      '<strong>No se pudo autenticar a student <em>local</em>.</strong><br>fake authentication error'
    );
    expect(navigate).not.toHaveBeenCalled();
    expect(component.busy).toBe(false);
  });

  it('shows a service-unavailable error without creating a session', async () => {
    const component = new LoginComponent(router);
    component.username = 'student';
    component.password = 'fake-password';
    vi.mocked(axios.post).mockRejectedValue(new Error('Network Error'));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    await component.login();
    expect(component.message).toContain('No se pudo autenticar a student.');
    expect(component.message).toContain('Network Error');
    expect(storedValues.has('workshop_token')).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows a timeout error and clears the busy state', async () => {
    const component = new LoginComponent(router);
    component.username = 'student';
    component.password = 'fake-password';
    vi.mocked(axios.post).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    await component.login();
    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'fake-password', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(component.message).toContain('timeout of 5000ms exceeded');
    expect(component.busy).toBe(false);
    expect(navigate).not.toHaveBeenCalled();
  });
});
```

### `web/src/app/dashboard/dashboard.component.spec.ts`

```typescript
import type { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardComponent } from './dashboard.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

describe('DashboardComponent characterization', () => {
  let storedValues: Map<string, string>;
  let navigate: ReturnType<typeof vi.fn>;
  let component: DashboardComponent;

  beforeEach(() => {
    storedValues = new Map();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storedValues.get(key) ?? null,
      setItem: (key: string, value: string) => storedValues.set(key, value),
      removeItem: (key: string) => storedValues.delete(key)
    });
    navigate = vi.fn().mockResolvedValue(true);
    const router = { navigate } as unknown as Router;
    const changeDetector = { detectChanges: vi.fn() } as unknown as ChangeDetectorRef;
    const zone = { run: (callback: () => void) => callback() } as unknown as NgZone;
    component = new DashboardComponent(router, changeDetector, zone);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('redirects to login when no token is stored', async () => {
    storedValues.set('workshop_user', '{"username":"student"}');
    await component.ngOnInit();
    expect(navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('loads tasks using the stored username and bearer token', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    const tasks = [
      { id: 1, owner: 'student', priority: 'HIGH', status: 'TODO', title: 'Task', description: 'Fake task' },
      { id: 2, owner: 'student', priority: 'LOW', status: 'ARCHIVED', title: 'Old task', description: 'Archived' }
    ];
    vi.mocked(axios.get).mockResolvedValue({ data: tasks } as never);
    await component.ngOnInit();
    expect(axios.get).toHaveBeenCalledWith('http://localhost:8000/api/tasks?owner=student', {
      headers: { Authorization: 'Bearer fake-token' }
    });
    expect(component.tasks).toEqual(tasks);
    expect(component.visibleTasks).toHaveLength(1);
    expect(component.visibleTasks[0].label).toBe('HIGH · STUDENT');
    expect(component.loading).toBe(false);
    expect(component.statusLabel('TODO')).toBe('Por hacer');
    expect(component.statusLabel('unknown')).toBe('unknown');
  });

  it('exposes a request error and clears the loading state', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(new Error('fake network error'));
    await component.ngOnInit();
    expect(component.error).toBe('fake network error');
    expect(component.loading).toBe(false);
  });

  it('shows an invalid-token response without clearing the session or redirecting', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(
      Object.assign(new Error('Request failed with status code 401'), {
        response: { status: 401, data: { detail: 'Invalid token' } }
      })
    );
    await component.ngOnInit();
    expect(component.error).toBe('Invalid token');
    expect(component.loading).toBe(false);
    expect(storedValues.get('workshop_token')).toBe('fake-token');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows a task-request timeout rejection and clears the loading state', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
    await component.ngOnInit();
    expect(component.error).toBe('timeout of 5000ms exceeded');
    expect(component.loading).toBe(false);
  });

  it('shows an error when the task response has no data', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockResolvedValue({} as never);
    await component.ngOnInit();
    expect(component.error).toBeTruthy();
    expect(component.loading).toBe(false);
  });

  it('clears token and user but preserves preferences on logout', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    storedValues.set('workshop_preferences', '{"theme":"dark"}');
    await component.logout();
    expect(storedValues.has('workshop_token')).toBe(false);
    expect(storedValues.has('workshop_user')).toBe(false);
    expect(storedValues.get('workshop_preferences')).toBe('{"theme":"dark"}');
    expect(navigate).toHaveBeenCalledWith(['/login']);
  });
});
```

## Ejecuciones

Todos los comandos se ejecutaron con cwd `web/`. Los tests usan datos ficticios y mocks; no se llamaron servicios HTTP reales.

| componente / IDs | comando | cwd | codigo de salida | resultado |
|---|---|---|---:|---|
| web / `H-WEB-01`, `H-WEB-02`, `H-WEB-06` | `npm test` (linea base, antes de configurar el compilador) | `web/` | 1 | 1 test pasó; 2 suites no cargaron por falta de `@angular/compiler` para JIT de `PlatformLocation`. |
| web / mismos IDs | `npm test` (despues de agregar `src/test-setup.ts`) | `web/` | 0 | 3 archivos, 10 tests pasaron. |
| web / mismos IDs | `npm test` (con casos de servicio/timeout/token) | `web/` | 0 | 3 archivos, 15 tests pasaron. |
| web / mismos IDs | `npm test` (con flujo integrado login → tareas) | `web/` | 0 | 4 archivos, 16 tests pasaron. |
| web / mismos IDs | `npm run test:coverage` | `web/` | 0 | 4 archivos, 16 tests pasaron; reporte V8 generado en `web/coverage/`. |

### Cobertura

Metodo: `@vitest/coverage-v8` (V8), metrica de lineas instrumentadas; el reporte tambien informa ramas, funciones y statements. Fuente: `web/coverage/coverage-summary.json` y `web/coverage/index.html`.

| alcance medido | lineas cubiertas / total | porcentaje de lineas |
|---|---:|---:|
| `web/src/app/login/login.component.ts` | 58 / 60 | 96.66% |
| `web/src/app/dashboard/dashboard.component.ts` | 68 / 68 | 100% |
| Modulos de implementacion del flujo (login + dashboard) | 126 / 128 | 98.44% |
| Global de `web/src` | 132 / 164 | 80.48% |

La cobertura enfocada de los dos modulos que implementan login y tareas supera 85%. La global se informa aparte y queda en 80.48%; incluye `main.ts`, `AppComponent`, rutas y `legacy-format.ts`, fuera de este flujo probado. Los archivos de spec, la configuracion y `src/test-setup.ts` no forman parte de los 128 statements instrumentados de esos modulos; no se afirma cobertura de los propios tests. La cobertura de ramas del flujo es inferior a la cobertura de lineas: dashboard 15/19 (78.94%) y login 13/15 (86.66%).

## Fallos, pendientes y pruebas propuestas

- **Fallo de linea base corregido en infraestructura de pruebas:** Vitest no cargaba el compilador Angular. `web/vitest.config.ts` ahora carga `web/src/test-setup.ts`, que importa `@angular/compiler`, ya presente en dependencias; no se agregaron paquetes.
- **Pendiente de contrato real:** todos los resultados HTTP son simulados. No se verificaron status ni payloads contra los servicios.
- **Timeout de tareas:** el test inyecta un rechazo que representa timeout y comprueba la UI; no demuestra un timeout real, porque el cliente no configura uno para `GET /api/tasks`.
- **Renderizado DOM y seguridad:** las pruebas corren en entorno `node`; no verifican el DOM ni el sanitizador de Angular. `H-WEB-02` (`[innerHTML]`) y `H-WEB-01` (`localStorage`) siguen sin corregirse; esta tarea solo amplía caracterizacion y no cambia sus estados.
- **Pruebas propuestas, no ejecutadas:** una prueba de navegador contra servicios locales con contratos acordados; prueba de DOM que verifique el texto de error como texto y no markup, cuando se elija y justifique un entorno de navegador/DOM.