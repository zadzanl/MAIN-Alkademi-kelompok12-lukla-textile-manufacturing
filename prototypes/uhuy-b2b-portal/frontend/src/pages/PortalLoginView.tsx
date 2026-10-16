/**
 * PortalLoginView — UHUY B2B external client portal entry (login / registration
 * / forgot-password). Rendered by App as an auth gate in front of the portal.
 *
 * Reuses the app's design tokens (index.css variables + .field/.btn-primary/.tab)
 * so light/dark mode, focus rings, 48px touch targets and reduced-motion all work
 * for free. Carries the EXTERNAL portal marker prominently.
 */

import React, { useCallback, useRef, useState } from 'react';
import * as portalApi from '../services/portalApi';
import { setSession, type AuthSession } from '../services/authSession';
import {
  detectIdentifierKind,
  formatOtp,
  identifierHint,
  isValidEmail,
  isValidPhone,
  passwordStrength,
  passwordsMatch,
  validatePassword,
} from '../services/authRules';
import PortalBadge from '../components/PortalBadge';

type Mode = 'login' | 'register' | 'forgot';
type ForgotStep = 'request' | 'reset';
type Feedback = { kind: 'info' | 'error' | 'success'; text: string } | null;

interface PortalLoginViewProps {
  onAuthenticated: (session: AuthSession) => void;
}

const FEEDBACK_STYLE: Record<NonNullable<Feedback>['kind'], React.CSSProperties> = {
  info: { background: 'var(--c-brand-bg)', color: 'var(--c-brand)' },
  error: { background: 'var(--c-bad-bg)', color: 'var(--c-bad-4)' },
  success: { background: 'var(--c-ok-bg)', color: 'var(--c-ok-2)' },
};

const Feedback: React.FC<{ value: Feedback }> = ({ value }) => {
  if (!value) return null;
  return (
    <p
      role="status"
      aria-live="polite"
      className="mt-4 rounded-[11px] px-3 py-2 text-[15px] leading-relaxed"
      style={FEEDBACK_STYLE[value.kind]}
    >
      {value.text}
    </p>
  );
};

const Field: React.FC<{ id: string; label: string; children: React.ReactNode; hint?: string }> = ({
  id,
  label,
  children,
  hint,
}) => (
  <div>
    <label htmlFor={id} className="block font-medium mb-2 text-[15px]" style={{ color: 'var(--c-ink)' }}>
      {label}
    </label>
    {children}
    {hint && (
      <p className="mt-1.5 text-[14px]" style={{ color: 'var(--c-ink-muted)' }}>
        {hint}
      </p>
    )}
  </div>
);

