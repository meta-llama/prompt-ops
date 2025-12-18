import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
	fontFamily: {
		display: ['Clash Display', 'system-ui', 'sans-serif'],
		sans: ['Cabinet Grotesk', 'system-ui', 'sans-serif'],
		mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
	},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar-background))',
					foreground: 'hsl(var(--sidebar-foreground))',
					primary: 'hsl(var(--sidebar-primary))',
					'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
					border: 'hsl(var(--sidebar-border))',
					ring: 'hsl(var(--sidebar-ring))'
				},
				// Panel backgrounds (dark mode aware via CSS vars)
				panel: {
					DEFAULT: 'hsl(var(--panel))',
					hover: 'hsl(var(--panel-hover))',
					muted: 'hsl(var(--panel-muted))',
				},
				// Meta brand colors (dark mode aware via CSS vars)
				meta: {
					// Primary blue - uses CSS variable for dark mode
					blue: {
						DEFAULT: 'hsl(var(--meta-blue))',
						hover: 'hsl(var(--meta-blue-hover))',
						// Static variants for specific use cases
						800: '#004bb9',
						1000: '#000a50',
					},
					// Accent: Teal (highlights, success states)
					teal: {
						DEFAULT: 'hsl(var(--meta-teal))',
						hover: 'hsl(var(--meta-teal-hover))',
						700: '#009b9b',
						800: '#00787D',
						900: '#00414b',
					},
					// Accent: Purple (features, special elements)
					purple: {
						DEFAULT: 'hsl(var(--meta-purple))',
						text: 'hsl(var(--meta-purple-text))',
						800: '#6441D2',
						900: '#280578',
						1000: '#0a005a',
					},
					// Accent: Pink (notifications, badges)
					pink: {
						DEFAULT: 'hsl(var(--meta-pink))',
						800: '#B43C8C',
						900: '#640055',
					},
					// Accent: Orange (warnings, experimental)
					orange: {
						DEFAULT: 'hsl(var(--meta-orange))',
						text: 'hsl(var(--meta-orange-text))',
						800: '#A0460A',
					},
					// Accent: Cyan
					cyan: {
						700: '#0096c8',
						800: '#0073aa',
					},
					// Grays - static values, use foreground/muted for dark mode aware
					gray: {
						DEFAULT: '#1c2b33',
						900: '#283943',
						800: '#344854',
						600: '#67788A',
						300: '#CBD2D9',
						100: '#F1F4F7',
					},
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'fade-in': {
					from: {
						opacity: '0',
						transform: 'translateY(20px)'
					},
					to: {
						opacity: '1',
						transform: 'translateY(0)'
					}
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'fade-in': 'fade-in 0.8s ease-out forwards',
				'fade-in-delay': 'fade-in 0.8s ease-out 0.2s forwards',
				'fade-in-delay-2': 'fade-in 0.8s ease-out 0.4s forwards'
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;
