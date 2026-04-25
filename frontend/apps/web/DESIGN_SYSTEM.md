# Dispatch Frontend Design System

This file is the local design contract for `frontend/apps/web`.

## Source

- External reference: `C:\Users\aliam\OneDrive\Bureau\Workspace\HVAdesignsystem\README.md`
- Constraint: only the HVA Markdown was read. No code was copied from that repo.

## Interpretation Boundary

The HVA README defines the structure of the system, not exact visual tokens.

- Directly sourced from HVA:
  - Separate primitive components in `src/components/ui`
  - Separate product patterns in `src/components/patterns`
  - Shared token/theme layer
  - Shared chart styling utilities
  - Reuse tokens and patterns before adding one-off styles
- Dispatch-specific interpretation in this repo:
  - Warm-neutral light palette
  - IBM Plex Sans + IBM Plex Mono typography
  - Operator-console shell and page composition rules
  - Motion timings and semantic component states

## File Ownership

- Tokens: `src/styles/tokens.css`
- Global contracts: `src/app/globals.css`
- Primitives: `src/components/ui/*`
- Product patterns: `src/components/patterns/*`
- Shared chart styling: `src/lib/chart-theme.ts`

## Foundations

### Color Roles

- Background: `#f4f7fb`
- Primary surface: `#ffffff`
- Rail surface: `#0f1b2d`
- Muted surface: `#edf3f8`
- Subtle surface: `#f8fbfd`
- Border: `#d8e1ea`
- Strong border: `#b6c4d4`
- Text: `#0f1b2d`
- Muted text: `#5b6c82`
- Primary action: `#123150`
- Secondary highlight: `#1f4f73`
- Positive state: `#129a92`
- Danger state: `#c43d53`
- Rail text: `#f4f8fc`
- Rail muted text: `#b6c2d2`

### Typography

- UI font: `IBM Plex Sans`
- Data font: `IBM Plex Mono`
- Page title:
  - 1.625rem
  - 600 weight
  - tight tracking
- Section title:
  - 1rem
  - 600 weight
- Body copy:
  - 0.92rem to 0.95rem
  - muted where explanatory

### Spacing

- Core spacing rhythm: `8 / 12 / 16 / 24 / 32`
- Page content max width: `1360px`
- Sidebar width: `252px`
- Topbar height: `56px`

### Shape

- Small radius: `8px`
- Standard radius: `10px`
- Large radius: `12px`
- Do not exceed `12px` on standard product UI

### Shadow

- Only one base panel shadow is used:
  - `0 2px 8px rgba(69, 26, 3, 0.04)`
- No glow, bloom, glass, or detached floating shells

### Motion

- Fast: `120ms`
- Base: `160ms`
- Slow: `220ms`
- Allowed:
  - color changes
  - border changes
  - box-shadow changes
  - opacity changes
- Avoid:
  - bounce
  - translate hover motion
  - decorative transform motion
  - animated gradients

## Layout Rules

### App Shell

- Fixed left rail
- Simple top bar
- Main content centered inside the content area
- Dark navy rail with white text
- White content surfaces on a cool light background
- No right rail by default
- No dashboard hero sections

### Page Structure

Use this order for standard pages:

1. `PageIntro`
2. primary work section
3. supporting sections
4. tables or detailed lists

### Panels

- Use `SectionPanel` or `.surface-panel`
- Panel headers are simple:
  - title
  - short explanation
  - optional actions on the right

## Primitive Component Rules

### Buttons

- Default:
  - solid primary fill
  - white text
- Outline:
  - surface background
  - strong border
- Ghost:
  - transparent
  - subtle hover surface only
- Never use pill buttons
- Never use gradient fills

### Inputs

- Solid border
- Surface background
- Clear labels above fields
- Focus ring uses the shared focus token

### Badges

- `6px` radius
- Only semantic variants:
  - default
  - outline
  - success
  - warning
  - danger
  - muted
- Do not use badges as decoration

### Tables

- Sentence-case headers
- Left-aligned text
- Simple hover surface
- No zebra striping by default
- No loud KPI-card wrapper around tables

### Dialogs / Dropdowns / Tabs / Toasts

- Keep neutral surfaces
- Use shared radii and border tokens
- Keep transitions subtle
- Avoid theatrical entrance animation

## Pattern Rules

### `PageIntro`

- Standard entry point for top-of-page context
- Title on the left
- Short explanation below
- Functional actions on the right only

### `SectionPanel`

- Standard panel wrapper for tables, forms, summaries, and charts
- Handles title, description, actions, and internal spacing

### `PropertiesList`

- Use for short key-value summaries
- Label on the left
- value on the right
- Stacks on smaller screens

## Page-Type Guidance

### Dashboard / Index Pages

- Lead with operational state, not marketing copy
- Use route inventory, state summaries, and tables
- No hero strip, no oversized stat-card grid

### Form Pages

- Keep width restrained
- Label first
- Actions grouped at the bottom or top-right of the section

### Detail Pages

- Summary header first
- Then supporting panels
- Then related tables, logs, or charts

### Analytics Pages

- Use shared chart colors from `src/lib/chart-theme.ts`
- Keep chart frames simple
- Avoid fake visual density
- Default chart order is navy, teal, blue, then slate

## Chart Styling

- Primary series: `--chart-1`
- Comparison series: `--chart-2`
- Support series: `--chart-3`
- Neutral series: `--chart-4`
- Grid lines use `--border-subtle`
- Labels use `--text-muted`

## Writing Style

- Plain operator language
- No ornamental labels
- No startup copy
- No faux urgency
- No decorative dashboard slogans

## Do / Do Not

### Do

- Reuse `ui` primitives first
- Reuse `patterns` before page-local wrappers
- Keep layouts predictable
- Keep tables and forms dense but readable
- Keep states semantic and explicit

### Do Not

- Add hero sections to internal pages
- Add glassmorphism or dark glossy shells
- Use uppercase micro-labels as decoration
- Add transformed hover motion
- Invent one-off component styles when a token or pattern can solve it

## Implementation Rule For Future Sprints

Before adding a new page or component:

1. Check `src/components/ui`
2. Check `src/components/patterns`
3. Check `src/styles/tokens.css`
4. Check `src/lib/chart-theme.ts`
5. Add new styles only if the existing system cannot express the need cleanly
