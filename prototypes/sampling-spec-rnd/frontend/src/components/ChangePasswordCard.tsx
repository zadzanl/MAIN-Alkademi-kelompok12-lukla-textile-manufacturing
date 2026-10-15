/**
 * ChangePasswordCard — change the signed-in user's password.
 *
 * The backend revokes all sessions after a password change, so on success we
 * clear the local session and hand control back to the auth gate.
 */

import React, { useState } from 'react';
import * as authApi from '../services/authApi';
import { clearSession, getToken } from '../services/authSession';
import { passwordsMatch, validatePassword } from '../services/authRules';
import { toast } from '../services/toast';

interface ChangePasswordCardProps {
  onLoggedOut: () => void;
}

const ChangePasswordCard: React.FC<ChangePasswordCardProps> = ({ onLoggedOut }) => {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    const pwError = validatePassword(next);
    if (pwError) { setError(pwError); return; }
    if (!passwordsMatch(next, confirm)) { setError('Konfirmasi password tidak cocok.'); return; }

    setBusy(true);
    setError(null);
    const res = await authApi.changePassword(token, current, next);
    setBusy(false);
    if (res.success) {
      toast.success('Password diubah. Silakan masuk kembali.');
      clearSession();
      onLoggedOut();
    } else {
      setError(res.error ?? 'Gagal mengubah password.');
    }
  };

  return (
    <div className="border rounded-[18px] p-6" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
      <h3 className="text-[15px] font-semibold mb-1" style={{ color: 'var(--c-ink)' }}>Keamanan</h3>
      <p className="text-[13px] mb-5" style={{ color: 'var(--c-ink-muted)' }}>
        Ganti password akun portal Anda.
      </p>
      <form onSubmit={submit} className="space-y-4 max-w-md" noValidate>
        <div>
          <label htmlFor="cp-current" className="block text-[13px] font-medium mb-2" style={{ color: 'var(--c-ink)' }}>
            Password saat ini
          </label>
          <input id="cp-current" className="field" type="password" autoComplete="current-password"
            value={current} onChange={(e) => setCurrent(e.target.value)} />
        </div>
        <div>
          <label htmlFor="cp-new" className="block text-[13px] font-medium mb-2" style={{ color: 'var(--c-ink)' }}>
            Password baru
          </label>
          <input id="cp-new" className="field" type="password" autoComplete="new-password"
            value={next} onChange={(e) => setNext(e.target.value)} />
        </div>
        <div>
          <label htmlFor="cp-confirm" className="block text-[13px] font-medium mb-2" style={{ color: 'var(--c-ink)' }}>
            Konfirmasi password baru
          </label>
          <input id="cp-confirm" className="field" type="password" autoComplete="new-password"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </div>
        {error && (
          <p role="alert" className="rounded-[11px] px-4 py-3 text-[13px]"
            style={{ background: 'var(--c-bad-bg)', color: 'var(--c-bad-4)' }}>
            {error}
          </p>
        )}
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy ? 'Menyimpan…' : 'Simpan password baru'}
        </button>
      </form>
    </div>
  );
};

export default ChangePasswordCard;
