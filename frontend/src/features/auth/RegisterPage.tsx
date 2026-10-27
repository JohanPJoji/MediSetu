import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api, auth } from '../../lib/api';
import { useAuth } from '../../app/AuthContext';
import { Button } from '../../components/primitives/Button';
import { Input } from '../../components/primitives/Input';
import styles from './Auth.module.css';

export function RegisterPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.register(email, password, fullName);
      const r = await api.login(email, password);
      auth.setToken(r.data.access_token);
      const me = await api.me();
      setUser(me.data);
      // After registration, go to onboarding to create patient profile
      navigate('/onboarding', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.logoMark} aria-hidden="true">M</div>
          <h1 className={styles.title}>MediSetu</h1>
          <p className={styles.subtitle}>Create a patient account</p>
        </div>

        <form onSubmit={submit} className={styles.form} noValidate>
          <Input
            id="full-name"
            label="Full name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            autoComplete="name"
            required
            placeholder="As it appears on your ID"
          />
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
            autoComplete="new-password"
            required
            placeholder="At least 8 characters"
            hint="Choose a strong password you'll remember."
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
            Create account
          </Button>
        </form>

        <p className={styles.registerLink}>
          Already have an account?{' '}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </main>
  );
}
