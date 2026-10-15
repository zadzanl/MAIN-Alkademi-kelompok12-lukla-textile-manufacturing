/**
 * SampleVersionView — Version History Tree + Component Spec + Material Estimation
 * PRD: Manajemen Versi Sample (v1 → v2 → converted to Mass Order)
 */

import React, { useState, useEffect, useCallback } from 'react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { LucideIcon } from '../components/Sidebar';
import { generateId } from '../lib/uuid';
import type { SampleVersion, GarmentComponent, MaterialEstimation, ExportCSV } from '../types';
import * as api from '../services/api';
import { toast } from '../services/toast';
import { TENANT_ID, actor, APPROVER_ID } from '../services/identity';

const STATUS_STYLE: Record<string, string> = {
  draft:            'bg-[#e8f2ff] text-[#0066cc]',
  pending_approval: 'bg-[#fff4e6] text-[#ff9500]',
  approved:         'bg-[#e8f5e9] text-[#34c759]',
  converted:        'bg-[#f0f0f2] text-[#626269]',
};
const STATUS_LABEL: Record<string, string> = {
  draft:            'Draft',
  pending_approval: 'Menunggu Persetujuan',
  approved:         'Disetujui',
  converted:        'Dikonversi ke Order',
};

const Badge: React.FC<{ status: string }> = ({ status }) => (
  <span className={`pill rounded-full px-2.5 py-1 text-[11px] font-semibold ${STATUS_STYLE[status] ?? 'bg-[#f0f0f2] text-[#626269]'}`}>
    {STATUS_LABEL[status] ?? status}
  </span>
);

interface Props {
  onExportCSV: ExportCSV;
}

const EMPTY_COMPONENT: Omit<GarmentComponent, 'component_id'> = {
  part_name: '', description: '', material_type: '',
  estimated_usage_m: 0, unit: 'm', sewing_time_std_ms: 0,
  rate_card_idr: 0, notes: '',
};
const EMPTY_MATERIAL: MaterialEstimation = {
  material_code: '', material_name: '', estimated_usage: 0,
  unit: 'm', unit_cost: 0, total_cost: 0, supplier_id: '', notes: '',
};

