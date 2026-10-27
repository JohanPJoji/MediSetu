/**
 * auth.ts — token helpers
 * Thin re-export of the auth object from api.ts, plus a typed user cache.
 * Keep in sync with api.ts — do not duplicate the token key.
 */
export { auth } from './api';
export type { Role } from './api';

/** Decoded JWT user shape — matches GET /api/users/me response */
export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: import('./api').Role;
}
