# Quest Core Design Tokens

> **CSS Custom Properties and Tailwind Configuration for Quest Premium Design System**

## 🎨 **CSS Custom Properties**

### **Color Tokens**
```css
:root {
  /* Primary Brand Colors */
  --quest-primary: #00D4B8;        /* Aurora Fade (Teal) */
  --quest-secondary: #4F46E5;      /* Electric Violet (Blue) */
  --quest-accent: #8B5CF6;         /* Purple */

  /* Background Colors */
  --quest-bg-primary: #0A0E1A;     /* Deep Charcoal */
  --quest-bg-secondary: #1A1D29;   /* Card Background */
  --quest-bg-tertiary: #2A2D3A;    /* Elevated Surface */

  /* Neutral Colors */
  --quest-neutral-100: #F8FAFC;    /* Pure White */
  --quest-neutral-200: #E2E8F0;    /* Mist Grey */
  --quest-neutral-300: #94A3B8;    /* Medium Grey */
  --quest-neutral-400: #64748B;    /* Text Secondary */
  --quest-neutral-500: #475569;    /* Text Muted */

  /* Semantic Colors */
  --quest-success: #10B981;        /* Success Green */
  --quest-warning: #F59E0B;        /* Warning Amber */
  --quest-error: #EF4444;          /* Error Red */
  --quest-info: #3B82F6;           /* Info Blue */

  /* Gradient Tokens */
  --quest-gradient-primary: linear-gradient(135deg, #00D4B8 0%, #4F46E5 100%);
  --quest-gradient-secondary: linear-gradient(135deg, #4F46E5 0%, #8B5CF6 100%);
  --quest-gradient-accent: linear-gradient(135deg, #00D4B8 0%, #8B5CF6 100%);
  --quest-sphere-gradient: radial-gradient(circle at 30% 30%, #00D4B8, #4F46E5, #8B5CF6);
  --quest-sphere-glow: 0 0 20px rgba(0, 212, 184, 0.3);

  /* Chart Colors */
  --quest-chart-1: #00D4B8;        /* Primary teal */
  --quest-chart-2: #4F46E5;        /* Blue */
  --quest-chart-3: #8B5CF6;        /* Purple */
  --quest-chart-4: #EC4899;        /* Pink */
  --quest-chart-5: #F59E0B;        /* Amber */
  --quest-chart-6: #10B981;        /* Green */
}
```

### **Typography Tokens**
```css
:root {
  /* Font Families */
  --quest-font-primary: "GT Walsheim", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --quest-font-mono: "SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace;

  /* Font Sizes */
  --quest-text-display: 4rem;      /* 64px - Large display text */
  --quest-text-h1: 3rem;           /* 48px - Hero headlines */
  --quest-text-h2: 2.25rem;        /* 36px - Section headers */
  --quest-text-h3: 1.875rem;       /* 30px - Subsection headers */
  --quest-text-h4: 1.5rem;         /* 24px - Card titles */
  --quest-text-h5: 1.25rem;        /* 20px - Component headers */
  --quest-text-h6: 1.125rem;       /* 18px - Small headers */
  --quest-text-body: 1rem;         /* 16px - Primary body text */
  --quest-text-body-sm: 0.875rem;  /* 14px - Secondary text */
  --quest-text-caption: 0.75rem;   /* 12px - Captions, labels */

  /* Font Weights */
  --quest-font-normal: 400;
  --quest-font-medium: 500;
  --quest-font-semibold: 600;
  --quest-font-bold: 700;

  /* Line Heights */
  --quest-leading-tight: 1.25;
  --quest-leading-normal: 1.5;
  --quest-leading-relaxed: 1.625;
}
```

