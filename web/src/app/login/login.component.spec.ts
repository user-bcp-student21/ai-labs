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
<<<<<<< HEAD
  let sessionValues: Map<string, string>;
=======
>>>>>>> b8c0b65831f76b64bf68427dd22fc2d5c817f9b5
  let router: Router;
  let navigate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storedValues = new Map();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storedValues.get(key) ?? null,
      setItem: (key: string, value: string) => storedValues.set(key, value),
      removeItem: (key: string) => storedValues.delete(key)
    });
<<<<<<< HEAD
    sessionValues = new Map();
    vi.stubGlobal('sessionStorage', {
      getItem: (key: string) => sessionValues.get(key) ?? null,
      setItem: (key: string, value: string) => sessionValues.set(key, value),
      removeItem: (key: string) => sessionValues.delete(key)
    });
=======
>>>>>>> b8c0b65831f76b64bf68427dd22fc2d5c817f9b5
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
<<<<<<< HEAD
    expect(sessionValues.get('workshop_token')).toBe('fake-token');
    expect(storedValues.has('workshop_token')).toBe(false);
=======
    expect(storedValues.get('workshop_token')).toBe('fake-token');
>>>>>>> b8c0b65831f76b64bf68427dd22fc2d5c817f9b5
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
<<<<<<< HEAD
    expect(sessionValues.has('workshop_token')).toBe(false);
=======
    expect(storedValues.has('workshop_token')).toBe(false);
>>>>>>> b8c0b65831f76b64bf68427dd22fc2d5c817f9b5
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