/**
 * PortalAdminView — Admin IT approval queue for internal registrations.
 * Visible only to actors with role === 'admin' (see App nav wiring).
 */

import React, { useCallback, useEffect, useState } from 'react';
import * as authApi from '../services/authApi';
import type { RegistrationView } from '../services/authApi';
import { getToken } from '../services/authSession';
import { toast } from '../services/toast';

const PortalAdminView: React.FC = () => {
  const [items, setItems] = useState<RegistrationView[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    const res = await authApi.listRegistrations(token);
    setLoading(false);
    if (res.success && res.data) setItems(res.data);
    else toast.error(res.error ?? 'Gagal memuat pengajuan.');
  }, []);

  useEffect(() => { void load(); }, [load]);

  const decide = async (id: string, decision: 'approve' | 'reject') => {
    const token = getToken();
    if (!token) return;
    setBusyId(id);
    const res = await authApi.decideRegistration(token, id, decision);
    setBusyId(null);
    if (res.success) {
      toast.success(decision === 'approve' ? 'Pengajuan disetujui.' : 'Pengajuan ditolak.');
      void load();
    } else {
      toast.error(res.error ?? 'Gagal memproses pengajuan.');
    }
  };

  return (
    <div className="space-y-5">
      <div className="surface p-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-[20px] font-semibold" style={{ color: 'var(--c-ink)' }}>Persetujuan Akses</h2>
            <p className="text-[13px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>
              Verifikasi permintaan registrasi user internal pabrik.
            </p>
          </div>
          <button type="button" onClick={() => void load()} className="btn-secondary">
            Muat ulang
          </button>
        </div>
      </div>

      <div className="surface overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton h-10 w-full" />)}
          </div>
        ) : items.length === 0 ? (
          <p className="p-8 text-[14px]" style={{ color: 'var(--c-ink-muted)' }}>
            Tidak ada pengajuan yang menunggu verifikasi.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nama</th>
                <th>Email</th>
                <th>No. Karyawan</th>
                <th>Departemen</th>
                <th>No. HP</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.registration_id}>
                  <td style={{ color: 'var(--c-ink)', fontWeight: 600 }}>{item.full_name}</td>
                  <td>{item.email}</td>
                  <td><code>{item.employee_id}</code></td>
                  <td>{item.department}</td>
                  <td>{item.phone}</td>
                  <td>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn-pill btn-pill-green"
                        disabled={busyId === item.registration_id}
                        onClick={() => void decide(item.registration_id, 'approve')}
                      >
                        Setujui
                      </button>
                      <button
                        type="button"
                        className="btn-pill btn-pill-red"
                        disabled={busyId === item.registration_id}
                        onClick={() => void decide(item.registration_id, 'reject')}
                      >
                        Tolak
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default PortalAdminView;
