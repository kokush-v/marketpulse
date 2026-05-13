# Proposal: Use Monochrome Dark Theme

## Problem

The frontend foundation currently uses colored shadcn/Tailwind theme tokens, including blue primary and teal accent colors. MarketPulse should instead present a black-and-white visual theme with dark-toned accents so the product UI feels restrained, focused, and consistent with the requested direction.

## Scope

- Update the frontend shadcn/Tailwind CSS theme tokens to a monochrome dark palette.
- Keep existing shadcn/ui component usage and Tailwind token names intact.
- Preserve accessible foreground/background contrast for the initial route.

## Out of Scope

- Adding new product screens.
- Adding or replacing shadcn/ui components.
- Changing backend, database, infrastructure, authentication, or provider integration behavior.
- Implementing user-selectable light/dark theme switching.

## Acceptance Criteria

- The default frontend theme uses black, white, and neutral gray tones instead of blue or teal brand accents.
- Primary, secondary, muted, accent, card, border, input, and ring tokens remain available through the existing shadcn/Tailwind CSS variable names.
- The initial frontend route renders with a dark-toned monochrome appearance.
- Frontend lint and typecheck continue to pass.

## Related Specs

- `openspec/specs/project-foundation/spec.md`
