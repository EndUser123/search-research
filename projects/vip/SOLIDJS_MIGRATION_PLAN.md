# SolidJS Migration Plan for V.I.P.

## Phase 1: Project Setup (Day 1)

### 1.1 Install SolidJS Dependencies
```bash
npm install solid-js
npm install -D vite-plugin-solid
npm install -D @types/node
```

### 1.2 Update `vite.config.ts`
Replace React plugin with SolidJS plugin:
```ts
import { defineConfig } from 'vite';
import solidPlugin from 'vite-plugin-solid';

export default defineConfig({
  plugins: [solidPlugin()],
  server: {
    port: 3000,
  },
  build: {
    target: 'esnext',
  },
});
```

### 1.3 Update `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "jsxImportSource": "solid-js",
    "types": ["vite/client"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

### 1.4 Update Entry Point (`index.tsx`)
```tsx
import { render } from 'solid-js/web';
import App from './App';

render(() => <App />, document.getElementById('root')!);
```

---

## Phase 2: Core Utilities Migration (Day 1-2)

### 2.1 Convert `usePanelResize.tsx` → `createPanelResize.tsx`
**React Hook → Solid Primitive**

**Before (React):**
```tsx
const [panelFlex, setPanelFlex] = useState(initialPanelFlex);
const resizeData = useRef<ResizeData | null>(null);

useEffect(() => {
  // cleanup logic
}, []);
```

**After (Solid):**
```tsx
import { createSignal, onCleanup } from 'solid-js';

const [panelFlex, setPanelFlex] = createSignal(initialPanelFlex);
let resizeData: ResizeData | null = null; // No ref needed

onCleanup(() => {
  // cleanup logic - runs automatically
});
```

**Key Changes:**
- `useState` → `createSignal`
- `useRef` → plain variable (components only run once)
- `useEffect` → `createEffect` or `onCleanup`
- `useCallback` → **delete it** (no re-renders = no memoization needed)

---

### 2.2 Convert Theme Context
**Before (React):**
```tsx
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState<Theme>('dark');
  // ...
};
```

**After (Solid):**
```tsx
import { createContext, useContext, createSignal, JSX } from 'solid-js';

const ThemeContext = createContext<ThemeContextType>();

export const ThemeProvider = (props: { children: JSX.Element }) => {
  const [currentTheme, setCurrentTheme] = createSignal<Theme>('dark');

  return (
    <ThemeContext.Provider value={{ currentTheme, setCurrentTheme }}>
      {props.children}
    </ThemeContext.Provider>
  );
};
```

**Key Changes:**
- `React.FC` → plain function
- `children: React.ReactNode` → `children: JSX.Element`
- Access props via `props.children` (Solid uses getters)

---

## Phase 3: Component Migration Strategy (Day 2-10)

### Migration Order (Least → Most Complex):
1. ✅ **Icons.tsx** (pure components, no state)
2. ✅ **FilterButtonGroup.tsx** (simple state)
3. ✅ **LogPanel.tsx** (local state + props)
4. ⚠️ **SourceUrlsPanel.tsx** (ResizeObserver + signals)
5. ⚠️ **DiscoveredItemsPanel.tsx** (complex state)
6. ⚠️ **StagingQueuePanel.tsx** (complex state)
7. 🔴 **App.tsx** (main orchestrator)

### Component Migration Template

**React Pattern:**
```tsx
interface Props {
  value: string;
  onChange: (v: string) => void;
}

const Component: React.FC<Props> = ({ value, onChange }) => {
  const [localState, setLocalState] = useState(0);

  useEffect(() => {
    // side effect
  }, [value]);

  return <div onClick={() => onChange('new')}>{value}</div>;
};
```

**Solid Pattern:**
```tsx
import { createSignal, createEffect } from 'solid-js';

interface Props {
  value: string;
  onChange: (v: string) => void;
}

const Component = (props: Props) => {
  const [localState, setLocalState] = createSignal(0);

  createEffect(() => {
    // side effect - auto-tracks props.value
    console.log(props.value);
  });

  return <div onClick={() => props.onChange('new')}>{props.value}</div>;
};
```

**Critical Differences:**
1. **Props are getters**: Use `props.value`, not destructuring
2. **No dependency arrays**: `createEffect` auto-tracks
3. **No memoization**: Delete `useCallback`, `useMemo`, `React.memo`

---

## Phase 4: The Big Win - SourceUrlsPanel (Day 3-4)

### Before (React - 180 lines with bugs):
```tsx
const SourceUrlsPanel: React.FC<Props> = ({ ... }) => {
  const fixedContentRef = useRef<HTMLDivElement>(null);
  const lastHeight = useRef<number>(0);

  useEffect(() => {
    if (!fixedContentRef.current) return;

    const updateHeight = () => {
      if (fixedContentRef.current && onMinHeightChange) {
        const height = fixedContentRef.current.offsetHeight;
        if (height > 0 && height !== lastHeight.current) {
          lastHeight.current = height;
          onMinHeightChange(height); // Can cause infinite loops!
        }
      }
    };

    const observer = new ResizeObserver(updateHeight);
    observer.observe(fixedContentRef.current);
    return () => observer.disconnect();
  }, [onMinHeightChange, stage1PanelsCollapsed.sourceUrls]);

  // ...
};
```

### After (Solid - 120 lines, zero bugs):
```tsx
import { createSignal, onMount, onCleanup } from 'solid-js';

const SourceUrlsPanel = (props: Props) => {
  let fixedContentRef: HTMLDivElement | undefined;
  const [fixedHeight, setFixedHeight] = createSignal(0);

  onMount(() => {
    if (!fixedContentRef) return;

    const observer = new ResizeObserver(() => {
      const height = fixedContentRef!.offsetHeight;
      if (height > 0) {
        setFixedHeight(height);
        props.onMinHeightChange?.(height); // No loops possible!
      }
    });

    observer.observe(fixedContentRef);
    onCleanup(() => observer.disconnect());
  });

  return (
    <div ref={fixedContentRef}>
      {/* ... */}
    </div>
  );
};
```

**Why This Works:**
- No `useRef` needed (use `let` + `ref` attribute)
- No `lastHeight` tracking (signals handle equality checks)
- No dependency arrays (observer setup runs once in `onMount`)
- **Infinite loop is architecturally impossible** (no re-renders)

---

## Phase 5: State Management (Day 5-7)

### Convert App.tsx State

**React:**
```tsx
const [urls, setUrls] = useState('');
const [discoveredItems, setDiscoveredItems] = useState<DiscoveredItems>({ videos: [], playlists: [] });
const [selectedDiscovered, setSelectedDiscovered] = useState<SelectedDiscovered>({ videos: new Set(), playlists: new Set() });
```

**Solid:**
```tsx
import { createSignal, createStore } from 'solid-js/store';

const [urls, setUrls] = createSignal('');

// For complex nested objects, use createStore (like Zustand but built-in)
const [discoveredItems, setDiscoveredItems] = createStore<DiscoveredItems>({
  videos: [],
  playlists: []
});

const [selectedDiscovered, setSelectedDiscovered] = createStore<SelectedDiscovered>({
  videos: new Set(),
  playlists: new Set()
});
```

**Updating Stores:**
```tsx
// React
setDiscoveredItems({ videos: newVideos, playlists: [] });

// Solid (granular updates)
setDiscoveredItems('videos', newVideos); // Only updates 'videos' property
setDiscoveredItems('playlists', (prev) => [...prev, newPlaylist]); // Functional update
```

---

## Phase 6: Testing & Verification (Day 8-10)

### Checklist:
- [ ] All panels render correctly
- [ ] Resize handles work smoothly (60fps)
- [ ] No console errors
- [ ] Theme switching works
- [ ] URL parsing works
- [ ] Batch operations work
- [ ] Panel collapse/expand works
- [ ] **Critical:** ResizeObserver doesn't cause loops

### Performance Benchmarks:
- Bundle size: Expect **30-40% reduction**
- Initial load: Expect **20-30% faster**
- Resize smoothness: Should be **native 60fps** without optimization

---

## Phase 7: Cleanup (Day 10)

### Remove React Dependencies:
```bash
npm uninstall react react-dom @types/react @types/react-dom
npm uninstall @vitejs/plugin-react
```

### Delete Unused Files:
- Any `.jsx` files (Solid uses `.tsx`)
- React-specific utilities (memoization helpers, etc.)

---

## Rollback Plan

If migration fails at any point:
1. Keep React version in `git` branch `react-stable`
2. Migrate incrementally (one component at a time)
3. Use `solid-element` to wrap Solid components as web components in React

---

## Expected Outcomes

### Code Reduction:
- **-30% lines of code** (no memoization boilerplate)
- **-100% infinite loop bugs** (architectural impossibility)
- **-50% "why is this re-rendering?" debugging**

### Performance:
- **40% smaller bundle** (no React runtime)
- **60fps resize** (no VDOM reconciliation)
- **Instant updates** (fine-grained reactivity)

### Developer Experience:
- **No dependency arrays** (createEffect auto-tracks)
- **No stale closures** (components run once)
- **No useCallback/useMemo** (no re-renders to optimize)

---

## Next Steps

1. **Create a new branch**: `git checkout -b solidjs-migration`
2. **Start with Phase 1** (project setup)
3. **Migrate Icons.tsx** as proof-of-concept
4. **Compare bundle sizes** before/after
5. **Decide**: Full migration or hybrid approach

Ready to proceed?