const PortalLoginView: React.FC<PortalLoginViewProps> = ({ onAuthenticated }) => {
  const [mode, setMode] = useState<Mode>('login');

  // ── login ──────────────────────────────────────────────────────────────────
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [loginFeedback, setLoginFeedback] = useState<Feedback>(null);
  const [loggingIn, setLoggingIn] = useState(false);

  // ── register ───────────────────────────────────────────────────────────────
  const [reg, setReg] = useState({
    company_name: '',
    contact_name: '',
    email: '',
    phone: '',
    password: '',
    confirm: '',
  });
  const [consent, setConsent] = useState(false);
  const [regFeedback, setRegFeedback] = useState<Feedback>(null);
  const [registering, setRegistering] = useState(false);

  // ── forgot / reset ─────────────────────────────────────────────────────────
  const [forgotStep, setForgotStep] = useState<ForgotStep>('request');
  const [forgotIdentifier, setForgotIdentifier] = useState('');
  const [otp, setOtp] = useState('');
  const [resetPasswordValue, setResetPasswordValue] = useState('');
  const [resetConfirm, setResetConfirm] = useState('');
  const [forgotFeedback, setForgotFeedback] = useState<Feedback>(null);
  const [resetting, setResetting] = useState(false);

  const tabsRef = useRef<(HTMLButtonElement | null)[]>([]);

  const selectMode = useCallback((next: Mode) => {
    setMode(next);
    setLoginFeedback(null);
    setRegFeedback(null);
    setForgotFeedback(null);
  }, []);

  // ── handlers ───────────────────────────────────────────────────────────────

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!identifier.trim()) {
      setLoginFeedback({ kind: 'error', text: 'Isi email atau nomor HP Anda.' });
      return;
    }
    setLoggingIn(true);
    setLoginFeedback(null);
    const res = await portalApi.login(identifier, password, remember);
    setLoggingIn(false);
    if (res.success && res.data) {
      const session: AuthSession = { token: res.data.accessToken, actor: res.data.actor };
      setSession(session);
      onAuthenticated(session);
      return;
    }
    setLoginFeedback({ kind: 'error', text: res.error ?? 'Gagal masuk.' });
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    const fields: Array<[string, boolean]> = [
      ['Nama perusahaan', !reg.company_name.trim()],
      ['Nama kontak', !reg.contact_name.trim()],
      ['Email', !isValidEmail(reg.email)],
      ['Nomor HP', !isValidPhone(reg.phone)],
    ];
    const invalid = fields.find(([, bad]) => bad);
    if (invalid) {
      setRegFeedback({ kind: 'error', text: `Periksa kembali: ${invalid[0]}.` });
      return;
    }
    const pwError = validatePassword(reg.password);
    if (pwError) {
      setRegFeedback({ kind: 'error', text: pwError });
      return;
    }
    if (!passwordsMatch(reg.password, reg.confirm)) {
      setRegFeedback({ kind: 'error', text: 'Konfirmasi password tidak cocok.' });
      return;
    }
    if (!consent) {
      setRegFeedback({ kind: 'error', text: 'Setujui permintaan akses portal terlebih dahulu.' });
      return;
    }
    setRegistering(true);
    setRegFeedback(null);
    const res = await portalApi.register({
      company_name: reg.company_name.trim(),
      contact_name: reg.contact_name.trim(),
      email: reg.email.trim(),
      phone: reg.phone.trim(),
      password: reg.password,
      consent,
    });
    setRegistering(false);
    if (res.success) {
      setReg({ company_name: '', contact_name: '', email: '', phone: '', password: '', confirm: '' });
      setConsent(false);
      setMode('login');
      setLoginFeedback({
        kind: 'success',
        text: 'Pengajuan diterima. Akun akan aktif setelah diverifikasi tim internal Lukla.',
      });
      return;
    }
    setRegFeedback({ kind: 'error', text: res.error ?? 'Gagal mengirim pengajuan.' });
  };

  const handleForgotRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!forgotIdentifier.trim()) {
      setForgotFeedback({ kind: 'error', text: 'Isi email atau nomor HP terdaftar Anda.' });
      return;
    }
    setResetting(true);
    setForgotFeedback(null);
    const res = await portalApi.forgotPassword(forgotIdentifier);
    setResetting(false);
    if (res.success) {
      setForgotStep('reset');
      setForgotFeedback({
        kind: 'info',
        text: res.message ?? 'Jika identitas terdaftar, kode verifikasi telah dikirim ke email Anda.',
      });
      return;
    }
    setForgotFeedback({ kind: 'error', text: res.error ?? 'Gagal meminta kode verifikasi.' });
  };

  const handleReset = async (event: React.FormEvent) => {
    event.preventDefault();
    if (otp.length !== 6) {
      setForgotFeedback({ kind: 'error', text: 'Kode verifikasi harus 6 digit.' });
      return;
    }
    const pwError = validatePassword(resetPasswordValue);
    if (pwError) {
      setForgotFeedback({ kind: 'error', text: pwError });
      return;
    }
    if (!passwordsMatch(resetPasswordValue, resetConfirm)) {
      setForgotFeedback({ kind: 'error', text: 'Konfirmasi password tidak cocok.' });
      return;
    }
    setResetting(true);
    setForgotFeedback(null);
    const res = await portalApi.resetPassword(forgotIdentifier, otp, resetPasswordValue);
    setResetting(false);
    if (res.success) {
      setForgotStep('request');
      setOtp('');
      setResetPasswordValue('');
      setResetConfirm('');
      setMode('login');
      setLoginFeedback({ kind: 'success', text: 'Password berhasil disetel ulang. Silakan masuk.' });
      return;
    }
    setForgotFeedback({ kind: 'error', text: res.error ?? 'Kode verifikasi salah atau kedaluwarsa.' });
  };

  const onTabKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const next = index === 0 ? 1 : 0;
    selectMode(next === 0 ? 'login' : 'register');
    tabsRef.current[next]?.focus();
  };

  const strength = passwordStrength(reg.password);
  const strengthLabel: Record<typeof strength, string> = { weak: 'Lemah', fair: 'Cukup', strong: 'Kuat' };

  // ── render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-page)' }}>
      <div className="portal-ribbon">
        <strong>UHUY B2B</strong>
        <span aria-hidden="true">·</span>
        <span>Portal Klien Eksternal</span>
      </div>

      <header className="border-b" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
        <div className="mx-auto w-full max-w-[1360px] px-5 sm:px-8 lg:px-16 flex items-center justify-between gap-3 py-5">
          <span className="text-[24px] font-semibold tracking-tight" style={{ color: 'var(--c-ink)' }}>
            UHUY B2B
          </span>
          <PortalBadge />
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto w-full max-w-[1360px] px-5 sm:px-8 lg:px-16 pt-12 sm:pt-20 pb-12">
          <p className="text-[14px] font-semibold uppercase tracking-[.16em] mb-5" style={{ color: 'var(--c-brand)' }}>
            Portal Klien · Eksternal
          </p>
          <h1 className="text-[34px] font-semibold tracking-tight leading-tight mb-5" style={{ color: 'var(--c-ink)' }}>
            Selamat Datang di Portal Klien UHUY B2B
          </h1>
          <p className="max-w-[660px] text-[19px] leading-relaxed mb-7" style={{ color: 'var(--c-ink-muted)' }}>
            Ajukan order dan permintaan desain/sample, pantau progres produksi, dan lihat saldo bahan titipan Anda —
            semua dalam satu portal mandiri.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-7 max-w-[980px]">
            {([
              { key: 'login' as Mode, title: 'Login', copy: 'Masuk untuk memantau order dan pengajuan Anda.', glyph: '↗' },
              { key: 'register' as Mode, title: 'Registrasi', copy: 'Ajukan akses portal klien baru.', glyph: '＋' },
            ]).map((card) => {
              const selected = mode === card.key || (mode === 'forgot' && card.key === 'login');
              return (
                <button
                  key={card.key}
                  type="button"
                  onClick={() => selectMode(card.key)}
                  aria-pressed={selected}
                  className="text-left p-4 sm:p-5 rounded-[20px] border transition-transform"
                  style={{
                    background: 'var(--bg-card)',
                    borderColor: selected ? 'var(--c-brand-soft)' : 'var(--c-hair)',
                    boxShadow: selected
                      ? '0 0 0 3px var(--c-brand-bg), 0 10px 30px rgba(29,29,31,.06)'
                      : '0 10px 30px rgba(29,29,31,.03)',
                  }}
                >
                  <span
                    className="w-[46px] h-[46px] rounded-[13px] grid place-items-center text-[24px] font-semibold mb-4"
                    style={{ background: 'var(--c-brand-bg)', color: 'var(--c-brand)' }}
                    aria-hidden="true"
                  >
                    {card.glyph}
                  </span>
                  <span className="block text-[24px] font-semibold mb-2" style={{ color: 'var(--c-ink)' }}>
                    {card.title}
                  </span>
                  <span className="block text-[15px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                    {card.copy}
                  </span>
                </button>
              );
            })}
          </div>

          <section aria-label="Akses portal klien" className="surface max-w-[760px] p-4 sm:p-7">
            <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
              <div>
                <h2 className="text-[26px] font-semibold mb-1" style={{ color: 'var(--c-ink)' }}>
                  {mode === 'forgot' ? 'Lupa akses' : 'Akses portal klien'}
                </h2>
                <p className="text-[15px]" style={{ color: 'var(--c-ink-muted)' }}>
                  {mode === 'forgot' ? 'Setel ulang password dengan kode verifikasi.' : 'Pilih cara untuk melanjutkan.'}
                </p>
              </div>
              <span className="inline-flex items-center gap-2 text-[15px]" style={{ color: 'var(--c-ink-muted)' }}>
                <span className="w-2 h-2 rounded-full" style={{ background: 'var(--c-brand)' }} aria-hidden="true" />
                Khusus klien eksternal
              </span>
            </div>

            {mode !== 'forgot' && (
              <div
                className="flex gap-1 mb-7 rounded-[12px] p-1"
                style={{ background: 'var(--c-panel-2)' }}
                role="tablist"
                aria-label="Pilihan akses"
              >
                {(['login', 'register'] as const).map((tab, index) => (
                  <button
                    key={tab}
                    ref={(el) => { tabsRef.current[index] = el; }}
                    type="button"
                    role="tab"
                    aria-selected={mode === tab}
                    tabIndex={mode === tab ? 0 : -1}
                    onClick={() => selectMode(tab)}
                    onKeyDown={(e) => onTabKeyDown(e, index)}
                    className="tab flex-1 py-2.5 px-4 font-semibold text-[17px]"
                  >
                    {tab === 'login' ? 'Login' : 'Registrasi'}
                  </button>
                ))}
              </div>
            )}

            {/* LOGIN */}
            {mode === 'login' && (
              <form onSubmit={handleLogin} noValidate>
                <Field
                  id="login-identity"
                  label="Email atau nomor HP"
                  hint={identifierHint(detectIdentifierKind(identifier))}
                >
                  <input
                    id="login-identity"
                    className="field"
                    type="text"
                    autoComplete="username"
                    maxLength={120}
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                  />
                </Field>

                <div className="mt-4">
                  <Field id="login-password" label="Password">
                    <input
                      id="login-password"
                      className="field"
                      type="password"
                      autoComplete="current-password"
                      maxLength={128}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </Field>
                </div>

                <div className="flex items-center justify-between flex-wrap gap-3 mt-5 mb-4">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4"
                      style={{ accentColor: 'var(--c-brand)' }}
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    <span className="text-[15px]" style={{ color: 'var(--c-ink)' }}>Ingat saya</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => selectMode('forgot')}
                    className="text-[15px] font-medium hover:underline"
                    style={{ color: 'var(--c-brand)' }}
                  >
                    Lupa akses?
                  </button>
                </div>

                <button type="submit" className="btn-primary w-full justify-center text-[17px]" disabled={loggingIn}>
                  {loggingIn ? 'Memproses…' : 'Masuk ke Portal'}
                </button>
                <Feedback value={loginFeedback} />
              </form>
            )}

            {/* REGISTER */}
            {mode === 'register' && (
              <form onSubmit={handleRegister} noValidate>
                <div className="grid sm:grid-cols-2 gap-3">
                  <Field id="reg-company" label="Nama perusahaan">
                    <input id="reg-company" className="field" type="text" autoComplete="organization" maxLength={120}
                      value={reg.company_name} onChange={(e) => setReg({ ...reg, company_name: e.target.value })} />
                  </Field>
                  <Field id="reg-contact" label="Nama kontak">
                    <input id="reg-contact" className="field" type="text" autoComplete="name" maxLength={100}
                      value={reg.contact_name} onChange={(e) => setReg({ ...reg, contact_name: e.target.value })} />
                  </Field>
                  <Field id="reg-email" label="Email">
                    <input id="reg-email" className="field" type="email" autoComplete="email" maxLength={120}
                      value={reg.email} onChange={(e) => setReg({ ...reg, email: e.target.value })} />
                  </Field>
                  <Field id="reg-phone" label="Nomor HP">
                    <input id="reg-phone" className="field" type="tel" inputMode="tel" maxLength={20}
                      value={reg.phone} onChange={(e) => setReg({ ...reg, phone: e.target.value })} />
                  </Field>
                  <Field id="reg-password" label="Password" hint={`Kekuatan: ${strengthLabel[strength]}`}>
                    <input id="reg-password" className="field" type="password" autoComplete="new-password" maxLength={128}
                      value={reg.password} onChange={(e) => setReg({ ...reg, password: e.target.value })} />
                  </Field>
                  <Field id="reg-confirm" label="Konfirmasi password">
                    <input id="reg-confirm" className="field" type="password" autoComplete="new-password" maxLength={128}
                      value={reg.confirm} onChange={(e) => setReg({ ...reg, confirm: e.target.value })} />
                  </Field>
                </div>

                <label className="flex items-start gap-3 mt-6 mb-4 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 mt-1 shrink-0" style={{ accentColor: 'var(--c-brand)' }}
                    checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                  <span className="text-[15px] leading-relaxed" style={{ color: 'var(--c-ink)' }}>
                    Saya menyetujui pengajuan permintaan akses portal klien untuk diverifikasi tim internal Lukla.
                  </span>
                </label>

                <button type="submit" className="btn-primary w-full justify-center text-[17px]" disabled={registering}>
                  {registering ? 'Mengirim…' : 'Ajukan Registrasi'}
                </button>
                <p className="mt-4 text-[15px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                  Permintaan diverifikasi tim internal Lukla. Data akses disimpan aman.
                </p>
                <Feedback value={regFeedback} />
              </form>
            )}

            {/* FORGOT / RESET */}
            {mode === 'forgot' && (
              <div>
                {forgotStep === 'request' ? (
                  <form onSubmit={handleForgotRequest} noValidate>
                    <Field id="forgot-identity" label="Email atau nomor HP">
                      <input id="forgot-identity" className="field" type="text" maxLength={120}
                        value={forgotIdentifier} onChange={(e) => setForgotIdentifier(e.target.value)} />
                    </Field>
                    <button type="submit" className="btn-primary w-full justify-center text-[17px] mt-6" disabled={resetting}>
                      {resetting ? 'Mengirim…' : 'Kirim kode verifikasi'}
                    </button>
                    <p className="mt-4 text-[15px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                      Kode verifikasi dikirim ke email yang terdaftar.
                    </p>
                    <Feedback value={forgotFeedback} />
                  </form>
                ) : (
                  <form onSubmit={handleReset} noValidate>
                    <Field id="forgot-otp" label="Kode verifikasi (6 digit)">
                      <input id="forgot-otp" className="field tracking-[.4em] text-center" type="text"
                        inputMode="numeric" maxLength={6} value={otp}
                        onChange={(e) => setOtp(formatOtp(e.target.value))} />
                    </Field>
                    <div className="grid sm:grid-cols-2 gap-3 mt-4">
                      <Field id="forgot-new" label="Password baru">
                        <input id="forgot-new" className="field" type="password" autoComplete="new-password" maxLength={128}
                          value={resetPasswordValue} onChange={(e) => setResetPasswordValue(e.target.value)} />
                      </Field>
                      <Field id="forgot-confirm" label="Konfirmasi password">
                        <input id="forgot-confirm" className="field" type="password" autoComplete="new-password" maxLength={128}
                          value={resetConfirm} onChange={(e) => setResetConfirm(e.target.value)} />
                      </Field>
                    </div>
                    <button type="submit" className="btn-primary w-full justify-center text-[17px] mt-6" disabled={resetting}>
                      {resetting ? 'Menyimpan…' : 'Setel ulang password'}
                    </button>
                    <Feedback value={forgotFeedback} />
                  </form>
                )}
                <button
                  type="button"
                  onClick={() => selectMode('login')}
                  className="mt-5 text-[15px] font-medium hover:underline"
                  style={{ color: 'var(--c-brand)' }}
                >
                  ← Kembali ke Login
                </button>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="border-t" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
        <div className="mx-auto w-full max-w-[1360px] px-5 sm:px-8 lg:px-16 py-6">
          <p className="text-[15px]" style={{ color: 'var(--c-ink-muted)' }}>
            © Lukla Manufacturing · Portal Klien Eksternal UHUY B2B
          </p>
        </div>
      </footer>
    </div>
  );
};

export default PortalLoginView;
