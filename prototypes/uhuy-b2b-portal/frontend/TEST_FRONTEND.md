# TEST FRONTEND — Portal Klien Eksternal UHUY B2B

Manual test guide for the external portal (port 3010, backend 8010).

## Prerequisites
- Backend running on port 8010 (`uvicorn src.main:app --reload --port 8010`).
- Frontend running on port 3010 (`npm run dev`).
- Demo credentials: `klien.a@uhuy.local` / `Klien#12345` (Client A), `klien.b@uhuy.local` / `Klien#12345` (Client B).

## BAGIAN 1 — External marker
1.1 Login page shows the top ribbon **UHUY B2B · Portal Klien Eksternal** and the **PORTAL EKSTERNAL** badge.
1.2 After login, the sidebar brand reads **UHUY B2B / Portal Klien · Eksternal** and a badge sits above the page title.
1.3 Accent colour is indigo (not the internal app's blue).

## BAGIAN 2 — Login
2.1 Login as Client A (email) → Dashboard appears; header caption shows "Backend terhubung".
2.2 Wrong password → red error "Identitas atau password salah."
2.3 Empty identifier → error "Isi email atau nomor HP Anda."
2.4 Login as Client B (phone `081100000002`) works.

## BAGIAN 3 — Dashboard
3.1 KPI cards: Order Aktif (2), Order Selesai (1), Pengajuan Menunggu, Lot Stok Titipan (2) for Client A.
3.2 Recent orders table lists only A's orders.

## BAGIAN 4 — Track orders & isolation
4.1 "Lacak Pesanan" lists A's orders; tab filters by status work.
4.2 Click **Detail** → modal shows scheme, target, progress bar, and phase timeline.
4.3 Log in as Client B → the list shows only B's orders (different ids).

## BAGIAN 5 — Submit requests
5.1 "Ajukan Order" → fill article/qty/scheme/target → submit → success toast.
5.2 "Pengajuan Saya" now lists the new request with status **Diajukan**.
5.3 "Ajukan Sample" → submit → appears with jenis **Sample**.
5.4 Empty article or qty ≤ 0 → error toast, no request created.
5.5 Switch to Client B → the request does NOT appear (isolation).

## BAGIAN 6 — Consigned stock
6.1 "Bahan Saya" lists A's lots (Cotton Combed 30s, Benang Polyester).
6.2 Client B sees different lots (Kain Drill, Kain Oxford).

## BAGIAN 7 — Registration & approval
7.1 Login page → Registrasi → fill form + consent → "Pengajuan diterima…" success.
7.2 Login with the new account before approval → blocked (pending).
7.3 (Admin) approve via API `POST /api/portal/auth/admin/clients/{id}/approve` with an admin token → login now works.

## BAGIAN 8 — Settings
8.1 "Pengaturan" shows company/contact/email/client id.
8.2 Change password with wrong current → error; correct → success + forced re-login.
8.3 "Keluar dari Portal" returns to the login page.

## BAGIAN 9 — Design & UI
9.1 Dark mode toggle works across all pages.
9.2 Buttons/inputs have ≥48px touch targets; rounded corners; focus rings.
9.3 No console errors; no 404/500 on the client-scoped calls (cross-client fetch intentionally returns 404 and is not triggered by the UI).

## Quick checklist
- [ ] Marker visible (login + shell)
- [ ] Login A/B works; pending blocked
- [ ] Orders scoped per client
- [ ] Order + sample requests submit and appear only for the owner
- [ ] Stock scoped per client
- [ ] Password change revokes session
- [ ] `tsc`, `eslint`, `npm test`, `vite build` all clean
