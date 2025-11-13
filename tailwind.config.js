/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      // Asana Design System Implementation
      fontFamily: {
        'sans': ['"TWK Lausanne"', '"Helvetica Neue"', 'Helvetica', 'sans-serif'],
        'heading': ['Ghost', '"Helvetica Neue"', 'Helvetica', 'sans-serif'],
      },
      colors: {
        // Asana True Black Scale
        black: {
          20: '#fefefe',    // Almost white backgrounds
          50: '#f8f9fa',    // Very light gray
          100: '#f1f3f4',   // Light gray borders
          200: '#e8eaed',   // Subtle borders
          300: '#dadce0',   // Medium borders
          400: '#bdc1c6',   // Text on light backgrounds
          500: '#9aa0a6',   // Secondary text
          600: '#80868b',   // Muted text
          700: '#5f6368',   // Primary text on light
          800: '#3c4043',   // Strong text
          900: '#202124',   // Primary text
          1000: '#000000'   // Pure black
        },
        // Asana Accent Colors
        orange: {
          50: '#fef7f0',
          100: '#fef0e4',
          500: '#ff8c00',
          600: '#f57c00',
        },
        green: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          500: '#8b5cf6',
          600: '#7c3aed',
        },
        blue: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
      spacing: {
        // Asana Spacing System (0-160px)
        '0': '0px',
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '7': '28px',
        '8': '32px',
        '9': '36px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
        '20': '80px',
        '24': '96px',
        '32': '128px',
        '40': '160px'
      },
      borderRadius: {
        'asana': '3px',
        'DEFAULT': '3px',
        'sm': '2px',
        'md': '3px',
        'lg': '6px',
        'xl': '12px',
      },
      boxShadow: {
        'asana-1': '0 3px 5px 0 rgba(36, 50, 66, 0.2)',
        'asana-2': '0 11px 12px 0 rgba(36, 50, 66, 0.12)',
        'asana-3': '0 2px 4px 0 rgba(0, 0, 0, 0.1)',
        'asana-button': '0 1px 3px 0 rgba(0, 0, 0, 0.12)',
        'asana-card': '0 2px 8px 0 rgba(0, 0, 0, 0.08)',
      },
      fontSize: {
        // Asana Typography Scale
        'h1-mobile': '40px',
        'h1-desktop': '72px',
        'h2-mobile': '32px',
        'h2-desktop': '60px',
        'h3-mobile': '23px',
        'h3-desktop': '36px',
        'h4': '20px',
        'h5': '16px',
        'h6': '14px',
        'body': '15px',
        'small': '13px',
        'xs': '11px',
      },
      lineHeight: {
        'tight': '1.1',
        'snug': '1.2',
        'normal': '1.4',
        'relaxed': '1.6',
        'loose': '1.8',
      },
      transitionDuration: {
        'short': '75ms',
        'standard': '150ms',
        'long': '450ms',
      },
      zIndex: {
        'dropdown': '100',
        'sticky': '200',
        'fixed': '300',
        'modal-backdrop': '400',
        'modal': '500',
        'popover': '600',
        'tooltip': '700',
        'notification': '800',
        'debug': '900',
        'max': '1000',
      },
      screens: {
        'xs': '480px',
        'sm': '768px',
        'md': '960px',
        'lg': '1120px',
        'xl': '1280px',
      },
    },
  },
  plugins: [],
}