### **Spacing Tokens**
```css
:root {
  /* Spacing Scale (8px base) */
  --quest-space-1: 0.25rem;        /* 4px */
  --quest-space-2: 0.5rem;         /* 8px */
  --quest-space-3: 0.75rem;        /* 12px */
  --quest-space-4: 1rem;           /* 16px */
  --quest-space-5: 1.25rem;        /* 20px */
  --quest-space-6: 1.5rem;         /* 24px */
  --quest-space-8: 2rem;           /* 32px */
  --quest-space-10: 2.5rem;        /* 40px */
  --quest-space-12: 3rem;          /* 48px */
  --quest-space-16: 4rem;          /* 64px */
  --quest-space-20: 5rem;          /* 80px */
}
```

### **Border Radius Tokens**
```css
:root {
  /* Border Radius */
  --quest-radius-sm: 0.25rem;      /* 4px */
  --quest-radius-md: 0.5rem;       /* 8px */
  --quest-radius-lg: 0.75rem;      /* 12px */
  --quest-radius-xl: 1rem;         /* 16px */
  --quest-radius-full: 50%;
}
```

### **Shadow Tokens**
```css
:root {
  /* Shadows */
  --quest-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --quest-shadow-md: 0 4px 16px rgba(0, 0, 0, 0.1);
  --quest-shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.2);
  --quest-shadow-glow: 0 0 20px rgba(0, 212, 184, 0.3);
  --quest-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.2);
}
```

### **Animation Tokens**
```css
:root {
  /* Transition Durations */
  --quest-duration-fast: 0.15s;
  --quest-duration-normal: 0.2s;
  --quest-duration-slow: 0.3s;
  --quest-duration-slower: 0.5s;

  /* Easing Functions */
  --quest-ease-out: cubic-bezier(0, 0, 0.2, 1);
  --quest-ease-in: cubic-bezier(0.4, 0, 1, 1);
  --quest-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}
```

## ⚙️ **Tailwind CSS Configuration**

