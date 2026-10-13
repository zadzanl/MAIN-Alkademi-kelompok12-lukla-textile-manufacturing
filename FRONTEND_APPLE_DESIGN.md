# Frontend Sampling & Spec R&D - Apple Design System

**Hanya Frontend React + TypeScript + Tailwind CSS dengan Apple Design**

---

## 📁 Lokasi Frontend

```
frontend/sampling-spec-rnd/
├── src/
│   ├── components/          (Komponen React)
│   │   ├── Button.tsx       (Apple-styled button, 48px touch target)
│   │   ├── Card.tsx         (Glassmorphism card effect)
│   │   ├── Input.tsx        (Form input)
│   │   └── SamplingCard.tsx (Time study display card)
│   │
│   ├── hooks/               (Custom React hooks)
│   │   ├── usePerformance.ts (FPS monitoring, 60fps optimization)
│   │   └── useLocalStorage.ts (Local caching)
│   │
│   ├── pages/               (Page components)
│   │   └── TimeStudyPage.tsx (Main UI - Time Study interface)
│   │
│   ├── styles/              (Design System)
│   │   ├── globals.css      (Apple Design + Glassmorphism)
│   │   └── design-system.ts (Design tokens - warna, spacing, radius)
│   │
│   ├── types/               (TypeScript definitions)
│   │   └── index.ts         (TimeStudy, SpecVersion types)
│   │
│   ├── App.tsx
│   └── main.tsx
│
├── index.html               (Entry HTML)
├── package.json             (Dependencies: React, Tailwind, Vite)
├── tsconfig.json            (TypeScript config)
├── vite.config.ts           (Vite build config)
├── tailwind.config.js       (Tailwind design tokens)
└── postcss.config.js        (CSS processing)
```

---

## 🎨 Apple Design Implementation

### Rounded Corners (8-24px)
```tsx
<div className="rounded-lg">      {/* 12px */}
<div className="rounded-xl">      {/* 16px */}
<div className="rounded-2xl">     {/* 20px */}
```

### Clear Contrast (WCAG AA+)
```tsx
<p className="text-gray-900">     {/* Dark text */}
<span className="text-primary">   {/* Purple accent */}
```

### Glassmorphism Effect (Blur + Transparency)
```tsx
<div className="glass">           {/* backdrop-filter: blur(8px) */}
  {/* Semi-transparent dengan blur effect */}
</div>
```

### Tablet Touch Targets (48px minimum)
```tsx
<button className="touch-target">  {/* min-height: 48px, min-width: 48px */}
  Click Me
</button>
```

---

## 🚀 Cara Pakai

### 1. Install Dependencies
```bash
cd frontend/sampling-spec-rnd
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Buka: **http://localhost:3000**

### 3. Build Production
```bash
npm run build
```

Output: `dist/` folder

---

## 📋 Component Library

### Button
```tsx
<Button 
  variant="primary"      // atau: secondary, danger, outline
  size="md"              // atau: sm, lg
  isLoading={false}
>
  Click
</Button>
```

### Card
```tsx
<Card 
  variant="glass"        // atau: default, outlined
>
  Content here
</Card>
```

### Input
```tsx
<Input
  label="Cycle Time"
  type="number"
  error="Invalid"
  helperText="Enter in ms"
/>
```

### SamplingCard
```tsx
<SamplingCard
  study={timeStudyObject}
  onStart={() => {}}
  onComplete={() => {}}
/>
```

---

## 🎯 Features

✅ **Apple Design System**
- Rounded corners (8-24px)
- Clear contrast (AA+ WCAG)
- Glassmorphism (blur effect)

✅ **Tablet Optimized**
- Touch targets 48px+ 
- 60 FPS performance
- No lag

✅ **Time Study UI**
- Create study
- Add samples
- Progress tracking
- Statistics display

✅ **Spec Version UI** (ready untuk ditambah)
- Version management
- Change tracking
- Drift monitoring

---

## 🔧 TypeScript Types

```typescript
interface TimeStudy {
  study_id: string
  process_name: string
  status: 'draft' | 'in_progress' | 'completed'
  total_cycles: number
  mean_cycle_time: number
  // ... lebih banyak fields
}

interface SpecVersion {
  version_id: string
  spec_name: string
  version_number: string
  status: 'draft' | 'review' | 'approved' | 'active'
  // ... lebih banyak fields
}
```

---

## 📊 Folder Structure Lebih Detail

```
src/
├── components/
│   ├── Button.tsx           (Touch-friendly button)
│   ├── Card.tsx             (Glassmorphic container)
│   ├── Input.tsx            (Form input field)
│   ├── SamplingCard.tsx     (Time study card)
│   └── index.ts             (Exports)
│
├── hooks/
│   ├── usePerformance.ts    (FPS monitoring, debounce)
│   ├── useLocalStorage.ts   (Local/IndexedDB caching)
│   └── index.ts             (Exports)
│
├── pages/
│   ├── TimeStudyPage.tsx    (Main page - time study UI)
│   └── index.ts             (Exports)
│
├── styles/
│   ├── globals.css          (Apple Design + Glassmorphism)
│   ├── design-system.ts     (Colors, spacing, radius tokens)
│   └── index.ts
│
├── types/
│   └── index.ts             (TimeStudy, SpecVersion, etc)
│
├── App.tsx
└── main.tsx
```

---

## 🎨 Design Tokens

```typescript
colors: {
  primary: '#8b5cf6'           // Purple
  accent: { blue, green, orange, red }
  neutral: { 50-900 }          // Gray scale
}

spacing: { xs, sm, md, lg, xl, 2xl, 3xl }
borderRadius: { xs(4px) - 3xl(24px) }
fontSize: { xs - 3xl }
shadows: { xs - glass }
backdropBlur: { xs(2px) - 2xl(24px) }
touchTarget: { min: 48px }
```

---

## ✨ Highlight Features

### Performance
- React.memo on all components
- useMemo for expensive calculations
- Debounced touch events (16ms = 60fps)
- FPS monitoring built-in

### Design
- Modern glassmorphism effect
- Rounded corners everywhere (Apple style)
- Clear text/background contrast
- Smooth animations

### UX
- 48px+ touch targets (factory gloves friendly)
- No layout shift on interaction
- Responsive design (mobile → tablet → desktop)
- Offline caching ready

---

## 🚀 Next Steps

1. **Run**: `npm install && npm run dev`
2. **Test**: Open http://localhost:3000
3. **See**: Time Study UI dengan Apple Design
4. **Modify**: Edit `src/pages/TimeStudyPage.tsx` untuk customize
5. **Add**: Spec Version page (`src/pages/SpecVersionPage.tsx`) nanti

---

## 📝 Notes

- Backend **tidak** termasuk (hanya frontend UI)
- Data simpan di **localStorage** (cukup untuk demo)
- Bisa nanti integrate dengan backend API
- Semua components sudah **production-ready**
- Design system **fully customizable** via `design-system.ts`

---

**Status**: ✅ Frontend siap pakai dengan Apple Design System
