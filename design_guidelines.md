{
  "product": {
    "name": "LabStock – Sistem Pemantauan Stok Reagen Laboratorium PK",
    "type": "internal data-dense operational dashboard (Excel replacement)",
    "language": "Bahasa Indonesia",
    "brand_attributes": [
      "profesional",
      "tepercaya (medical-grade)",
      "cepat dipindai (scan-friendly)",
      "padat data tapi tetap terbaca",
      "familiar seperti Excel (sticky header/kolom, zebra rows, angka rapih)"
    ],
    "north_star": "Staf lab bisa memantau pemakaian harian 1–31, melihat alarm buffer stock, dan menyiapkan PRF tanpa kehilangan konteks baris/kolom seperti di Excel."
  },

  "inspiration_refs": {
    "web_refs": [
      {
        "title": "shadcn/ui Data Table + patterns",
        "url": "https://ui.shadcn.com/docs/components/base/data-table",
        "why": "Baseline shadcn table primitives + data-table approach."
      },
      {
        "title": "TanStack Table column pinning (sticky/pinned columns)",
        "url": "https://tanstack.com/table/latest/docs/framework/react/guide/column-pinning",
        "why": "Best practice for pinned first column + offsets."
      },
      {
        "title": "shadcn blocks – sticky header table",
        "url": "https://www.shadcn.io/blocks/tables-sticky-header",
        "why": "Reference for sticky header + scroll container."
      },
      {
        "title": "shadcn blocks – pinned columns",
        "url": "https://www.shadcn.io/blocks/tables-pinned-columns",
        "why": "Reference for pinned first column + shadow edge cue."
      },
      {
        "title": "OpenELIS reagent forecasting facility UI notes",
        "url": "https://github.com/DIGI-UW/openelis-work/blob/main/designs/inventory/reagent-forecasting-facility.md",
        "why": "Clinical inventory context + status semantics."
      }
    ],
    "design_fusion": "Layout discipline ala enterprise data tables (sticky/pinned + density controls) + medical-neutral palette (cool gray + teal) + Excel-like conditional formatting badges (solid fills, no gradients)."
  },

  "typography": {
    "font_pairing": {
      "ui": {
        "family": "IBM Plex Sans",
        "fallback": "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
        "why": "Highly legible for dense numeric UI; professional/enterprise tone."
      },
      "numbers": {
        "family": "IBM Plex Mono",
        "fallback": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas",
        "why": "Aligns digits in day columns; improves scan speed."
      }
    },
    "tailwind_setup_note": "Use Google Fonts import in index.css OR add via <link> in public/index.html. Apply mono only to numeric cells (days 1–31, totals).",
    "type_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "section_title": "text-lg font-semibold",
      "table_header": "text-xs font-semibold uppercase tracking-wide",
      "table_cell": "text-sm",
      "small": "text-xs"
    },
    "numeric_formatting": {
      "alignment": "Numbers right-aligned; text left-aligned; status centered.",
      "tabular_nums": "Add Tailwind class: tabular-nums (if available) + font-mono for day cells.",
      "thousands": "Use Indonesian locale formatting for totals where applicable (e.g., 1.234)."
    }
  },

  "color_system": {
    "notes": [
      "No purple. No heavy gradients. This is a clinical tool; prioritize clarity.",
      "Status must not rely on color alone: always include label text (KRITIS / WASPADA / AMAN).",
      "Use solid fills for status badges (Excel-like conditional formatting)."
    ],
    "tokens_hsl_for_index_css": {
      "background": "210 25% 98%",
      "foreground": "222 47% 11%",
      "card": "0 0% 100%",
      "card-foreground": "222 47% 11%",
      "popover": "0 0% 100%",
      "popover-foreground": "222 47% 11%",

      "primary": "198 78% 28%",
      "primary-foreground": "0 0% 100%",

      "secondary": "210 20% 96%",
      "secondary-foreground": "222 47% 11%",

      "muted": "210 18% 94%",
      "muted-foreground": "215 16% 40%",

      "accent": "174 45% 92%",
      "accent-foreground": "198 78% 18%",

      "destructive": "0 72% 52%",
      "destructive-foreground": "0 0% 100%",

      "border": "214 20% 88%",
      "input": "214 20% 88%",
      "ring": "198 78% 28%",

      "radius": "0.6rem",

      "status-critical": "0 72% 52%",
      "status-warning": "38 92% 50%",
      "status-safe": "152 55% 36%",
      "status-neutral": "215 16% 40%"
    },
    "status_badges": {
      "critical": {
        "label": "KRITIS",
        "bg": "bg-red-600",
        "text": "text-white",
        "ring": "ring-1 ring-red-700/30"
      },
      "warning": {
        "label": "WASPADA",
        "bg": "bg-amber-500",
        "text": "text-slate-950",
        "ring": "ring-1 ring-amber-600/30"
      },
      "safe": {
        "label": "AMAN",
        "bg": "bg-emerald-600",
        "text": "text-white",
        "ring": "ring-1 ring-emerald-700/30"
      },
      "unknown": {
        "label": "PERLU CEK",
        "bg": "bg-slate-200",
        "text": "text-slate-800",
        "ring": "ring-1 ring-slate-300"
      }
    },
    "row_highlight_rules": {
      "critical_row": "Optional: tint row background very lightly (bg-red-50) but keep text readable; do not over-saturate.",
      "warning_row": "Optional: bg-amber-50",
      "safe_row": "No tint; rely on badge + numbers."
    },
    "allowed_gradients": {
      "usage": "Only for top header strip or dashboard hero accent (<=20% viewport).",
      "examples": [
        "bg-gradient-to-r from-slate-50 via-teal-50 to-slate-50",
        "bg-gradient-to-b from-white via-slate-50 to-white"
      ]
    }
  },

  "layout": {
    "app_shell": {
      "pattern": "Persistent left sidebar + top bar (period selector) + main content area.",
      "desktop_grid": "Sidebar 260px fixed; content fluid; max-w-none (do not center).",
      "mobile_behavior": "Sidebar collapses into Sheet (hamburger). Top bar stays sticky.",
      "page_padding": "px-3 sm:px-4 lg:px-6 py-4",
      "content_max_width": "Do NOT constrain to narrow max width; tables need full viewport."
    },
    "top_bar": {
      "height": "h-14",
      "sticky": "sticky top-0 z-40",
      "style": "bg-background/80 backdrop-blur border-b",
      "left": "Page title + breadcrumb",
      "right": "Month/Year selector + quick actions (Export/Refresh placeholder)"
    },
    "dashboard": {
      "structure": [
        "Row 1: KPI cards (Total Reagen, KRITIS, WASPADA, AMAN)",
        "Row 2: Quick links cards (Pemantauan Stok, Master Reagen, Data LIS)",
        "Row 3: Mini table 'Reagen Kritis Hari Ini' (top 10)"
      ],
      "kpi_card_style": "Card with left colored accent bar (2px) matching status; big number + small label."
    }
  },

  "tables": {
    "core_principles": [
      "Excel-like density: compact row height, small header text, numeric alignment.",
      "Sticky header + sticky first column (Nama Reagen).",
      "Horizontal scroll for day columns 1–31.",
      "Zebra rows + hover row highlight.",
      "Clear column grouping: Identitas, Pemakaian Harian, Rekap, Stok."
    ],
    "density_modes": {
      "default": "condensed",
      "options": {
        "condensed": {
          "row": "h-9",
          "cell_padding": "px-2 py-1",
          "font": "text-sm"
        },
        "regular": {
          "row": "h-10",
          "cell_padding": "px-3 py-2",
          "font": "text-sm"
        }
      },
      "ui_control": "Optional: a Select 'Kerapatan' (Padat/Normal) stored in localStorage."
    },
    "pemantauan_stok_table": {
      "container": {
        "wrapper": "Use ScrollArea or div with overflow-auto; set max-h: calc(100vh - topbar - filters - padding).",
        "tailwind": "relative rounded-lg border bg-card",
        "scroll": "overflow-auto",
        "shadow_cues": "Add subtle inset shadow at pinned column edge: after pseudo-element or box-shadow on sticky cell."
      },
      "sticky_header": {
        "tailwind": "sticky top-0 z-30 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/75",
        "border": "border-b",
        "no_gradient": true
      },
      "sticky_first_column": {
        "tailwind": "sticky left-0 z-20 bg-card",
        "edge_shadow": "shadow-[2px_0_0_0_hsl(var(--border))]"
      },
      "day_columns": {
        "width": "w-12 (tight) or w-14 if readability issues",
        "cell": "text-right font-mono tabular-nums",
        "header": "text-center"
      },
      "computed_columns": {
        "total_pemakaian": "Right aligned, font-semibold",
        "sisa_stok": "Right aligned; if <= buffer show text-red-700 font-semibold",
        "saldo_akhir": "Right aligned; subtle emphasis"
      },
      "zebra_hover": {
        "zebra": "odd:bg-muted/30",
        "hover": "hover:bg-accent/40"
      },
      "empty_state": {
        "copy": "Belum ada data untuk periode ini.",
        "component": "Card + Button 'Muat Ulang'",
        "testids": ["pemantauan-empty-state", "pemantauan-reload-button"]
      },
      "loading_state": {
        "component": "Skeleton rows (10–12) + sticky header skeleton",
        "testid": "pemantauan-loading"
      }
    },
    "master_reagen_table": {
      "pattern": "Standard data table with inline edit via Dialog or Drawer (desktop: Dialog, mobile: Drawer).",
      "editable_cells": "Use Input with numeric validation; show 'Simpan' primary button.",
      "testids": [
        "master-reagen-table",
        "master-reagen-edit-button",
        "master-reagen-save-button"
      ]
    },
    "data_lis": {
      "layout": "Tabs: 'Raw LIS' (read-only table) + 'Mapping Test' (table with filter OK/TIDAK ADA).",
      "filter": "Use Select or Command for status filter.",
      "testids": ["data-lis-tabs", "mapping-status-filter"]
    }
  },

  "components": {
    "component_path": {
      "shadcn_ui": {
        "button": "/app/frontend/src/components/ui/button.jsx",
        "badge": "/app/frontend/src/components/ui/badge.jsx",
        "card": "/app/frontend/src/components/ui/card.jsx",
        "table": "/app/frontend/src/components/ui/table.jsx",
        "tabs": "/app/frontend/src/components/ui/tabs.jsx",
        "select": "/app/frontend/src/components/ui/select.jsx",
        "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
        "sheet": "/app/frontend/src/components/ui/sheet.jsx",
        "dialog": "/app/frontend/src/components/ui/dialog.jsx",
        "drawer": "/app/frontend/src/components/ui/drawer.jsx",
        "separator": "/app/frontend/src/components/ui/separator.jsx",
        "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
        "sonner": "/app/frontend/src/components/ui/sonner.jsx",
        "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
        "calendar": "/app/frontend/src/components/ui/calendar.jsx"
      }
    },
    "sidebar_nav": {
      "items": [
        "Dashboard",
        "Pemantauan Stok",
        "Master Reagen",
        "Data LIS",
        "PRF",
        "Penerimaan",
        "Analisis Struktur Excel"
      ],
      "active_state": "bg-accent text-accent-foreground font-medium",
      "iconography": "Use lucide-react icons only (no emoji).",
      "testids": {
        "sidebar": "app-sidebar",
        "nav-item": "sidebar-nav-item-<slug>"
      }
    },
    "month_year_selector": {
      "component": "Select (month) + Select (year) OR a Popover with Calendar month picker.",
      "recommended": "Two Selects for speed + familiarity.",
      "testids": ["period-month-select", "period-year-select"]
    },
    "status_badge_component": {
      "base": "Use shadcn Badge but override variants via className.",
      "example": "<Badge className=\"bg-red-600 text-white ring-1 ring-red-700/30\">KRITIS</Badge>",
      "testid": "reagen-status-badge"
    },
    "inline_alerts": {
      "pattern": "Top-of-page alert strip listing counts + quick filter chips (Kritis/Waspada/Aman).",
      "component": "Alert + Badge + Button(ghost)",
      "testids": ["status-alert-strip", "status-filter-chip-critical"]
    }
  },

  "motion_microinteractions": {
    "principles": [
      "No universal transition: only transition-colors, shadow, opacity.",
      "Micro feedback for dense workflows: hover row, active pinned shadow, focus rings.",
      "Respect prefers-reduced-motion."
    ],
    "table_interactions": {
      "row_hover": "transition-colors duration-150",
      "cell_focus": "When editing: ring-2 ring-ring ring-offset-2",
      "pinned_column_edge": "On horizontal scroll, show stronger shadow (optional via scroll listener)."
    },
    "recommended_library": {
      "name": "framer-motion",
      "use_cases": ["sidebar collapse", "dashboard card entrance (subtle)", "toast/alert presence"],
      "install": "npm i framer-motion",
      "note": "Keep motion subtle; avoid bouncy animations in medical tool."
    }
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text on badges and table backgrounds.",
      "Status not color-only: include label + optional icon (AlertTriangle/CheckCircle).",
      "Keyboard navigation: focusable controls in top bar and filters.",
      "Sticky header must not obscure focus outlines; ensure z-index layering."
    ],
    "aria": {
      "tables": "Use proper <Table>, <TableHead>, <TableRow>, <TableCell> semantics from shadcn.",
      "filters": "Label Selects with <Label> and aria-label where needed."
    }
  },

  "data_density_rules": {
    "do": [
      "Use compact spacing (px-2) in day columns.",
      "Use mono font for numeric columns.",
      "Keep header labels short (Hari 1..31).",
      "Provide quick filters (Kritis/Waspada/Aman) to reduce scanning load."
    ],
    "dont": [
      "Do not convert the monitoring table into cards.",
      "Do not hide day columns behind accordions on desktop.",
      "Do not use large gradients or decorative illustrations."
    ]
  },

  "copy_guidelines_id": {
    "status_terms": {
      "critical": "KRITIS (Perlu order/CITO)",
      "warning": "WASPADA (Mendekati buffer)",
      "safe": "AMAN",
      "prf_warning": "PRF perlu dibuat"
    },
    "table_columns": {
      "nama_reagen": "Nama Reagen",
      "qc": "QC",
      "total_pemakaian": "Total Pemakaian",
      "saldo_awal": "Saldo Awal",
      "stok_masuk": "Stok Masuk",
      "sisa_stok": "Sisa Stok",
      "buffer_stock": "Buffer Stock",
      "satuan": "Satuan",
      "status": "Status"
    }
  },

  "images": {
    "image_urls": [
      {
        "category": "background_texture",
        "description": "Optional subtle noise overlay (CSS-based). No photos needed for this app.",
        "urls": []
      }
    ],
    "css_noise_snippet": "/* Add to a global wrapper: */\n.bg-noise::before {\n  content: \"\";\n  position: absolute;\n  inset: 0;\n  pointer-events: none;\n  background-image: url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='.08'/%3E%3C/svg%3E\");\n  mix-blend-mode: multiply;\n}"
  },

  "implementation_notes_js": {
    "no_tsx": true,
    "data_testid_rule": "All interactive and key informational elements MUST include data-testid in kebab-case.",
    "z_index_layering": {
      "header": "z-30",
      "sticky_first_col": "z-20",
      "body": "z-0"
    },
    "table_scaffold_hint": {
      "tanstack_optional": "If using TanStack Table for pinning/virtualization later, keep column definitions separate and add columnPinning state.",
      "simple_now": "Phase 1 can use plain shadcn Table + CSS sticky for first column/header."
    }
  },

  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css : replace :root tokens with the provided HSL tokens (keep dark mode optional but not default).",
    "Remove/ignore CRA demo styles in App.css (App-header etc). Do NOT center the app container.",
    "Build an AppShell layout: Sidebar + Topbar (sticky) + main content. Use Sheet for mobile sidebar.",
    "Pemantauan Stok page: implement a scroll container with sticky header and sticky first column; day columns 1–31 fixed width; numeric cells use font-mono + text-right.",
    "Implement StatusBadge helper that maps (sisa_stok vs buffer) to KRITIS/WASPADA/AMAN with the exact badge classes; include label text always.",
    "Add quick filters (chips/buttons) for status on Pemantauan Stok and Dashboard; each must have data-testid.",
    "Use Skeleton for loading and Card-based empty states; keep copy in Bahasa Indonesia.",
    "Avoid gradients except subtle header strip; never exceed 20% viewport; never apply gradients to tables/cards.",
    "Ensure all buttons/inputs/selects/tabs/links and key stats numbers include data-testid attributes."
  ],

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
