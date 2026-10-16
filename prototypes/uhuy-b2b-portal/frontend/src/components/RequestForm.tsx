/**
 * RequestForm — shared form for submitting an external client request
 * (production order or design/sample). Writes go through the client-scoped
 * `/requests/{kind}` endpoint, so the server attributes them to the signed-in
 * client only.
 */

import React, { useState } from 'react';
import { getToken } from '../services/authSession';
import * as portalApi from '../services/portalApi';
import { toast } from '../services/toast';
import { MAKLON_SCHEMES, type RequestKind } from '../types/portal';

interface RequestFormProps {
  kind: RequestKind;
  onSubmitted: () => void;
}

interface FormState {
  article_name: string;
  quantity: string;
  scheme: string;
  target_date: string;
  notes: string;
}

const EMPTY: FormState = { article_name: '', quantity: '1', scheme: 'CMT', target_date: '', notes: '' };

const COPY: Record<RequestKind, { title: string; blurb: string; submit: string; qtyLabel: string }> = {
  order: {
    title: 'Ajukan Order Produksi',
    blurb: 'Kirim permintaan order produksi massal. Tim internal Lukla akan meninjau dan mengonfirmasi.',
    submit: 'Kirim Pengajuan Order',
    qtyLabel: 'Jumlah (pcs)',
  },
  sample: {
    title: 'Ajukan Permintaan Sample',
    blurb: 'Ajukan desain/sample baru. Sertakan catatan komponen atau bahan bila perlu.',
    submit: 'Kirim Permintaan Sample',
    qtyLabel: 'Jumlah sample (pcs)',
  },
};

const RequestForm: React.FC<RequestFormProps> = ({ kind, onSubmitted }) => {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const copy = COPY[kind];

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const article = form.article_name.trim();
    if (!article) {
      toast.error('Nama artikel wajib diisi.');
      return;
    }
    const quantity = Number.parseInt(form.quantity, 10);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      toast.error('Jumlah harus angka lebih dari 0.');
      return;
    }
    if (!MAKLON_SCHEMES.includes(form.scheme as (typeof MAKLON_SCHEMES)[number])) {
      toast.error('Pilih skema maklon yang valid.');
      return;
    }
    const token = getToken();
    if (!token) return;

    setSubmitting(true);
    const payload = {
      article_name: article,
      quantity,
      scheme: form.scheme,
      target_date: form.target_date,
      notes: form.notes.trim(),
    };
    const res =
      kind === 'order'
        ? await portalApi.createOrderRequest(token, payload)
        : await portalApi.createSampleRequest(token, payload);
    setSubmitting(false);

    if (res.success) {
      toast.success(res.message ?? 'Pengajuan terkirim.');
      setForm(EMPTY);
      onSubmitted();
    } else {
      toast.error(res.error ?? 'Gagal mengirim pengajuan.');
    }
  };

  return (
    <div className="max-w-[760px] mx-auto">
      <div className="surface p-6 mb-5">
        <h2 className="text-[20px] font-semibold" style={{ color: 'var(--c-ink)' }}>{copy.title}</h2>
        <p className="text-[13px] mt-1" style={{ color: 'var(--c-ink-muted)' }}>{copy.blurb}</p>
      </div>

      <form onSubmit={submit} noValidate className="surface p-6 space-y-5">
        <div>
          <label htmlFor="req-article" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
            Nama artikel / produk
          </label>
          <input id="req-article" className="field" type="text" maxLength={120}
            value={form.article_name} onChange={(e) => setForm({ ...form, article_name: e.target.value })} />
        </div>

        <div className="grid sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor="req-qty" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
              {copy.qtyLabel}
            </label>
            <input id="req-qty" className="field" type="number" min={1} inputMode="numeric"
              value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
          </div>
          <div>
            <label htmlFor="req-scheme" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
              Skema maklon
            </label>
            <select id="req-scheme" className="field" value={form.scheme}
              onChange={(e) => setForm({ ...form, scheme: e.target.value })}>
              {MAKLON_SCHEMES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="req-target" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
              Target selesai
            </label>
            <input id="req-target" className="field" type="date"
              value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })} />
          </div>
        </div>

        <div>
          <label htmlFor="req-notes" className="block font-medium mb-2 text-[13px]" style={{ color: 'var(--c-ink)' }}>
            Catatan
          </label>
          <textarea id="req-notes" className="field" rows={4} maxLength={1000}
            placeholder="Detail komponen, bahan, warna, atau instruksi khusus."
            value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>

        <div className="flex justify-end gap-3">
          <button type="button" className="btn-secondary" onClick={() => setForm(EMPTY)} disabled={submitting}>
            Reset
          </button>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? 'Mengirim…' : copy.submit}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RequestForm;
