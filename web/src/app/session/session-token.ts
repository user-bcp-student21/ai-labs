const TOKEN_KEY = 'workshop_token';

export function saveSessionToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function readSessionToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

// Also removes the token left by earlier versions in localStorage.
export function clearSessionToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
}
