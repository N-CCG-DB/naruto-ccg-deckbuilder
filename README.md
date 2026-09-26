# Naruto CCG Deck Builder

A browser-based deck builder for the Naruto Collectible Card Game (the
2006 Bandai game). Browse every card, build a deck, and export it to
Tabletop Simulator or a plain text decklist.

Live site: https://n-ccg-db.github.io/naruto-ccg-deckbuilder/

## Features

- Browse 4,400+ cards across all 28 sets plus promos and tournament packs
- Filter by name, card type, and set
- Card inspector with full stats, effect text, and high-quality scans
- Deck building with three zones: Mainboard, Reinforcements, Sideboard
- Export to:
  - Tabletop Simulator (.json save object)
  - Plain text decklist (.txt)
- Import decks back from either format
- Dark theme, keyboard-friendly, no account required

### Layout features

- **Resizable Card Inspector.** Drag the handle on its right edge to
  widen or narrow the panel. The card image scales with the panel.
- **Collapsible Decklist.** Click "Hide ▶" in the deck header to
  collapse the panel, and "◀ Show Deck" to bring it back.
- **Responsive mobile layout.** On phones the panels stack and a
  bottom tab bar switches between Cards, Inspector, and Deck.
- **Filters reset scroll.** Changing the set, type, or search
  automatically jumps the card browser back to the top.

Panel sizes reset on page refresh — by design, so the app always
starts in a consistent state.

## How to Use

Just open the live site. No install, no sign-up.

1. Find cards with the search bar and filters at the top
2. Click a card to inspect it in the left panel
3. Use + / - on any card to add/remove from your deck
4. Switch target zone with the Mainboard / Reinforcements / Sideboard
   buttons
5. Collapse the decklist with "Hide ▶" if you want more room for cards
6. Export when you're done. The TTS export is ready to load straight
   into Tabletop Simulator as a deck object.

## Running Locally

The site is fully static. No build step.

    git clone https://github.com/N-CCG-DB/naruto-ccg-deckbuilder.git
    cd naruto-ccg-deckbuilder

Then either:

- Open index.html with Live Server in VS Code (recommended — fetch
  needs a local server), or
- Run: python -m http.server 8000
  and visit http://localhost:8000

Note: Opening index.html directly via file:// will fail because the
browser blocks fetch on local files.

## Data Pipeline (for maintainers)

> **Heads up:** The Python pipeline scripts currently live in
> `unused/`. They are kept for archival purposes and can be restored
> to the project root if the database needs to be rebuilt. The live
> site does not depend on them.

Card data lives in cards.json. Images live in cards_database/, one
folder per set. To regenerate after adding or renaming images:

    # First, move the pipeline scripts back to the root:
    #   unused/list_images.py      -> list_images.py
    #   unused/merge_cards.py      -> merge_cards.py
    #   unused/exports/            -> exports/

    python list_images.py    walks cards_database/ to cards_from_images.json
    python merge_cards.py    merges with exports/card_database.json to cards.json

Then commit and push. GitHub Pages will redeploy automatically.

See PROJECT_BRIEF.md for the full schema, folder conventions, and rules.

## Project Structure

| Path | Purpose |
|---|---|
| index.html | The entire app (HTML + CSS + JS) |
| cards.json | Canonical card database |
| sets.json | Set display names + dropdown order |
| cards_database/ | Card images, one folder per set |
| cardback.webp | Card back image used by the TTS export |
| convert_incoming.py | Converts staged data from incoming_cards/ |
| incoming_cards/ | Staging area for new card data |
| unused/ | Archived scripts (image listing, merging, scraping) |
| PROJECT_BRIEF.md | Full technical documentation |

## Card Image Credits

Card scans are community-sourced for preservation and play purposes.
Naruto CCG and all related properties are (c) Bandai. This is a fan
project and is not affiliated with or endorsed by Bandai.

## Contributing

Issues and PRs welcome, especially:
- Missing card data (some promo and errata cards still need entries)
- New features for the deck builder
- Bug reports for the TTS export

If you're an AI assistant picking this project up: read
PROJECT_BRIEF.md first. It has the schema, folder conventions, and
rules you need.

## License

Code is MIT. Card images remain the property of their respective
rights holders.