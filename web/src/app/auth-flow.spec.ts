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
  let sessionValues: Map<string, string>;
  let navigate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    storedValues = new Map();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => storedValues.get(key) ?? null,
      setItem: (key: string, value: string) => storedValues.set(key, value),
      removeItem: (key: string) => storedValues.delete(key)
    });
    sessionValues = new Map();
    vi.stubGlobal('sessionStorage', {
      getItem: (key: string) => sessionValues.get(key) ?? null,
      setItem: (key: string, value: string) => sessionValues.set(key, value),
      removeItem: (key: string) => sessionValues.delete(key)
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

    expect(sessionValues.get('workshop_token')).toBe('fake-token');
    expect(storedValues.has('workshop_token')).toBe(false);
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