tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border:     'var(--border-shadcn)',
        input:      'var(--input-shadcn)',
        ring:       'var(--ring-shadcn)',
        background: 'var(--bg-shadcn)',
        foreground: 'var(--fg-shadcn)',

        primary: {
          DEFAULT:    'var(--primary-shadcn)',
          foreground: 'var(--primary-fg-shadcn)',
        },
        secondary: {
          DEFAULT:    'var(--secondary-shadcn)',
          foreground: 'var(--secondary-fg-shadcn)',
        },
        destructive: {
          DEFAULT:    'var(--destructive-shadcn)',
          foreground: 'var(--destructive-fg-shadcn)',
        },
        muted: {
          DEFAULT:    'var(--muted-shadcn)',
          foreground: 'var(--muted-fg-shadcn)',
        },
        accent: {
          DEFAULT:    'var(--accent-shadcn)',
          foreground: 'var(--accent-fg-shadcn)',
        },
        popover: {
          DEFAULT:    'var(--popover-shadcn)',
          foreground: 'var(--popover-fg-shadcn)',
        },
        card: {
          DEFAULT:    'var(--card-shadcn)',
          foreground: 'var(--card-fg-shadcn)',
        },

        /* ── Chart colours — from SupplyWise tailwind.config.ts ── */
        chart: {
          '1': 'var(--chart-1)',
          '2': 'var(--chart-2)',
          '3': 'var(--chart-3)',
          '4': 'var(--chart-4)',
          '5': 'var(--chart-5)',
        },

        /* ── Sidebar tokens — from SupplyWise tailwind.config.ts ── */
        sidebar: {
          DEFAULT:              'var(--sidebar)',
          foreground:           'var(--sidebar-foreground)',
          primary:              'var(--sidebar-primary)',
          'primary-foreground': 'var(--sidebar-primary-foreground)',
          accent:               'var(--sidebar-accent)',
          'accent-foreground':  'var(--sidebar-accent-foreground)',
          border:               'var(--sidebar-border)',
          ring:                 'var(--sidebar-ring)',
        },
      },

      borderRadius: {
        lg: 'var(--radius-shadcn)',
        md: 'calc(var(--radius-shadcn) - 2px)',
        sm: 'calc(var(--radius-shadcn) - 4px)',
      },

      /* ── Extra defaults matching SupplyWise tailwind.config.ts ── */
      borderColor: {
        DEFAULT: 'var(--border-shadcn)',
      },
      outlineColor: {
        DEFAULT: 'var(--ring-shadcn)',
      },
      ringColor: {
        DEFAULT: 'var(--ring-shadcn)',
      },
    }
  }
}