const SampleVersionView: React.FC<Props> = ({ onExportCSV }) => {
  const [versions, setVersions]           = useState<SampleVersion[]>([]);
  const [selected, setSelected]           = useState<SampleVersion | null>(null);
  const [tab, setTab]                     = useState('all');
  const [search, setSearch]               = useState('');

  // modals
  const [showCreate, setShowCreate]       = useState(false);
  const [showRevise, setShowRevise]       = useState(false);
  const [showCompModal, setShowCompModal] = useState(false);
  const [showMatModal, setShowMatModal]   = useState(false);
  const [showHistory, setShowHistory]     = useState(false);
  const [historyVersions, setHistoryVersions] = useState<SampleVersion[]>([]);

  // create form
  const [form, setForm] = useState({
    article_id: '', article_name: '', client_id: '',
    notes: '',
  });
  const [revisionNote, setRevisionNote] = useState('');

  // inline component editor state
  const [editComponents, setEditComponents] = useState<GarmentComponent[]>([]);
  const [editMaterials, setEditMaterials]   = useState<MaterialEstimation[]>([]);

  // ── fetch ──────────────────────────────────────────────────────────

  const fetchAll = useCallback(async () => {
    const res = await api.listSampleVersions(TENANT_ID);
    if (res.success && res.data) setVersions(res.data);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── filtered list ──────────────────────────────────────────────────

  const filtered = versions.filter(v => {
    if (tab !== 'all' && v.status !== tab) return false;
    if (search && !v.article_name.toLowerCase().includes(search.toLowerCase()) &&
        !v.article_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // ── actions ────────────────────────────────────────────────────────

  const handleCreate = async () => {
    if (!form.article_id || !form.article_name || !form.client_id) {
      toast.error('Article ID, Nama Artikel, dan Client ID wajib diisi.'); return;
    }
    const res = await api.createSampleVersion({ tenant_id: TENANT_ID, ...form, created_by: actor() });
    if (res.success) {
      setShowCreate(false);
      setForm({ article_id: '', article_name: '', client_id: '', notes: '' });
      fetchAll();
    } else {
      toast.error(res.error ?? 'Gagal membuat versi sample.');
    }
  };

  const handleRevise = async () => {
    if (!selected || !revisionNote) { toast.error('Catatan revisi wajib diisi.'); return; }
    const res = await api.createSampleVersionRevision(selected.version_id, actor(), revisionNote);
    if (res.success) {
      setShowRevise(false); setRevisionNote(''); fetchAll();
    } else { toast.error(res.error ?? 'Gagal membuat revisi.'); }
  };

  const handleSubmitApproval = async (sv: SampleVersion) => {
    const res = await api.submitSampleVersionApproval(sv.version_id, actor());
    if (res.success) { fetchAll(); } else { toast.error(res.error ?? 'Gagal submit approval.'); }
  };

  const handleApprove = async (sv: SampleVersion) => {
    const note = prompt('Catatan persetujuan (opsional):') ?? '';
    const res = await api.approveSampleVersion(sv.version_id, APPROVER_ID, note);
    if (res.success) { fetchAll(); } else { toast.error(res.error ?? 'Gagal approve.'); }
  };

  const handleConvert = async (sv: SampleVersion) => {
    const orderId = prompt('Masukkan ID Order untuk konversi:');
    if (!orderId) return;
    const res = await api.convertSampleVersionToOrder(sv.version_id, orderId, actor());
    if (res.success) { fetchAll(); } else { toast.error(res.error ?? 'Gagal konversi ke order.'); }
  };

  const handleSaveComponents = async () => {
    if (!selected) return;
    const res = await api.updateSampleVersionComponents(selected.version_id, actor(), editComponents);
    if (res.success) { setShowCompModal(false); fetchAll(); } else { toast.error(res.error ?? 'Gagal menyimpan komponen.'); }
  };

  const handleSaveMaterials = async () => {
    if (!selected) return;
    // auto-calc total_cost
    const mats = editMaterials.map(m => ({ ...m, total_cost: m.estimated_usage * m.unit_cost }));
    const res = await api.updateSampleVersionMaterials(selected.version_id, actor(), mats);
    if (res.success) { setShowMatModal(false); fetchAll(); } else { toast.error(res.error ?? 'Gagal menyimpan material.'); }
  };

  const openHistory = async (sv: SampleVersion) => {
    const res = await api.getSampleVersionHistory(sv.article_id, TENANT_ID);
    if (res.success && res.data) {
      setHistoryVersions(res.data);
      setShowHistory(true);
    }
  };

  const openComponents = (sv: SampleVersion) => {
    setSelected(sv);
    setEditComponents(sv.components?.length
      ? sv.components
      : [{ component_id: generateId(), ...EMPTY_COMPONENT }]);
    setShowCompModal(true);
  };

  const openMaterials = (sv: SampleVersion) => {
    setSelected(sv);
    setEditMaterials(sv.materials?.length ? sv.materials : [{ ...EMPTY_MATERIAL }]);
    setShowMatModal(true);
  };

  // ── total cost helper ──────────────────────────────────────────────

  const totalCost = (mats: MaterialEstimation[]) =>
    mats.reduce((s, m) => s + (m.total_cost || m.estimated_usage * m.unit_cost), 0);

  // ── render ─────────────────────────────────────────────────────────

  return (
    <div>
      {/* Header bar */}
      <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">Manajemen Versi Sample</h2>
          <p className="text-[#6e6e73] text-sm mt-1">Rancangan produk → revisi → konversi ke Mass Order</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary"
        >
          <LucideIcon name="plus" className="w-4 h-4" /> Artikel Baru
        </button>
      </div>

      {/* Main table */}
      <DataTable
        title="Daftar Versi Sample"
        subtitle={`${filtered.length} versi ditemukan`}
        tabs={[
          { id: 'all', label: 'Semua' },
          { id: 'draft', label: 'Draft' },
          { id: 'pending_approval', label: 'Menunggu' },
          { id: 'approved', label: 'Disetujui' },
          { id: 'converted', label: 'Dikonversi' },
        ]}
        activeTab={tab}
        onTabChange={setTab}
        searchValue={search}
        onSearchChange={setSearch}
        columns={[
          { key: 'article_id',    label: 'Artikel' },
          { key: 'article_name',  label: 'Nama' },
          { key: 'client_id',     label: 'Client' },
          { key: 'version_label', label: 'Versi' },
          { key: 'status',        label: 'Status', render: v => <Badge status={String(v)} /> },
          {
            key: 'components', label: 'Komponen',
            render: (_v: unknown, row: SampleVersion) => (
              <button onClick={() => openComponents(row)}
                className="text-[#0066cc] text-xs font-semibold hover:underline">
                {row.components?.length ?? 0} komponen
              </button>
            ),
          },
          {
            key: 'materials', label: 'Estimasi Bahan',
            render: (_v: unknown, row: SampleVersion) => (
              <button onClick={() => openMaterials(row)}
                className="text-[#0066cc] text-xs font-semibold hover:underline">
                Rp {totalCost(row.materials ?? []).toLocaleString('id-ID')}
              </button>
            ),
          },
          {
            key: 'version_id', label: 'Aksi',
            render: (_v: unknown, row: SampleVersion) => (
              <div className="flex gap-2 flex-wrap">
                <button onClick={() => openHistory(row)}
                  title="Riwayat versi"
                  className="btn-pill btn-pill-gray">
                  Riwayat
                </button>
                {row.status === 'draft' && (
                  <>
                    <button onClick={() => { setSelected(row); setShowRevise(true); }}
                      className="btn-pill btn-pill-blue">
                      Revisi
                    </button>
                    <button onClick={() => handleSubmitApproval(row)}
                      className="btn-pill btn-pill-orange">
                      Ajukan
                    </button>
                  </>
                )}
                {row.status === 'pending_approval' && (
                  <button onClick={() => handleApprove(row)}
                    className="btn-pill btn-pill-green">
                    Setujui
                  </button>
                )}
                {row.status === 'approved' && (
                  <button onClick={() => handleConvert(row)}
                    className="btn-pill btn-pill-dark">
                    → Order
                  </button>
                )}
              </div>
            ),
          },
        ]}
        data={filtered}
      />

      <div className="mt-3">
        <button onClick={() => onExportCSV(filtered, 'sample_versions')}
          className="btn-secondary">
          <LucideIcon name="download" className="w-4 h-4" /> Ekspor CSV
        </button>
      </div>

      {/* ── Create modal ──────────────────────────────────────────────── */}
      <Modal isOpen={showCreate} title="Tambah Artikel Baru" onClose={() => setShowCreate(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowCreate(false)}
              className="btn-secondary">
              Batal
            </button>
            <button onClick={handleCreate}
              className="btn-primary">
              Buat v1
            </button>
          </div>
        }>
        <div className="space-y-4">
          {([
            { id: 'article_id',   label: 'Kode Artikel *',  ph: 'e.g. ART-001' },
            { id: 'article_name', label: 'Nama Artikel *',  ph: 'e.g. Kaos Polos Snøhund' },
            { id: 'client_id',    label: 'Client ID *',     ph: 'e.g. snohund' },
          ] as { id: keyof typeof form; label: string; ph: string }[]).map(({ id, label, ph }) => (
            <div key={id}>
              <label className="block text-sm font-medium text-[#1d1d1f] mb-1">{label}</label>
              <input value={form[id]} placeholder={ph} aria-label={label}
                onChange={e => setForm(f => ({ ...f, [id]: e.target.value }))}
                className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Catatan</label>
            <textarea rows={2} value={form.notes} aria-label="Catatan"
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
          </div>
        </div>
      </Modal>

      {/* ── Revise modal ──────────────────────────────────────────────── */}
      <Modal isOpen={showRevise} title={`Buat Revisi Baru dari ${selected?.version_label}`}
        onClose={() => setShowRevise(false)}
        footer={
          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowRevise(false)}
              className="btn-secondary">
              Batal
            </button>
            <button onClick={handleRevise}
              className="btn-primary">
              Buat Revisi
            </button>
          </div>
        }>
        <div>
          <label className="block text-sm font-medium text-[#1d1d1f] mb-1">Catatan Revisi *</label>
          <textarea rows={3} value={revisionNote} placeholder="Jelaskan perubahan desain, pola, atau bahan..." aria-label="Catatan Revisi"
            onChange={e => setRevisionNote(e.target.value)}
            className="w-full border border-[#dedee2] rounded-[10px] px-3 py-2.5 text-[13px] focus:outline-2 focus:outline-[#80baff]" />
          <p className="text-xs text-[#6e6e73] mt-2">
            Komponen & estimasi bahan akan diwarisi dari {selected?.version_label}. Anda bisa edit setelah versi baru dibuat.
          </p>
        </div>
      </Modal>

      {/* ── Version History modal ─────────────────────────────────────── */}
      <Modal isOpen={showHistory} title="Riwayat Versi Artikel" onClose={() => setShowHistory(false)}>
        <div className="space-y-0">
          {historyVersions.map((hv, idx) => (
            <div key={hv.version_id} className="flex gap-4 pb-4 relative">
              {/* timeline line */}
              {idx < historyVersions.length - 1 && (
                <div className="absolute left-[11px] top-7 w-[2px] h-full bg-[#e6e6e9]" />
              )}
              {/* dot */}
              <div className={`w-6 h-6 rounded-full border-2 shrink-0 mt-1 z-10 ${
                hv.status === 'converted' ? 'bg-[#1d1d1f] border-[#1d1d1f]' :
                hv.status === 'approved'  ? 'bg-[#34c759] border-[#34c759]' :
                hv.status === 'pending_approval' ? 'bg-[#ff9500] border-[#ff9500]' :
                'bg-white border-[#0066cc]'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-sm text-[#1d1d1f]">{hv.version_label}</span>
                  <Badge status={hv.status} />
                  {hv.converted_to_order_id && (
                    <span className="text-xs text-[#6e6e73]">→ Order: {hv.converted_to_order_id}</span>
                  )}
                </div>
                <p className="text-xs text-[#6e6e73] mt-0.5">
                  {hv.created_by} · {new Date(hv.created_at).toLocaleDateString('id-ID')}
                </p>
                <p className="text-xs text-[#1d1d1f] mt-1">{hv.notes}</p>
                {/* Revision log */}
                {hv.revision_log?.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {hv.revision_log.map((log, li) => (
                      <li key={li} className="text-[11px] text-[#6e6e73]">
                        {log.action.replace(/_/g, ' ')} — {log.by} · {new Date(log.at).toLocaleTimeString('id-ID')}
                        {log.note ? ` — "${log.note}"` : ''}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
        </div>
      </Modal>

      {/* ── Component Spec modal ──────────────────────────────────────── */}
      <Modal isOpen={showCompModal}
        title={`Spesifikasi Komponen — ${selected?.article_name} ${selected?.version_label}`}
        onClose={() => setShowCompModal(false)}
        footer={
          <div className="flex gap-3 justify-between">
            <button onClick={() => setEditComponents(c => [...c, { component_id: generateId(), ...EMPTY_COMPONENT }])}
              className="btn-secondary !py-2 !px-3">
              + Tambah Baris
            </button>
            <div className="flex gap-2">
              <button onClick={() => setShowCompModal(false)}
                className="btn-secondary">
                Batal
              </button>
              {selected?.status === 'draft' && (
                <button onClick={handleSaveComponents}
                  className="bg-[#0071e3] text-white rounded-[10px] px-4 py-2 font-semibold text-[13px] hover:bg-[#0066cc]">
                  Simpan
                </button>
              )}
            </div>
          </div>
        }>
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-[12px] border-collapse">
            <thead>
              <tr className="bg-[#fafafa]">
                {['Bagian', 'Deskripsi', 'Tipe Bahan', 'Est. (m)', 'Satuan', 'Waktu Std (ms)', 'Rate (IDR)', ''].map(h => (
                  <th key={h} className="px-2 py-2 text-left font-medium text-[#6e6e73] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {editComponents.map((comp, idx) => (
                <tr key={comp.component_id} className="border-b border-[#f0f0f2]">
                  {(['part_name','description','material_type'] as const).map(field => (
                    <td key={field} className="px-1 py-1">
                      <input value={comp[field]} aria-label={field}
                        disabled={selected?.status !== 'draft'}
                        onChange={e => setEditComponents(cs => cs.map((c,i) => i===idx ? {...c,[field]:e.target.value} : c))}
                        className="w-full border border-[#dedee2] rounded-[8px] px-2 py-1 text-[12px] focus:outline-[#80baff] focus:outline-2 disabled:bg-[#f5f5f7]" />
                    </td>
                  ))}
                  {(['estimated_usage_m','sewing_time_std_ms','rate_card_idr'] as const).map(field => (
                    <td key={field} className="px-1 py-1 w-20">
                      <input type="number" value={comp[field]} aria-label={field}
                        disabled={selected?.status !== 'draft'}
                        onChange={e => setEditComponents(cs => cs.map((c,i) => i===idx ? {...c,[field]:parseFloat(e.target.value)||0} : c))}
                        className="w-full border border-[#dedee2] rounded-[8px] px-2 py-1 text-[12px] focus:outline-[#80baff] focus:outline-2 disabled:bg-[#f5f5f7]" />
                    </td>
                  ))}
                  <td className="px-1 py-1">
                    <select value={comp.unit} disabled={selected?.status !== 'draft'} aria-label="Satuan"
                      onChange={e => setEditComponents(cs => cs.map((c,i) => i===idx ? {...c,unit:e.target.value} : c))}
                      className="border border-[#dedee2] rounded-[8px] px-1 py-1 text-[12px] disabled:bg-[#f5f5f7]">
                      {['m','pcs','yard','kg'].map(u => <option key={u}>{u}</option>)}
                    </select>
                  </td>
                  <td className="px-1 py-1">
                    {selected?.status === 'draft' && (
                      <button onClick={() => setEditComponents(cs => cs.filter((_,i) => i!==idx))} aria-label="Hapus komponen"
                        className="text-[#ff3b30] hover:text-[#cc2200] font-bold px-1">×</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {editComponents.length === 0 && (
            <p className="text-center text-[#6e6e73] text-sm py-6">Belum ada komponen. Klik "+ Tambah Baris".</p>
          )}
        </div>
      </Modal>

      {/* ── Material Estimation modal ─────────────────────────────────── */}
      <Modal isOpen={showMatModal}
        title={`Estimasi Bahan — ${selected?.article_name} ${selected?.version_label}`}
        onClose={() => setShowMatModal(false)}
        footer={
          <div className="flex gap-3 justify-between">
            <button onClick={() => setEditMaterials(m => [...m, { ...EMPTY_MATERIAL }])}
              className="btn-secondary !py-2 !px-3">
              + Tambah Baris
            </button>
            <div className="flex gap-2 items-center">
              <span className="text-[13px] font-semibold text-[#1d1d1f]">
                Total: Rp {editMaterials.reduce((s,m) => s + m.estimated_usage * m.unit_cost, 0).toLocaleString('id-ID')}
              </span>
              <button onClick={() => setShowMatModal(false)}
                className="btn-secondary">
                Batal
              </button>
              {selected?.status === 'draft' && (
                <button onClick={handleSaveMaterials}
                  className="bg-[#0071e3] text-white rounded-[10px] px-4 py-2 font-semibold text-[13px] hover:bg-[#0066cc]">
                  Simpan
                </button>
              )}
            </div>
          </div>
        }>
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-[12px] border-collapse">
            <thead>
              <tr className="bg-[#fafafa]">
                {['Kode','Nama Bahan','Est. Qty','Satuan','Harga/Unit (Rp)','Total (Rp)',''].map(h => (
                  <th key={h} className="px-2 py-2 text-left font-medium text-[#6e6e73] border-b border-[#f0f0f2] whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {editMaterials.map((mat, idx) => (
                <tr key={idx} className="border-b border-[#f0f0f2]">
                  {(['material_code','material_name'] as const).map(field => (
                    <td key={field} className="px-1 py-1">
                      <input value={mat[field]} disabled={selected?.status !== 'draft'} aria-label={field}
                        onChange={e => setEditMaterials(ms => ms.map((m,i) => i===idx ? {...m,[field]:e.target.value} : m))}
                        className="w-full border border-[#dedee2] rounded-[8px] px-2 py-1 text-[12px] focus:outline-[#80baff] focus:outline-2 disabled:bg-[#f5f5f7]" />
                    </td>
                  ))}
                  <td className="px-1 py-1 w-20">
                    <input type="number" value={mat.estimated_usage} disabled={selected?.status !== 'draft'} aria-label="Estimasi pemakaian"
                      onChange={e => setEditMaterials(ms => ms.map((m,i) => i===idx ? {...m,estimated_usage:parseFloat(e.target.value)||0} : m))}
                      className="w-full border border-[#dedee2] rounded-[8px] px-2 py-1 text-[12px] disabled:bg-[#f5f5f7]" />
                  </td>
                  <td className="px-1 py-1">
                    <select value={mat.unit} disabled={selected?.status !== 'draft'} aria-label="Satuan"
                      onChange={e => setEditMaterials(ms => ms.map((m,i) => i===idx ? {...m,unit:e.target.value} : m))}
                      className="border border-[#dedee2] rounded-[8px] px-1 py-1 text-[12px] disabled:bg-[#f5f5f7]">
                      {['m','kg','pcs','yard','roll'].map(u => <option key={u}>{u}</option>)}
                    </select>
                  </td>
                  <td className="px-1 py-1 w-28">
                    <input type="number" value={mat.unit_cost} disabled={selected?.status !== 'draft'} aria-label="Harga per unit"
                      onChange={e => setEditMaterials(ms => ms.map((m,i) => i===idx ? {...m,unit_cost:parseFloat(e.target.value)||0} : m))}
                      className="w-full border border-[#dedee2] rounded-[8px] px-2 py-1 text-[12px] disabled:bg-[#f5f5f7]" />
                  </td>
                  <td className="px-2 py-1 font-semibold text-[#1d1d1f] whitespace-nowrap">
                    {(mat.estimated_usage * mat.unit_cost).toLocaleString('id-ID')}
                  </td>
                  <td className="px-1 py-1">
                    {selected?.status === 'draft' && (
                      <button onClick={() => setEditMaterials(ms => ms.filter((_,i) => i!==idx))} aria-label="Hapus material"
                        className="text-[#ff3b30] font-bold px-1">×</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {editMaterials.length === 0 && (
            <p className="text-center text-[#6e6e73] text-sm py-6">Belum ada bahan. Klik "+ Tambah Baris".</p>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default SampleVersionView;

