/**
 * PortalSettingsView — external client account settings: identity summary,
 * password change, and sign-out. Mirrors the internal portal's change-password
 * flow but for the external client actor.
 */

import React, { useState } from 'react';
import { getActor, getToken, clearSession } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import { passwordsMatch, validatePassword } from '../services/authRules';
import PortalBadge from '../components/PortalBadge';

interface PortalSettingsViewProps {
  onLoggedOut: () => void;
}

const PortalSettingsView: React.FC<PortalSettingsViewProps> = ({ onLoggedOut }) => {
  const actor = getActor();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const token = getToken();
    if (!token) return;
    if (!current) {
      toast.error('Isi password saat ini.');
      return;
    }
    const pwError = validatePassword(next);
    if (pwError) {
      toast.error(pwError);
      return;
    }
    if (!passwordsMatch(next, confirm)) {
      toast.error('Konfirmasi password tidak cocok.');
      return;
    }
    setSaving(true);
    const res = await portalApi.changePassword(token, current, next);
    setSaving(false);
    if (res.success) {
      toast.success(res.message ?? 'Password berhasil diubah.');
      // The server revokes all sessions on change; force re-login.
      clearSession();
      onLoggedOut();
    } else {
      toast.error(res.error ?? 'Gagal mengubah password.');
    }
  };

  return (
    <div className="max-w-[760px] space-y-5">
      <div className="surface p-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-[20px] font-semibold" style={{ color: 'var(--c-ink)' }}>Pengaturan Akun</h2>
            <p className="text-[13px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>
              Informasi akun portal klien dan keamanan.
            </p>
          </div>
          <PortalBadge />
        </div>
      </div>

      <div className="surface p-6">
        <h3 className="text-[16px] font-semibold mb-4" style={{ color: 'var(--c-ink)' }}>Informasi Akun</h3>
        <dl className="grid sm:grid-cols-2 gap-4">
          <Row label="Perusahaan" value={actor?.companyName ?? '—'} />
          <Row label="Nama kontak" value={actor?.displayName ?? '—'} />
          <Row label="Email" value={actor?.email ?? '—'} />
          <Row label="Client ID" value={actor?.clientId || '—'} />
        </dl>
      </div>

      <form onSubmit={submit} noValidate className="surface p-6 space-y-4">
        <h3 className="text-[16px] font-semibold" style={{ color: 'var(--c-ink)' }}>Ganti Password</h3>
        <div>
          <label htmlFor="pw-current" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
            Password saat ini
          </label>
          <input id="pw-current" className="field" type="password" autoComplete="current-password" maxLength={128}
            value={current} onChange={(e) => setCurrent(e.target.value)} />
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="pw-new" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
              Password baru
            </label>
            <input id="pw-new" className="field" type="password" autoComplete="new-password" maxLength={128}
              value={next} onChange={(e) => setNext(e.target.value)} />
          </div>
          <div>
            <label htmlFor="pw-confirm" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
              Konfirmasi password
            </label>
            <input id="pw-confirm" className="field" type="password" autoComplete="new-password" maxLength={128}
              value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
        </div>
        <p className="text-[12px]" style={{ color: 'var(--c-ink-muted)' }}>
          Minimal 8 karakter, memuat huruf dan angka. Semua sesi akan dicabut setelah password diubah.
        </p>
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Menyimpan…' : 'Simpan Password'}
          </button>
        </div>
      </form>

      <div className="surface p-6 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h3 className="text-[16px] font-semibold" style={{ color: 'var(--c-ink)' }}>Keluar</h3>
          <p className="text-[13px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>Akhiri sesi portal di perangkat ini.</p>
        </div>
        <button type="button" className="btn-danger" onClick={onLoggedOut}>Keluar dari Portal</button>
      </div>
    </div>
  );
};

const Row: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <dt className="text-[12px] font-semibold uppercase tracking-wide" style={{ color: 'var(--c-ink-muted)' }}>{label}</dt>
    <dd className="text-[14px] font-semibold mt-0.5" style={{ color: 'var(--c-ink)' }}>{value}</dd>
  </div>
);

export default PortalSettingsView;
