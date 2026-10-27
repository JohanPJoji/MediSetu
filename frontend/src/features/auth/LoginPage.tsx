import { useState, type FormEvent } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { api, auth } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { Input } from '../../components/primitives/Input';
import styles from './Auth.module.css';

const ROLE_SEEDS = [
  { label: 'Patient',  email: 'patient@medisetu.dev',  password: 'Patient@12345' },
  { label: 'Doctor',   email: 'doctor@medisetu.dev',   password: 'Doctor@12345' },
  { label: 'Nurse',    email: 'nurse@medisetu.dev',    password: 'Nurse@12345' },
  { label: 'Pharmacy', email: 'pharmacy@medisetu.dev', password: 'Pharmacy@12345' },
  { label: 'Admin',    email: 'admin@medisetu.dev',    password: 'Admin@123456' },
];

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();

  const from = (location.state as { from?: Location })?.from?.pathname ?? '/dashboard';

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const r = await api.login(email, password);
      auth.setToken(r.data.access_token);
      const me = await api.me();
      setUser(me.data);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed. Check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillSeed = (seed: typeof ROLE_SEEDS[number]) => {
    setEmail(seed.email);
    setPassword(seed.password);
    setError('');
  };

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.logoMark} aria-hidden="true">M</div>
          <h1 className={styles.title}>MediSetu</h1>
          <p className={styles.subtitle}>Sign in to your account</p>
        </div>

        <form onSubmit={submit} className={styles.form} noValidate>
          <Input
            id="email"
            label="Email address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
            placeholder="you@example.com"
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            placeholder="••••••••"
          />

          {error && (
            <div className={styles.errorBox} role="alert">
              {error}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={loading}
            className={styles.submitBtn}
          >
            Sign in
          </Button>
        </form>

        <p className={styles.registerLink}>
          New patient?{' '}
          <Link to="/register">Create a patient account</Link>
        </p>

        {/* Quick-fill for development/demo */}
        <details className={styles.devSeeds}>
          <summary>Demo accounts</summary>
          <div className={styles.seedList}>
            {ROLE_SEEDS.map((s) => (
              <button
                key={s.label}
                type="button"
                className={styles.seedBtn}
                onClick={() => fillSeed(s)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </details>
      </div>
    </main>
  );
}