### **Complete tailwind.config.js**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        quest: {
          // Primary Brand Colors
          primary: '#00D4B8',      // Aurora Fade (Teal)
          secondary: '#4F46E5',    // Electric Violet (Blue)
          accent: '#8B5CF6',       // Purple
          
          // Background Colors
          'bg-primary': '#0A0E1A',    // Deep Charcoal
          'bg-secondary': '#1A1D29',  // Card Background
          'bg-tertiary': '#2A2D3A',   // Elevated Surface
          
          // Neutral Colors
          neutral: {
            100: '#F8FAFC',    // Pure White
            200: '#E2E8F0',    // Mist Grey
            300: '#94A3B8',    // Medium Grey
            400: '#64748B',    // Text Secondary
            500: '#475569',    // Text Muted
          },
          
          // Semantic Colors
          success: '#10B981',     // Success Green
          warning: '#F59E0B',     // Warning Amber
          error: '#EF4444',       // Error Red
          info: '#3B82F6',        // Info Blue
          
          // Chart Colors
          chart: {
            1: '#00D4B8',      // Primary teal
            2: '#4F46E5',      // Blue
            3: '#8B5CF6',      // Purple
            4: '#EC4899',      // Pink
            5: '#F59E0B',      // Amber
            6: '#10B981',      // Green
          }
        }
      },
      
      fontFamily: {
        'quest': ['GT Walsheim', 'system-ui', 'sans-serif'],
        'quest-mono': ['SF Mono', 'Monaco', 'Inconsolata', 'monospace'],
      },
      
      fontSize: {
        'quest-display': ['4rem', { lineHeight: '1.1' }],      // 64px
        'quest-h1': ['3rem', { lineHeight: '1.2' }],           // 48px
        'quest-h2': ['2.25rem', { lineHeight: '1.25' }],       // 36px
        'quest-h3': ['1.875rem', { lineHeight: '1.3' }],       // 30px
        'quest-h4': ['1.5rem', { lineHeight: '1.4' }],         // 24px
        'quest-h5': ['1.25rem', { lineHeight: '1.4' }],        // 20px
        'quest-h6': ['1.125rem', { lineHeight: '1.5' }],       // 18px
        'quest-body': ['1rem', { lineHeight: '1.5' }],         // 16px
        'quest-body-sm': ['0.875rem', { lineHeight: '1.5' }],  // 14px
        'quest-caption': ['0.75rem', { lineHeight: '1.4' }],   // 12px
      },
      
      backgroundImage: {
        'quest-gradient': 'linear-gradient(135deg, #00D4B8 0%, #4F46E5 100%)',
        'quest-gradient-secondary': 'linear-gradient(135deg, #4F46E5 0%, #8B5CF6 100%)',
        'quest-gradient-accent': 'linear-gradient(135deg, #00D4B8 0%, #8B5CF6 100%)',
        'quest-sphere': 'radial-gradient(circle at 30% 30%, #00D4B8, #4F46E5, #8B5CF6)',
      },
      
      boxShadow: {
        'quest-sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'quest-md': '0 4px 16px rgba(0, 0, 0, 0.1)',
        'quest-lg': '0 8px 32px rgba(0, 0, 0, 0.2)',
        'quest-glow': '0 0 20px rgba(0, 212, 184, 0.3)',
        'quest-hover': '0 8px 24px rgba(0, 0, 0, 0.2)',
      },
      
      spacing: {
        'quest-1': '0.25rem',   // 4px
        'quest-2': '0.5rem',    // 8px
        'quest-3': '0.75rem',   // 12px
        'quest-4': '1rem',      // 16px
        'quest-5': '1.25rem',   // 20px
        'quest-6': '1.5rem',    // 24px
        'quest-8': '2rem',      // 32px
        'quest-10': '2.5rem',   // 40px
        'quest-12': '3rem',     // 48px
        'quest-16': '4rem',     // 64px
        'quest-20': '5rem',     // 80px
      },
      
      borderRadius: {
        'quest-sm': '0.25rem',  // 4px
        'quest-md': '0.5rem',   // 8px
        'quest-lg': '0.75rem',  // 12px
        'quest-xl': '1rem',     // 16px
      },
      
      transitionDuration: {
        'quest-fast': '150ms',
        'quest-normal': '200ms',
        'quest-slow': '300ms',
        'quest-slower': '500ms',
      },
      
      transitionTimingFunction: {
        'quest-out': 'cubic-bezier(0, 0, 0.2, 1)',
        'quest-in': 'cubic-bezier(0.4, 0, 1, 1)',
        'quest-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      
      animation: {
        'quest-pulse': 'quest-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'quest-gradient': 'quest-gradient 3s ease infinite',
      },
      
      keyframes: {
        'quest-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'quest-gradient': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      
      maxWidth: {
        'quest-container': '1440px',
        'quest-content': '1200px',
      },
      
      screens: {
        'quest-sm': '640px',
        'quest-md': '768px',
        'quest-lg': '1024px',
        'quest-xl': '1280px',
        'quest-2xl': '1536px',
      },
    },
  },
  plugins: [],
}
```

## 🎯 **Utility Classes**

### **Component Classes**
```css
/* Quest Button Components */
.quest-btn-primary {
  @apply bg-quest-gradient text-white px-6 py-3 rounded-quest-md font-medium transition-quest-normal hover:shadow-quest-glow hover:-translate-y-0.5;
}

.quest-btn-secondary {
  @apply bg-transparent text-quest-primary border border-quest-primary px-6 py-3 rounded-quest-md font-medium transition-quest-normal hover:bg-quest-primary hover:text-white;
}

.quest-btn-disabled {
  @apply bg-quest-neutral-500 text-quest-neutral-300 px-6 py-3 rounded-quest-md font-medium cursor-not-allowed;
}

/* Quest Card Components */
.quest-card {
  @apply bg-quest-bg-secondary border border-white border-opacity-10 rounded-quest-lg p-quest-6 shadow-quest-md;
}

.quest-card-elevated {
  @apply bg-quest-bg-tertiary shadow-quest-lg;
}

.quest-card-hover {
  @apply transition-quest-normal hover:shadow-quest-hover hover:-translate-y-0.5;
}

/* Quest Input Components */
.quest-input {
  @apply bg-quest-bg-tertiary border border-white border-opacity-10 text-quest-neutral-100 px-4 py-3 rounded-quest-md text-quest-body focus:border-quest-primary focus:ring-2 focus:ring-quest-primary focus:ring-opacity-20 focus:outline-none;
}

