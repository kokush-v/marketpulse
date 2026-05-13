# frontend-theme Specification

## Purpose
Define the default frontend visual theme for MarketPulse as a monochrome dark palette exposed through the shared shadcn and Tailwind token system.
## Requirements
### Requirement: Frontend uses a monochrome dark theme

The frontend SHALL use a black-and-white theme with dark-toned neutral accents for the default application appearance.

The frontend SHALL expose the theme through the existing shadcn/Tailwind CSS variable tokens so shadcn/ui components and product screens can consume the same palette consistently.

#### Scenario: Render initial route with monochrome dark theme

- Given the frontend application is running
- When the initial route is rendered
- Then the page uses dark neutral backgrounds
- And the page uses white or near-white foreground text
- And interactive or accent elements use neutral black, white, or gray tones instead of colored blue or teal accents

#### Scenario: Preserve shadcn token compatibility

- Given frontend components use shadcn/Tailwind tokens such as `background`, `foreground`, `card`, `primary`, `secondary`, `muted`, `accent`, `border`, `input`, and `ring`
- When the theme tokens are updated
- Then those token names remain available
- And existing shadcn/ui components continue to render through the same token interface
