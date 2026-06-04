tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: 'var(--border-shadcn)',
        input: 'var(--input-shadcn)',
        ring: 'var(--ring-shadcn)',
        background: 'var(--bg-shadcn)',
        foreground: 'var(--fg-shadcn)',
        primary: {
          DEFAULT: 'var(--primary-shadcn)',
          foreground: 'var(--primary-fg-shadcn)',
        },
        secondary: {
          DEFAULT: 'var(--secondary-shadcn)',
          foreground: 'var(--secondary-fg-shadcn)',
        },
        destructive: {
          DEFAULT: 'var(--destructive-shadcn)',
          foreground: 'var(--destructive-fg-shadcn)',
        },
        muted: {
          DEFAULT: 'var(--muted-shadcn)',
          foreground: 'var(--muted-fg-shadcn)',
        },
        accent: {
          DEFAULT: 'var(--accent-shadcn)',
          foreground: 'var(--accent-fg-shadcn)',
        },
        popover: {
          DEFAULT: 'var(--popover-shadcn)',
          foreground: 'var(--popover-fg-shadcn)',
        },
        card: {
          DEFAULT: 'var(--card-shadcn)',
          foreground: 'var(--card-fg-shadcn)',
        },
      },
      borderRadius: {
        lg: 'var(--radius-shadcn)',
        md: 'calc(var(--radius-shadcn) - 2px)',
        sm: 'calc(var(--radius-shadcn) - 4px)',
      },
    }
  }
}