.quest-label {
  @apply text-quest-neutral-200 text-quest-body-sm font-medium mb-quest-2;
}

/* Quest Typography */
.quest-heading-display {
  @apply font-quest text-quest-display font-bold text-quest-neutral-100;
}

.quest-heading-1 {
  @apply font-quest text-quest-h1 font-bold text-quest-neutral-100;
}

.quest-heading-2 {
  @apply font-quest text-quest-h2 font-semibold text-quest-neutral-100;
}

.quest-text-body {
  @apply font-quest text-quest-body text-quest-neutral-200;
}

.quest-text-muted {
  @apply font-quest text-quest-body-sm text-quest-neutral-400;
}

/* Quest Layout */
.quest-container {
  @apply max-w-quest-container mx-auto px-quest-6;
}

.quest-content {
  @apply max-w-quest-content mx-auto;
}

/* Quest Animations */
.quest-hover-lift {
  @apply transition-quest-normal hover:-translate-y-0.5 hover:shadow-quest-hover;
}

.quest-gradient-animate {
  @apply bg-gradient-to-r bg-300% animate-quest-gradient;
}

.quest-pulse {
  @apply animate-quest-pulse;
}

/* Quest Spheres */
.quest-sphere {
  @apply w-30 h-30 rounded-full bg-quest-sphere shadow-quest-glow relative;
}

.quest-sphere::before {
  @apply content-[''] absolute top-6 left-9 w-9 h-9 bg-white bg-opacity-30 rounded-full blur-sm;
}
```

## 📱 **Responsive Utilities**

### **Breakpoint-Specific Classes**
```css
/* Mobile First Responsive */
.quest-responsive-grid {
  @apply grid grid-cols-1 gap-quest-4 quest-md:grid-cols-2 quest-lg:grid-cols-3 quest-xl:grid-cols-4;
}

.quest-responsive-text {
  @apply text-quest-h3 quest-md:text-quest-h2 quest-lg:text-quest-h1;
}

.quest-responsive-padding {
  @apply p-quest-4 quest-md:p-quest-6 quest-lg:p-quest-8;
}

.quest-responsive-spacing {
  @apply space-y-quest-4 quest-md:space-y-quest-6 quest-lg:space-y-quest-8;
}
```

## 🎨 **Dark Mode Support**

### **Dark Mode Variants**
```css
/* Already optimized for dark mode as primary theme */
.quest-light-mode {
  /* Alternative light theme tokens if needed */
  --quest-bg-primary: #FFFFFF;
  --quest-bg-secondary: #F8FAFC;
  --quest-bg-tertiary: #F1F5F9;
  --quest-text-primary: #1E293B;
  --quest-text-secondary: #475569;
}
```

## 🚀 **Implementation Guide**

### **Installation Steps**
1. **Update Tailwind Config**: Replace existing `tailwind.config.js` with Quest configuration
2. **Import CSS Variables**: Add design token CSS to main stylesheet
3. **Apply Component Classes**: Use Quest utility classes in components
4. **Test Responsive Design**: Verify all breakpoints work correctly
5. **Validate Accessibility**: Ensure color contrast meets WCAG AA standards

### **Usage Examples**
```tsx
// Button Component
<button className="quest-btn-primary quest-hover-lift">
  Get Started
</button>

// Card Component  
<div className="quest-card quest-card-hover">
  <h3 className="quest-heading-2">Trinity Discovery</h3>
  <p className="quest-text-body">Discover your professional identity</p>
</div>

// Input Component
<div>
  <label className="quest-label">Email Address</label>
  <input className="quest-input" type="email" placeholder="Enter email" />
</div>

// Layout Container
<div className="quest-container quest-responsive-padding">
  <div className="quest-content">
    {/* Content here */}
  </div>
</div>
```

---

**Quest Core Design Tokens** - Complete implementation guide for Quest's premium design system with Tailwind CSS integration.