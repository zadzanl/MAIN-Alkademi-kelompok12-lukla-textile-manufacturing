/**
 * PortalAuthView — PT Luka internal portal entry (login / registration /
 * forgot-password). Rendered by App as an auth gate in front of the dashboard.
 *
 * Visuals follow the supplied portal design but reuse this app's design tokens
 * (index.css CSS variables + .field/.btn-primary/.tab) so light/dark mode,
 * focus rings, 48px touch targets and reduced-motion all work for free.
 */

import React, { useCallback, useRef, useState } from 'react';
import * as authApi from '../services/authApi';
import { setSession, type AuthSession } from '../services/authSession';
import {
  detectIdentifierKind,
  formatOtp,
  identifierHint,
  isValidEmail,
  isValidKtp,
  isValidPhone,
  passwordStrength,
  passwordsMatch,
  validatePassword,
} from '../services/authRules';

type Mode = 'login' | 'register' | 'forgot';
type ForgotStep = 'request' | 'reset';
type Feedback = { kind: 'info' | 'error' | 'success'; text: string } | null;

interface PortalAuthViewProps {
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
      className="mt-4 rounded-[11px] px-4 py-3 text-[13px] leading-relaxed"
      style={FEEDBACK_STYLE[value.kind]}
    >
      {value.text}
    </p>
  );
};

const Field: React.FC<{
  id: string;
  label: string;
  children: React.ReactNode;
  hint?: string;
}> = ({ id, label, children, hint }) => (
  <div>
    <label htmlFor={id} className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
      {label}
    </label>
    {children}
    {hint && (
      <p className="mt-1.5 text-[12px]" style={{ color: 'var(--c-ink-muted)' }}>
        {hint}
      </p>
    )}
  </div>
);

