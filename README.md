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

## How to Use

Just open the live site. No install, no sign-up.

1. Find cards with the search bar and filters at the top
2. Click a card to inspect it in the left panel
3. Use + / - on any card to add/remove from your deck
4. Switch target zone with the Mainboard / Reinforcements / Sideboard
   buttons
5. Export when you're done. The TTS export is ready to load straight
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

Card data lives in cards.json. Images live in cards_database/, one
folder per set. To regenerate after adding or renaming images:

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
| exports/card_database.json | Rich card data source |
| list_images.py | Rebuilds image list from cards_database/ |
| merge_cards.py | Produces cards.json from images + rich data |
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