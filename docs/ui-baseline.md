# UI Baseline And Display Contract

## Baseline

The pre-redesign v1.0.0 screens are stored in
`resources/baseline-v1.0.0/`. They cover:

- home;
- game mode;
- difficulty;
- empty placement board;
- populated tactical board;
- Hard AI response;
- instructions.

The current public screenshots in `resources/` use the shared visual system from
`ui_theme.py`. Comparing the two sets provides a stable manual regression check
for screen hierarchy, text containment, and component consistency.

## Display Contract

- Logical canvas and minimum supported resolution: **900 x 720**.
- Target Windows display scales: **100%, 125%, and 150%**.
- Text must remain within its panel at the logical canvas size.
- Status metrics use measured columns rather than fixed text coordinates.
- Buttons provide default and hover states from the shared theme.

The automated tests resize complete rendered surfaces at each target scale. A
release candidate should still be opened on Windows at all three DPI settings,
because surface resizing does not reproduce every operating-system font and DPI
behavior.
