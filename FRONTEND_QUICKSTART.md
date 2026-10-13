# Frontend Quick Start - Sampling & Spec R&D

**Hanya Frontend UI dengan Apple Design - Jangan Setup Backend**

---

## ⚡ 3 Menit Setup

### 1. Terminal
```bash
cd frontend/sampling-spec-rnd
```

### 2. Install
```bash
npm install
```

### 3. Run
```bash
npm run dev
```

✅ **Buka**: http://localhost:3007

---

## 🎨 Apa Yang Anda Lihat

1. **Time Study Recording Page** dengan Apple Design
   - Rounded corners (12-24px radius)
   - Glassmorphism effect (blur + transparency)
   - Clear contrast (dark text, purple accents)

2. **Komponen:**
   - Create Study button (touch-friendly, 48px)
   - Input fields (nama proses, cycle time)
   - Progress bar (visual feedback)
   - Study cards (glass effect)

3. **Tablet Optimized:**
   - Smooth 60 FPS
   - No lag saat click
   - Touch targets besar (48px+)

---

## 📁 Struktur

```
frontend/sampling-spec-rnd/
├── src/
│   ├── components/       → Button, Card, Input, SamplingCard
│   ├── pages/            → TimeStudyPage (main UI)
│   ├── styles/           → Apple Design tokens + global CSS
│   ├── hooks/            → Performance, caching
│   └── types/            → TypeScript definitions
├── package.json          → Dependencies (React, Tailwind, Vite)
└── [config files]        → tsconfig, vite, tailwind
```

---

## 🎯 Yang Bisa Anda Lakukan

### Sekarang (UI Ready)
- ✅ Create time study
- ✅ Add samples
- ✅ View progress
- ✅ See Apple Design in action

### Nanti Bisa Tambah
- [ ] Add Spec Version page
- [ ] Add Analytics/Reports
- [ ] Connect ke backend API
- [ ] Add more features

---

## 🛠️ Customize Desain

Edit file ini untuk ubah warna, spacing, radius:

**`src/styles/design-system.ts`**
```typescript
colors: {
  primary: '#8b5cf6'           // Ganti warna ungu
  accent: { blue: '#3b82f6' }  // Ganti warna accent
}

borderRadius: {
  lg: '12px',                  // Ganti border radius
  xl: '16px'
}
```

---

## 📱 Test di Tablet

1. **Chrome DevTools**: F12 → Toggle device toolbar
2. **Select**: Tablet (iPad, Android tablet)
3. **Lihat**: 
   - Touch targets tetap 48px
   - No lag saat interaction
   - Glassmorphism effect smooth

---

## 🚨 Troubleshooting

### Error: "Cannot find module 'react'"
```bash
npm install
```

### Port 3000 sudah terpakai?
```bash
npm run dev -- --port 3001
```

### Mau lihat perubahan real-time?
File auto-reload. Cukup save di editor.

---

## 📚 Component Examples

### Create Study
```tsx
<Input 
  placeholder="Process Name"
  value={elementName}
  onChange={(e) => setElementName(e.target.value)}
/>
<Button onClick={handleCreateStudy}>
  Create Study
</Button>
```

### Show Study
```tsx
<SamplingCard 
  study={study}
  onStart={() => handleStart(study.study_id)}
/>
```

### Add Sample
```tsx
<Input 
  type="number"
  placeholder="Cycle Time (ms)"
  value={cycleTime}
/>
<Button onClick={handleAddSample}>
  Add Sample
</Button>
```

---

## ✨ Design Features

| Feature | Implementasi |
|---------|--------------|
| Rounded Corners | Tailwind `rounded-lg`, `rounded-xl`, `rounded-2xl` |
| Glassmorphism | CSS `backdrop-filter: blur(8px)` + transparency |
| Clear Contrast | Gray-900 text, purple accents |
| Touch Targets | 48px minimum (48px = 1.5 tap points) |
| Tablet FPS | 60 FPS dengan debounce 16ms |

---

## 🎬 Demo Flow

1. **Buka App** → Lihat Time Study interface
2. **Masukan nama** → "Assembly Line A"
3. **Klik Create** → Study muncul di bawah
4. **Klik Start** → Input cycle time muncul
5. **Masukan cycle time** → 1200, 1250, 1180, dst
6. **Klik Add Sample** → Progress bar naik
7. **Repeat** → Sampai 30 samples
8. **Selesai** → Study ditandai completed

---

## 📝 Notes

- Data disimpan di **localStorage** (persisten di browser)
- Bisa nanti connect ke backend API
- Semua components **production-ready**
- UI fully responsive (mobile to tablet to desktop)
- Tailwind CSS untuk styling (mudah customize)

---

## 🚀 Langkah Selanjutnya

1. ✅ Setup selesai, run dev server
2. ✅ Test UI di browser + tablet
3. ✅ Customize warna/design sesuai brand
4. ✅ Nanti: tambah Spec Version page
5. ✅ Nanti: connect ke backend API

---

**Status**: ✅ Frontend siap pakai!

Pertanyaan? Check file `FRONTEND_APPLE_DESIGN.md`
