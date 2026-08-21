# HubVision Dynamic Interface Design

## Direction

HubVision is a visual cockpit for creators, designers, and marketing professionals to discover AI tools and activate ready-to-use prompts. The landing page should move visitors toward one of two actions: explore the catalog or unlock access.

## Visual system

- Obsidian `#05070D` for the page background.
- Deep panel `#0D1721` for surfaces and drawers.
- Cyan `#39D8FF` for navigation and primary actions.
- Ice `#A9F7FF` for glass reflections and highlights.
- Violet `#7C5CFF` to distinguish prompt content.
- Lime `#C6FF62` only for status and confirmation states.
- `Space Grotesk` for display, `Outfit` for interface copy, and `DM Mono` for data labels.

## Layout and interaction

The existing dark sci-fi foundation remains, but hierarchy becomes more deliberate. The hero continues to introduce the product through the `explore / vision / crie` sequence. The tool catalog becomes quieter and more technical, with a scanner-like hover line for discovery. The prompt gallery becomes the expressive focal point, using imagery, filters, and direct copy actions.

`FERRAMENTAS` receives a lower-light treatment: reduced glow, less saturated text, and a restrained status accent. `BIBLIOTECA` receives a Digital Glass treatment: translucent text, an internal reflective band, subtle refraction-like shadowing, and a restrained hover sheen.

## Signature

The signature interaction is the "intent scanner": a thin cyan-violet line travels across a category or card on hover, suggesting that HubVision is indexing and surfacing useful resources.

## Constraints

- Preserve the existing prompt and bookmark data sources.
- Keep the page usable on mobile and keyboard navigable.
- Respect `prefers-reduced-motion` by disabling decorative sheen and scanner motion.
- Avoid adding a new framework or replacing the existing static architecture.
