'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Wrench } from 'lucide-react';

interface DemoAccount {
  email: string;
  label: string;
  color: string;
}

export interface DemoLoginConfig {
  email: string;
  password: string;
  accounts: DemoAccount[];
}

interface LoginFormProps {
  demoLogin: DemoLoginConfig | null;
}

export default function LoginForm({ demoLogin }: LoginFormProps) {
  const [email, setEmail] = useState(demoLogin?.email ?? '');
  const [password, setPassword] = useState(demoLogin?.password ?? '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      router.push('/copilot');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (accountEmail: string) => {
    if (!demoLogin) return;

    setEmail(accountEmail);
    setPassword(demoLogin.password);
    setError('');
    setLoading(true);
    try {
      await login(accountEmail, demoLogin.password);
      router.push('/copilot');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/20 mb-4">
            <Wrench size={32} className="text-primary-400" />
          </div>
          <h1 className="text-2xl font-bold">Industrial Maintenance Copilot</h1>
          <p className="text-sm text-muted mt-2">Industrial Equipment Smart Maintenance System</p>
        </div>
        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="block text-sm mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="w-full" placeholder="Enter your email" />
          </div>
          <div>
            <label className="block text-sm mb-1">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="w-full" placeholder="Enter your password" />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button type="submit" disabled={loading} className="btn btn-primary btn-block btn-lg">
            {loading ? 'Logging in...' : 'Sign In'}
          </button>
        </form>
        {demoLogin && (
          <div className="mt-6 space-y-2">
            <p className="text-xs text-muted text-center mb-2">Demo Quick Login</p>
            {demoLogin.accounts.map(({ email: accountEmail, label, color }) => (
              <button
                key={accountEmail}
                onClick={() => quickLogin(accountEmail)}
                disabled={loading}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm border ${color}`}
              >
                {label}: {accountEmail}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