const PortalAuthView: React.FC<PortalAuthViewProps> = ({ onAuthenticated }) => {
  const [mode, setMode] = useState<Mode>('login');
  const [guideOpen, setGuideOpen] = useState(false);

  // ── login ──────────────────────────────────────────────────────────────────
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [loginFeedback, setLoginFeedback] = useState<Feedback>(null);
  const [loggingIn, setLoggingIn] = useState(false);

  // ── register ───────────────────────────────────────────────────────────────
  const [reg, setReg] = useState({
    full_name: '',
    email: '',
    employee_id: '',
    ktp_id: '',
    phone: '',
    department: '',
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
      setLoginFeedback({ kind: 'error', text: 'Isi nomor karyawan, NIK/KTP, email, atau nomor HP.' });
      return;
    }
    setLoggingIn(true);
    setLoginFeedback(null);
    const res = await authApi.login(identifier, password, remember);
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
      ['Nama lengkap', !reg.full_name.trim()],
      ['Email perusahaan', !isValidEmail(reg.email)],
      ['Nomor karyawan', !reg.employee_id.trim()],
      ['NIK/KTP (16 digit)', !isValidKtp(reg.ktp_id)],
      ['Nomor HP', !isValidPhone(reg.phone)],
      ['Departemen', !reg.department.trim()],
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
      setRegFeedback({ kind: 'error', text: 'Setujui permintaan akses internal terlebih dahulu.' });
      return;
    }
    setRegistering(true);
    setRegFeedback(null);
    const res = await authApi.register({
      full_name: reg.full_name.trim(),
      email: reg.email.trim(),
      employee_id: reg.employee_id.trim(),
      ktp_id: reg.ktp_id.trim(),
      phone: reg.phone.trim(),
      department: reg.department.trim(),
      password: reg.password,
      consent,
    });
    setRegistering(false);
    if (res.success) {
      setReg({ full_name: '', email: '', employee_id: '', ktp_id: '', phone: '', department: '', password: '', confirm: '' });
      setConsent(false);
      setMode('login');
      setLoginFeedback({
        kind: 'success',
        text: 'Pengajuan diterima. Akun akan aktif setelah diverifikasi Admin IT.',
      });
      return;
    }
    setRegFeedback({ kind: 'error', text: res.error ?? 'Gagal mengirim pengajuan.' });
  };

  const handleForgotRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!forgotIdentifier.trim()) {
      setForgotFeedback({ kind: 'error', text: 'Isi identitas terdaftar Anda.' });
      return;
    }
    setResetting(true);
    setForgotFeedback(null);
    const res = await authApi.forgotPassword(forgotIdentifier);
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
    const res = await authApi.resetPassword(forgotIdentifier, otp, resetPasswordValue);
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
  const strengthLabel: Record<typeof strength, string> = {
    weak: 'Lemah',
    fair: 'Cukup',
    strong: 'Kuat',
  };

  // ── render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-page)' }}>
      {/* Header */}
      <header className="border-b" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
        <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-8 lg:px-16 flex items-center justify-between gap-4 py-5">
          <span className="text-[22px] font-semibold tracking-tight" style={{ color: 'var(--c-ink)' }}>
            PT Luka
          </span>
          <span className="rounded-full border px-3 py-1.5 text-[12px]" style={{ borderColor: 'var(--c-hair)', color: 'var(--c-ink-muted)' }}>
            Portal Internal
          </span>
        </div>
      </header>

      <main className="flex-1">
        <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-8 lg:px-16 pt-12 sm:pt-20 pb-12">
          {/* Hero */}
          <p className="text-[12px] font-semibold uppercase tracking-[.16em] mb-5" style={{ color: 'var(--c-brand)' }}>
            Backoffice · PT Luka
          </p>
          <h1 className="text-[32px] font-semibold tracking-tight leading-tight mb-5" style={{ color: 'var(--c-ink)' }}>
            Selamat Datang di Portal PT Luka
          </h1>
          <p className="max-w-[660px] text-[18px] leading-relaxed mb-10" style={{ color: 'var(--c-ink-muted)' }}>
            Akses informasi operasional garment, produksi, order, inventori, dan laporan internal dalam satu portal.
          </p>

          {/* Form surface */}
          <section
            aria-label="Akses portal"
            className="surface max-w-[760px] mx-auto p-6 sm:p-9"
          >
            <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
              <div>
                <h2 className="text-[24px] font-semibold mb-1" style={{ color: 'var(--c-ink)' }}>
                  {mode === 'forgot' ? 'Lupa akses' : 'Akses portal'}
                </h2>
                <p className="text-[14px]" style={{ color: 'var(--c-ink-muted)' }}>
                  {mode === 'forgot' ? 'Setel ulang password dengan kode verifikasi.' : 'Pilih cara untuk melanjutkan.'}
                </p>
              </div>
              <span className="inline-flex items-center gap-2 text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>
                <span className="w-2 h-2 rounded-full" style={{ background: 'var(--c-brand)' }} aria-hidden="true" />
                Khusus internal
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
                    className="tab flex-1 py-2.5 px-4 font-semibold text-[16px]"
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
                  label="Nomor karyawan, NIK/KTP, email, atau nomor HP"
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

                <div className="flex items-center justify-between flex-wrap gap-3 mt-5 mb-6">
                  <label className="inline-flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="w-4 h-4"
                      style={{ accentColor: 'var(--c-brand)' }}
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    <span className="text-[14px]" style={{ color: 'var(--c-ink)' }}>Ingat saya</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => selectMode('forgot')}
                    className="text-[14px] font-medium hover:underline"
                    style={{ color: 'var(--c-brand)' }}
                  >
                    Lupa akses?
                  </button>
                </div>

                <button type="submit" className="btn-primary w-full justify-center text-[16px]" disabled={loggingIn}>
                  {loggingIn ? 'Memproses…' : 'Masuk ke Portal'}
                </button>

                <p className="mt-4 text-[13px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                  Autentikasi memakai identitas internal resmi (ID karyawan/NIK) dan password Anda.
                </p>
                <Feedback value={loginFeedback} />
              </form>
            )}

            {/* REGISTER */}
            {mode === 'register' && (
              <form onSubmit={handleRegister} noValidate>
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field id="reg-name" label="Nama lengkap">
                    <input id="reg-name" className="field" type="text" autoComplete="name" maxLength={100}
                      value={reg.full_name} onChange={(e) => setReg({ ...reg, full_name: e.target.value })} />
                  </Field>
                  <Field id="reg-email" label="Email perusahaan">
                    <input id="reg-email" className="field" type="email" autoComplete="email" maxLength={120}
                      value={reg.email} onChange={(e) => setReg({ ...reg, email: e.target.value })} />
                  </Field>
                  <Field id="reg-employee" label="Nomor karyawan">
                    <input id="reg-employee" className="field" type="text" maxLength={40}
                      value={reg.employee_id} onChange={(e) => setReg({ ...reg, employee_id: e.target.value })} />
                  </Field>
                  <Field id="reg-ktp" label="NIK / KTP" hint="16 digit angka">
                    <input id="reg-ktp" className="field" type="text" inputMode="numeric" maxLength={16}
                      value={reg.ktp_id} onChange={(e) => setReg({ ...reg, ktp_id: e.target.value.replace(/\D/g, '') })} />
                  </Field>
                  <Field id="reg-phone" label="Nomor HP">
                    <input id="reg-phone" className="field" type="tel" inputMode="tel" maxLength={20}
                      value={reg.phone} onChange={(e) => setReg({ ...reg, phone: e.target.value })} />
                  </Field>
                  <Field id="reg-department" label="Departemen">
                    <input id="reg-department" className="field" type="text" maxLength={80}
                      value={reg.department} onChange={(e) => setReg({ ...reg, department: e.target.value })} />
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

                <label className="flex items-start gap-3 mt-6 mb-6 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 mt-1 shrink-0" style={{ accentColor: 'var(--c-brand)' }}
                    checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                  <span className="text-[14px] leading-relaxed" style={{ color: 'var(--c-ink)' }}>
                    Saya menyetujui pengajuan permintaan akses internal untuk diverifikasi Admin IT.
                  </span>
                </label>

                <button type="submit" className="btn-primary w-full justify-center text-[16px]" disabled={registering}>
                  {registering ? 'Mengirim…' : 'Ajukan Registrasi'}
                </button>
                <p className="mt-4 text-[13px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                  Permintaan diverifikasi Admin IT. Data identitas disimpan aman; NIK/KTP disimpan sebagai hash.
                </p>
                <Feedback value={regFeedback} />
              </form>
            )}

            {/* FORGOT / RESET */}
            {mode === 'forgot' && (
              <div>
                {forgotStep === 'request' ? (
                  <form onSubmit={handleForgotRequest} noValidate>
                    <Field id="forgot-identity" label="Nomor karyawan, NIK/KTP, email, atau nomor HP">
                      <input id="forgot-identity" className="field" type="text" maxLength={120}
                        value={forgotIdentifier} onChange={(e) => setForgotIdentifier(e.target.value)} />
                    </Field>
                    <button type="submit" className="btn-primary w-full justify-center text-[16px] mt-6" disabled={resetting}>
                      {resetting ? 'Mengirim…' : 'Kirim kode verifikasi'}
                    </button>
                    <p className="mt-4 text-[13px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                      Kode verifikasi dikirim ke email perusahaan yang terdaftar.
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
                    <div className="grid sm:grid-cols-2 gap-4 mt-4">
                      <Field id="forgot-new" label="Password baru">
                        <input id="forgot-new" className="field" type="password" autoComplete="new-password" maxLength={128}
                          value={resetPasswordValue} onChange={(e) => setResetPasswordValue(e.target.value)} />
                      </Field>
                      <Field id="forgot-confirm" label="Konfirmasi password">
                        <input id="forgot-confirm" className="field" type="password" autoComplete="new-password" maxLength={128}
                          value={resetConfirm} onChange={(e) => setResetConfirm(e.target.value)} />
                      </Field>
                    </div>
                    <button type="submit" className="btn-primary w-full justify-center text-[16px] mt-6" disabled={resetting}>
                      {resetting ? 'Menyimpan…' : 'Setel ulang password'}
                    </button>
                    <Feedback value={forgotFeedback} />
                  </form>
                )}
                <button
                  type="button"
                  onClick={() => selectMode('login')}
                  className="mt-5 text-[14px] font-medium hover:underline"
                  style={{ color: 'var(--c-brand)' }}
                >
                  ← Kembali ke Login
                </button>
              </div>
            )}
          </section>

          {/* Security aside */}
          <aside
            className="surface max-w-[760px] mx-auto mt-4 p-5 sm:px-7 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div>
              <h2 className="text-[24px] font-semibold mb-1" style={{ color: 'var(--c-ink)' }}>
                Akses internal dan terverifikasi
              </h2>
              <p className="text-[14px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                Gunakan kanal resmi perusahaan untuk bantuan akses.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setGuideOpen((open) => !open)}
              aria-expanded={guideOpen}
              className="shrink-0 rounded-[12px] border px-4 py-2.5 text-[14px] font-semibold"
              style={{ borderColor: 'var(--c-brand-soft)', color: 'var(--c-brand)' }}
            >
              Hubungi Admin IT
            </button>
          </aside>

          {guideOpen && (
            <div
              className="max-w-[760px] mx-auto mt-3 p-5 rounded-[12px] border"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--c-brand-soft)' }}
            >
              <h3 className="text-[19px] font-semibold mb-2" style={{ color: 'var(--c-ink)' }}>
                Panduan menghubungi Admin IT
              </h3>
              <p className="text-[14px] leading-relaxed" style={{ color: 'var(--c-ink-muted)' }}>
                Temukan kontak Admin IT melalui direktori perusahaan atau kanal komunikasi internal resmi.
                Jangan membagikan password maupun kode verifikasi kepada siapa pun.
              </p>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t" style={{ background: 'var(--bg-card)', borderColor: 'var(--c-hair)' }}>
        <div className="mx-auto w-full max-w-[1120px] px-5 sm:px-8 lg:px-16 py-6">
          <p className="text-[13px]" style={{ color: 'var(--c-ink-muted)' }}>© PT Luka · Portal Internal</p>
        </div>
      </footer>
    </div>
  );
};

export default PortalAuthView;
