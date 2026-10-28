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
  let sessionValues: Map<string, string>;
  let navigate: ReturnType<typeof vi.fn>;
  let component: DashboardComponent;

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
    sessionValues.set('workshop_token', 'fake-token');
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
    sessionValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(new Error('fake network error'));

    await component.ngOnInit();

    expect(component.error).toBe('fake network error');
    expect(component.loading).toBe(false);
  });

  it('shows an invalid-token response without clearing the session or redirecting', async () => {
    sessionValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(
      Object.assign(new Error('Request failed with status code 401'), {
        response: { status: 401, data: { detail: 'Invalid token' } }
      })
    );

    await component.ngOnInit();

    expect(component.error).toBe('Invalid token');
    expect(component.loading).toBe(false);
    expect(sessionValues.get('workshop_token')).toBe('fake-token');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('shows a task-request timeout rejection and clears the loading state', async () => {
    sessionValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue(new Error('timeout of 5000ms exceeded'));

    await component.ngOnInit();

    expect(component.error).toBe('timeout of 5000ms exceeded');
    expect(component.loading).toBe(false);
  });

  it('shows an error when the task response has no data', async () => {
    sessionValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockResolvedValue({} as never);

    await component.ngOnInit();

    expect(component.error).toBeTruthy();
    expect(component.loading).toBe(false);
  });

  it('clears token and user but preserves preferences on logout', async () => {
    sessionValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    storedValues.set('workshop_preferences', '{"theme":"dark"}');

    await component.logout();

    expect(sessionValues.has('workshop_token')).toBe(false);
    expect(storedValues.has('workshop_token')).toBe(false);
    expect(storedValues.has('workshop_user')).toBe(false);
    expect(storedValues.get('workshop_preferences')).toBe('{"theme":"dark"}');
    expect(navigate).toHaveBeenCalledWith(['/login']);
  });
});