# Sampling & Spec R&D Frontend

Professional React frontend for time study recording and specification management with Apple Design System, glassmorphism, and optimized tablet performance.

## Quick Start

### Installation

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check
```

The app will be available at `http://localhost:3000`

## Project Structure

```
frontend/sampling-spec-rnd/
├── src/
│   ├── components/          # React components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── SamplingCard.tsx
│   ├── hooks/               # Custom hooks
│   │   ├── usePerformance.ts
│   │   └── useLocalStorage.ts
│   ├── pages/               # Page components
│   │   └── TimeStudyPage.tsx
│   ├── styles/              # Global styles & tokens
│   │   ├── globals.css
│   │   └── design-system.ts
│   ├── types/               # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## Design System

### Apple Design Principles

✨ **Rounded Corners** (8-24px radius)
- Soft, modern aesthetic
- Applied via Tailwind classes: `rounded-lg`, `rounded-xl`, `rounded-2xl`
- See `src/styles/design-system.ts`

✨ **Clear Contrast**
- High readability with proper color hierarchy
- Primary: #8b5cf6 (Purple)
- Secondary: #6b7280 (Gray)
- Error: #ef4444 (Red)
- Success: #10b981 (Green)

✨ **Glassmorphism Effect**
- `backdrop-filter: blur(8-12px)`
- Semi-transparent white/dark backgrounds
- Border: `1px solid rgba(255,255,255,0.2)`
- Used in Card, Button, and Input components

### Tablet Performance

🚀 **Touch Optimization**
- Minimum touch target: 48px (factory gloved hands)
- Debounced touch events (16ms for 60fps)
- No layout shift on interaction

📊 **Performance Monitoring**
- FPS tracking
- Render time measurement
- Lag detection with warnings

🔄 **Batch Updates**
- Microtask queue batching
- Reduced re-renders
- Smooth animations

## Components

### Button
```tsx
<Button 
  variant="primary|secondary|danger|outline"
  size="sm|md|lg"
  isLoading={false}
  onClick={handleClick}
>
  Click Me
</Button>
```

### Card
```tsx
<Card variant="default|glass|outlined" className="p-6">
  Content here
</Card>
```

### Input
```tsx
<Input
  label="Cycle Time"
  type="number"
  error={error}
  helperText="Enter in milliseconds"
  onChange={handleChange}
/>
```

### SamplingCard
```tsx
<SamplingCard
  study={timeStudyObject}
  onStart={handleStart}
  onPause={handlePause}
  onResume={handleResume}
  onComplete={handleComplete}
/>
```

## Hooks

### usePerformance
```tsx
const { 
  metrics,           // { renderTime, fps, isLagging }
  batchUpdate,       // (updates: (() => void)[]) => void
  throttle,          // (callback, delay) => (...args) => void
  debounce,          // (callback, delay) => (...args) => void
  debounceTouchEvent, // (callback) => (e: TouchEvent) => void
  scheduleIdleTask   // (callback, timeout) => void
} = usePerformance();
```

### useLocalStorage
```tsx
const [value, setValue, removeValue] = useLocalStorage(
  'key',
  initialValue,
  { 
    ttl: 24 * 60 * 60 * 1000,  // 24 hours
    useIndexedDB: true          // Use IndexedDB for large data
  }
);
```

## Styling

### Tailwind CSS Configuration
- Custom colors (primary, accent, glass)
- Spacing scale (xs-3xl)
- Border radius variants (4-24px)
- Glassmorphism utilities
- Touch target helpers

### CSS Variables
```css
--color-primary: 139, 92, 246
--color-glass-alpha: 0.9
--touch-target-min: 48px
```

### Glass Effect Classes
```tsx
<div className="glass">           {/* Full opacity + blur */}
<div className="glass-sm">        {/* Medium opacity + blur */}
<div className="glass-md">        {/* High opacity + blur */}
```

## API Integration

### Backend Connection
- Proxy configured in `vite.config.ts`
- Base URL: `http://localhost:8000/api`
- Timeout: 30 seconds
- Error handling with user feedback

### Example API Call
```tsx
const response = await fetch('/api/sampling-spec-rnd/studies/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tenant_id: 'default',
    process_id: 'proc_001',
    process_name: 'Assembly Line A',
    operator_id: 'op_001',
    target_sample_size: 30,
  })
});
```

## Offline Support

- IndexedDB caching for all data
- Automatic sync when online
- TTL-based cache invalidation
- Fallback to localStorage for small datasets

## Accessibility

♿ **WCAG Compliance**
- Focus visible states (2px outline)
- Semantic HTML (button, input, select)
- ARIA labels where needed
- Keyboard navigation support
- Touch-friendly hit areas (48px min)

🔊 **Screen Readers**
- Proper heading hierarchy
- Label associations
- Status announcements
- Error messages linked to inputs

## Browser Support

- Chrome 90+
- Safari 14+
- Firefox 88+
- Edge 90+
- iOS Safari 14+
- Android Chrome 90+

## Performance Metrics

📈 **Target Metrics**
- First Contentful Paint: < 1s
- Time to Interactive: < 2s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- FPS: 60 (debounce at 16ms)

## Development Tips

### Component Development
1. Create component in `src/components/`
2. Export from `src/components/index.ts`
3. Use TypeScript for props
4. Wrap with `React.memo()` for performance
5. Use Tailwind for styling

### Performance Optimization
```tsx
// Use memoization
const MyComponent = React.memo(({ prop }) => {
  const memoValue = useMemo(() => compute(prop), [prop]);
  return <div>{memoValue}</div>;
});

// Use throttle for frequent events
const { throttle } = usePerformance();
const handleScroll = throttle(() => {
  // Handle scroll
}, 100);

// Use batch updates
const { batchUpdate } = usePerformance();
batchUpdate([
  () => setState1(val1),
  () => setState2(val2),
]);
```

### Debugging
```tsx
// Check performance metrics
const { metrics } = usePerformance();
console.log(`FPS: ${metrics.fps}, Lagging: ${metrics.isLagging}`);

// Monitor cache operations
const [value, setValue] = useLocalStorage('key', initial);
```

## Build & Deploy

### Production Build
```bash
npm run build
# Output: dist/

npm run preview
# Preview built app locally
```

### Deployment Checklist
- [ ] Run `npm run type-check` (no errors)
- [ ] Run `npm run build` (no warnings)
- [ ] Test on tablet/mobile device
- [ ] Verify offline caching works
- [ ] Check backend API endpoints
- [ ] Validate responsive layout

## Troubleshooting

### Layout Shift on Tablet
- Check touch target sizes (should be 48px+)
- Use `will-change: transform` for animations
- Debounce touch events

### Performance Issues
- Profile with DevTools Performance tab
- Check `metrics.isLagging` in console
- Reduce animation complexity
- Enable code splitting

### API Connection Issues
- Verify backend is running on port 8000
- Check CORS headers from backend
- Inspect Network tab for 404/500 errors
- Clear IndexedDB if cache is stale

## Support

See documentation files:
- `DESIGN_SYSTEM_REFERENCE.md` - Complete design tokens
- `IMPLEMENTATION_GUIDE.md` - Step-by-step component usage
- `CODE_EXAMPLES.md` - Real-world code snippets
- `STARTUP_CHECKLIST.md` - Getting started guide

## License

Proprietary - Alkademi
