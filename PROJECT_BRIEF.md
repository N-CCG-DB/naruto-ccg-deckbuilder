# Naruto CCG Deck Builder — Project Brief

Paste this file at the start of any new AI chat to give the assistant
full context. It is the single source of truth for this project.

## Purpose

A static web app hosted on GitHub Pages that lets users:
1. Browse a database of Naruto CCG (2006) cards
2. Filter by name, type, and set
3. Build a deck (Mainboard / Reinforcements / Sideboard)
4. Export the deck as Tabletop Simulator JSON or a plain text decklist
5. Import decks back from either format

Repo: https://github.com/N-CCG-DB/naruto-ccg-deckbuilder

## Tech Stack

- Plain HTML / CSS / JavaScript. No build step, no frameworks.
- GitHub Pages for hosting (case-sensitive, Linux-based).
- Python for offline data pipeline (image listing, merging, compression).
- JSON for card data.

## RECENT MIGRATION - READ THIS FIRST

As of the latest change, `index.html` reads `narutoccgdatabase.json`.
It no longer fetches `cards.json` or `sets.json`. Those two files are
still on disk but dormant - nothing reads them. They are kept for
rollback safety only.

The new database has a different shape and schema than the old one.
Details below. Do not assume the old schema when touching the app.

## File Layout (project root)

    naruto-ccg-deckbuilder/
    ├── index.html                    the app (single file: HTML+CSS+JS)
    ├── narutoccgdatabase.json        * LIVE card database (site reads this)
    ├── cards.json                    DORMANT - no longer read by the site
    ├── sets.json                     DORMANT - no longer read by the site
    ├── cards.json.backup             legacy backup from the old pipeline
    ├── cardback.webp                 card back for Tabletop Simulator export
    ├── PROJECT_BRIEF.md              this file
    ├── PROJECT_HANDOFF.md            pipeline notes for the master DB build
    ├── README.md                     user-facing docs
    ├── convert_incoming.py           converts incoming_cards/ staging data
    ├── cards_database/               ALL card images, one folder per set
    ├── incoming_cards/               staging (not used by the site)
    └── unused/                       archived scripts, not part of the pipeline
        ├── exports/
        │   └── card_database.json    rich card data source (old pipeline)
        ├── list_images.py            walks cards_database/ to cards_from_images.json
        ├── merge_cards.py            merges images + exports/card_database.json to cards.json
        ├── run_pipeline.py           (legacy) driver script
        ├── sync_sheets.py            (legacy) Google Sheets sync
        ├── update_database_from_scraped.py (legacy) scrape to DB script
        ├── cards_from_images.json    output of list_images.py
        ├── scraped_naruto_cards.json raw scrape (not used by the site)
        └── .processed_manifest.json  pipeline bookkeeping

Note: The entire Python pipeline lives in `unused/`. The live site
only needs `index.html`, `narutoccgdatabase.json`, `cardback.webp`,
and `cards_database/`.

## Canonical Card Schema - narutoccgdatabase.json

Top-level shape is a dict keyed by sheet name, each value an array of
card objects:

    {
      "Promo Cards": [ { ...card... }, ... ],
      "01 Path to Hokage": [ ... ],
      "02 Coils of the Snake": [ ... ],
      ...
    }

`index.html` flattens this into a single array at load time. Do not
change the file shape without updating the loader.

Each card object uses Title Case keys with spaces. Every card has
exactly these fields:

| Key | Type | Notes |
|---|---|---|
| Card ID | string | Lowercase internal ID, e.g. ex001, nus010, pr005r. Primary key. |
| Collector Number | string | Display form, e.g. EX-001, N-370. What users see. |
| Printed Name | string | Name as printed on the card |
| Display Name | string | Clean name - this is what the site shows |
| Type | string | Exactly one of: Ninja, Jutsu, Mission, Client |
| Set | string | Display name of the set, e.g. Promo Cards |
| Year | number or null | e.g. 2006 |
| Symbols | string | e.g. Fire/Lightning, Earth/Fire (may contain /) |
| Entrance Cost | number or null | Floats in the JSON (0.0, 3.0). Blank for Jutsu. |
| Hand Cost | number or null | Same. Blank for Jutsu. |
| Healthy Combat | number or null | Ninja only |
| Healthy Support | number or null | Ninja only |
| Injured Combat | number or null | Ninja only |
| Injured Support | number or null | Ninja only |
| Combat Attribute | string or null | Ninja only, e.g. Oil |
| Chakra Cost | string or null | Jutsu only, e.g. "L L 1" |
| Characteristics | string or null | Comma-separated. Ninja + Client. |
| Effect Title | string or null | Uppercased in the UI, wrapped in [ ] |
| Effect Text | string or null | Preserves real \n for multi-line display |
| Keywords | string or null | e.g. GROWTH, Permanent |
| Errata | string or null | |
| image_path | string | e.g. promos/ex001.webp - no leading ./, no cards_database/ prefix |

Rules:

- `Type` is never null and never "Other". Four values only.
- Empty cells are `null`, not `""` and not `"None"`. The old
  `cards.json` used `"None"` for some fields; the new DB does not.
  Do not add `"None"` handling.
- Numeric fields that are present come through as JSON numbers
  (0.0, 3.0). `index.html` renders them as integers.
- Effect Text line breaks are literal `\n` inside the string. The
  inspector renders them with `white-space: pre-line`.

Do not rename keys. `index.html` references them via a central `F`
field map at the top of the script.

## Image Path Convention

`index.html` builds URLs like:

    ./cards_database/{image_path}

`image_path` already contains `{setfolder}/{imgname}` - so
`promos/ex001.webp` becomes `./cards_database/promos/ex001.webp`.

Rules:

- All images live under `cards_database/`
- One subfolder per set
- Filenames are lowercase and match the image_path exactly
- GitHub Pages is case-sensitive. If `image_path` says `ex001.webp`
  but the file is `EX001.webp`, the image will 404 on the live site.

The set folder for filtering is derived from `image_path`, not from
a separate field: `image_path.split('/')[0]`. This guarantees the
filter matches the disk layout with no lookup table.

## Set Folders (canonical list)

Folder keys must match exactly. Dots are removed from folder names
(set_17.5 becomes set_175) even though the display name keeps the dot.
The display name shown in the dropdown comes from each card's `Set`
field, not from a hard-coded list.

| Folder key | Display Name |
|---|---|
| set_1_path_of_the_hokage | The Path to Hokage |
| set_2_coils_of_the_snake | Coils of the Snake |
| set_3_curse_of_the_sand | Curse of the Sand |
| set_4_revenge_and_rebirth | Revenge and Rebirth |
| set_5_dream_legacy | The Dream Legacy |
| set_6_eternal_rivalry | Eternal Rivalry |
| set_7_quest_for_power | Quest for Power |
| set_8_battle_for_destiny | Battle of Destiny |
| set_9_the_chosen | The Chosen |
| set_10_lineage_of_the_legends | Lineage of the Legends |
| set_11_approaching_wind | Approaching Wind |
| set_12_a_new_chronicle | A New Chronicle |
| set_13_fateful_reunion | Fateful Reunion |
| set_14_emerging_alliance | Emerging Alliance |
| set_15_fortold_prophecy | Foretold Prophecy |
| set_16_broken_promise | Broken Promise |
| set_17_will_of_fire | Will of Fire |
| set_175_tournament_pack_1 | Tournament Pack 1 |
| set_18_fangs_of_the_snake | Fangs of the Snake |
| set_19_path_of_pain | Path of Pain |
| set_195_tournament_pack_2 | Tournament Pack 2 |
| set_20_tales_of_the_galiant_sage | Tales of the Gallant Sage |
| set_21_shattered_truth | Shattered Truth |
| set_215_tournament_pack_3 | Tournament Pack 3 |
| set_22_weapons_of_war | Weapons of War |
| set_23_invasion | Invasion |
| set_235_tournament_pack_4 | Tournament Pack 4 |
| set_24_sages_legacy | Sage's Legacy |
| set_25_kage_summit | Kage Summit |
| set_26_avengers_wrath | Avenger's Wrath |
| set_27_heros_ascension | Hero's Ascension |
| set_28_ultimate_ninja_storm_3 | Ultimate Ninja Storm 3 |
| promos | Promo Cards |

## Card Type Rules (from Card ID prefix)

Legacy reference - `Type` is now explicit in the JSON. Only needed if
rebuilding from source:

| Prefix | Type |
|---|---|
| n, nus | Ninja |
| j, jus | Jutsu |
| m, mus | Mission |
| c, cus | Client |

Suffix letters on IDs: e (errata), a (alt art), r / ra (reprint),
b (separate card, never merged).

## Data Pipeline (for maintainers)

Heads up: The Python pipeline scripts currently live in `unused/`.
They produced `cards.json` under the old schema and are not used to
build `narutoccgdatabase.json`. See `PROJECT_HANDOFF.md` for how the
master DB was built.

If the site ever needs to go back to `cards.json`, restore the scripts
from `unused/` to the root and re-run `list_images.py` plus
`merge_cards.py`. Do not do this without an explicit request.

## What index.html Reads

- `fetch('narutoccgdatabase.json')` - card data
- Image URLs from `cards_database/{image_path}`

It does not fetch `cards.json` or `sets.json`. The set dropdown is
built at runtime from the data.

No build step. Open with Live Server, or git push for GitHub Pages.

## UI Behavior (index.html)

The app is a single file with three panels: Card Inspector (left),
Card Browser (center), Decklist (right).

### Data loading

- Fetches `narutoccgdatabase.json`
- Flattens `{sheet: [cards]}` into one array
- Builds `cardIndex` - a `Map` keyed by lowercased `Card ID` - for
  O(1) lookups during import and deck operations
- Builds the set dropdown from the union of `image_path` folders,
  taking the display name from each card's `Set` field

### Field map (F)

All master-DB keys are referenced through a single `F` object at the
top of the script:

    const F = {
      cardId:          'Card ID',
      collectorNumber: 'Collector Number',
      name:            'Display Name',
      type:            'Type',
      set:             'Set',
      year:            'Year',
      symbols:         'Symbols',
      entranceCost:    'Entrance Cost',
      handCost:        'Hand Cost',
      healthyCombat:   'Healthy Combat',
      healthySupport:  'Healthy Support',
      injuredCombat:   'Injured Combat',
      injuredSupport:  'Injured Support',
      combatAttribute: 'Combat Attribute',
      chakraCost:      'Chakra Cost',
      characteristics: 'Characteristics',
      effectTitle:     'Effect Title',
      effectText:      'Effect Text',
      keywords:        'Keywords',
      errata:          'Errata',
      imagePath:       'image_path',
    };

Never write a raw master-DB key string elsewhere in the file. Use `F`.

### Deck key convention

Deck pools (`currentDeck.main` / `.reinf` / `.side`) are keyed by
lowercased `Card ID`. Everything that adds, removes, or looks up a
card goes through `cardKey(card)`.

### Inspector

Two modes, controlled by the `MINIMAL_INSPECTOR` constant at the top
of the script. Flip it and refresh - no rebuild needed.

`MINIMAL_INSPECTOR = true` (default) renders these rows in this order,
hidden if the underlying value is null / "" / undefined:

| # | Row | Source | Visible for |
|---|---|---|---|
| 1 | Name | Display Name | all |
| 2 | Type | Type | all |
| 3 | Symbols | Symbols | all |
| 4 | Characteristics | Characteristics | Ninja, Client |
| 5 | Entrance Cost | Entrance Cost | Ninja, Mission, Client |
| 6 | Hand Cost | Hand Cost | Ninja, Mission, Client |
| 7 | Combat / Support (Healthy) | Healthy Combat / Healthy Support | Ninja |
| 8 | Combat / Support (Injured) | Injured Combat / Injured Support | Ninja |
| 9 | Combat Attribute | Combat Attribute | Ninja |
| 10 | Jutsu Cost | Chakra Cost | Jutsu |
| 11 | Effect | [EFFECT TITLE] uppercased + newline + Effect Text | all |
| 12 | Card Number | Collector Number | all |
| 13 | Set | Set | all |

Rules baked into the renderer:

- Numeric fields render as integers (0.0 becomes 0)
- Effect block uses `white-space: pre-line` so \n in `Effect Text`
  displays as real line breaks
- Effect Title is uppercased and wrapped in square brackets
- If Title is present but Text is not (or vice versa), only the
  present part renders
- Rows never print the literal string null

`MINIMAL_INSPECTOR = false` appends Year, Keywords, Errata rows at
the bottom, also hidden when blank. Nothing else changes.

### Layout and resizing

- Only the Card Inspector is user-resizable via a drag handle on its
  right edge. Width is clamped between 240px and 70% of viewport.
- Resize is desktop-only (`window.innerWidth > 820`). On mobile the
  panels stack and are switched via the mobile tab bar.
- Panel widths are NOT persisted. Refresh returns to CSS defaults
  (inspector 420px, decklist 340px fixed).

### Collapsible decklist

- The Decklist panel is a fixed 340px wide column that can be
  collapsed to 0 via the Hide button in its header.
- When collapsed, a floating Show Deck tab appears at the top-right
  of the Card Browser to bring it back.
- Always starts expanded on page load.
- Collapse is disabled on mobile (tab bar handles visibility there).

### Inspector image

- `.inspector-img` has no max-width; it fills the panel width minus
  padding, so dragging the panel wider makes the card image larger.

### Mobile layout

- Breakpoint: `max-width: 820px`.
- Panels stack vertically. A `.mobile-tabs` bar at the top switches
  between Cards, Inspector, and Deck views via `data-mobile-view`
  on `.app-container`.
- Card grid shrinks to `minmax(120px, 1fr)`.
- Clicking any card auto-switches to the Inspector view.

### Filter scroll reset

- Changing search, type, or set calls `scrollBrowserToTop()` so the
  browser snaps back to the top of the results.

### Search

Matches, case-insensitively, against:

- Display Name
- Collector Number
- Card ID

## Export / Import Formats

### TTS JSON (exportToTTS)

Standard Tabletop Simulator `DeckCustom` save object with one
`ObjectStates` entry per non-empty zone (Mainboard, Reinforcements,
Sideboard). Card `Description` is the lowercased `Card ID`. Image
URLs point at `{origin}/cards_database/{image_path}`.

Format is unchanged from the old build - old exports still load.

### Text export (exportTextDeck)

    // Mainboard
    3x Card Name [cardid]

    // Reinforcements
    1x Card Name [cardid]

    // Sideboard
    2x Card Name [cardid]

Only non-empty sections are written.

### TTS import (importJSONDeck)

Walks `ContainedObjects`, reads `Description` (lowercased), matches
against `cardIndex`. Falls back silently if no match. Section is
selected by `Nickname` on the parent deck object.

### Text import (importTextDeckPrompt)

Accepts `3x Name [id]` or `3 Name [id]` or `3x Name`. Matching order:

1. Lowercased `Card ID` (from brackets)
2. Lowercased `Collector Number` (from brackets)
3. Lowercased `Display Name`

Section headers detected by substring: reinforcement, sideboard, main.

Backwards compatible with old decklists that used lowercase IDs like
`nus001` / `jus001`, because those are still the lowercased `Card ID`
values.

## Known Issues / TODO

- ~129 promo cards may still have sparse data (missing Effect Text,
  missing Chakra Cost). No longer a type problem - `Type` is always
  populated in the new DB.
- Cards that reference missing image files will render a broken img.
  There is no placeholder fallback. If you add one, use a neutral
  background and no text.
- `cards.json` and `sets.json` are still in the repo for rollback but
  nothing references them. Deleting them is safe but not required.
- `PROJECT_HANDOFF.md` documents the old Excel to master-DB pipeline.
  It does not describe the current site.

## Rules for AI Assistants Working on This Project

1. The live data source is `narutoccgdatabase.json`. Do not switch
   back to `cards.json` or `sets.json` without an explicit request.
2. Never reference master-DB keys directly. Go through the `F` field
   map at the top of `index.html`.
3. Never add `"None"` or `"NaN"` string handling. The new DB uses
   real `null` for blanks. Guard with the `isBlank()` helper.
4. Never add dots to folder keys. Disk folders have no dots.
5. Never assume case-insensitive paths. GitHub Pages is
   case-sensitive.
6. Deck pools are keyed by lowercased `Card ID`. Do not change this
   without also updating import matching and the text export.
7. Ask before restructuring the pipeline. The Python scripts live in
   `unused/` and are not part of the live deployment.
8. Test in a browser after every change. The site should still
   filter, build decks, resize, collapse the decklist, and export.
   Test at least one Ninja, one Jutsu, one Mission, and one Client
   in the inspector.
9. Commit working states before making risky changes.
10. Panel sizes are intentionally NOT persisted. Do not add
    localStorage save/restore for panel widths unless the user asks.
11. The `MINIMAL_INSPECTOR` constant is the only intended switch for
    inspector verbosity. Do not add new inspector modes without being
    asked.
12. Effect Text must preserve \n. Do not collapse whitespace or use
    innerText where it would strip breaks - the display relies on
    `white-space: pre-line`.

## Addendum: Set Dropdown Derivation (post-migration fix)

An early version of the post-migration build derived the Set dropdown
label from the FIRST card's "Set" value inside each folder. That broke
when the source data had inconsistent "Set" values across a folder's
cards, producing duplicated labels (e.g. ten "Promo Cards" entries) and
dropping others entirely.

The current implementation in buildSetFolders() does this:

1. Group strictly by folder, where folder = image_path.split('/')[0].
   This is guaranteed unique per folder and always matches the disk
   layout. It is the dropdown's <option value>.
2. For each folder, count how many cards agree on each "Set" value.
   The label is the majority vote. Ties break alphabetically.
3. If a folder has no cards with a "Set" value, the label falls back
   to the folder name with underscores replaced by spaces.
4. If two folders resolve to the same label, append " (folder_key)"
   to disambiguate. This makes duplicate labels visible in the UI so
   the data problem can be spotted and fixed at the source.
5. Entries are natural-sorted on the folder key, so set_1 < set_2 <
   set_10 < set_17 < set_175 < set_18 < promos.
6. Any folder whose cards disagree on "Set" is logged via
   console.warn("Set inconsistency in folder ..."). Open devtools
   after load to see which folders have dirty source data.

Do NOT revert to first-card-wins label selection. Do NOT key the
dropdown by the "Set" value. The folder is the source of truth for
identity; "Set" is only a label hint.

If the "Set" field ever gets cleaned up at the source, no code change
is needed here — the majority vote will simply start agreeing with
itself and the console warnings will disappear.

Long-term option (not implemented, kept as a fallback): replace the
majority-vote label logic with a hard-coded SET_DISPLAY_NAMES map of
the 33 canonical folder -> display-name pairs already listed in this
brief. That removes any dependence on the "Set" field for the
dropdown entirely. Consider this if the source data cannot be fixed.

## Addendum: Cost Boxes, Scoped Search, and Sorting

Three additions were made to index.html after the migration to
narutoccgdatabase.json. All three are self-contained and do not
require any data changes.

### A. Cost Boxes in the Inspector

Two cost layouts changed in renderInspector():

1. Entrance Cost and Hand Cost now render inside a single two-column
   .stat-row box, matching the shape of the Healthy and Injured stat
   boxes. This applies to Ninja, Mission, and Client cards.
   Implementation: statRow('Entrance Cost', fmtNum(ent), 'Hand Cost', fmtNum(hand)).
   The box only renders if at least one of the two values is
   non-blank; a missing side shows "-" inside the box.

2. Jutsu Cost now renders in a full-width single-item box using the
   same .stat-row styling, via the singleBox() helper. It only
   renders when Chakra Cost is non-blank.

Do not revert these to plain <p> rows. The box layout is intentional
and matches the combat/support boxes for visual consistency.

### B. Scoped Search

The header now has two search controls: a text input (#search-input)
and a scope dropdown (#scope-filter). Default scope is "All fields",
which reproduces the previous multi-token AND behavior.

Scope options and their match rules:

| Scope value       | Match rule                                                |
|-------------------|-----------------------------------------------------------|
| ALL               | multi-token AND, each token OR'd across every field below |
| name              | Display Name, substring, case-insensitive                 |
| number            | Collector Number OR Card ID, substring, case-insensitive  |
| type              | exact match against the four Type values, case-insensitive|
| symbols           | Symbols, substring, case-insensitive                      |
| characteristics   | Characteristics, substring, case-insensitive              |
| effectTitle       | Effect Title, substring, case-insensitive                 |
| effectText        | Effect Text, substring, case-insensitive                  |
| keywords          | Keywords, substring, case-insensitive                     |
| combatAttribute   | Combat Attribute, substring, case-insensitive             |
| entranceCost      | exact numeric match if the token parses as a number,      |
|                   | substring fallback otherwise                              |
| handCost          | same rule as entranceCost                                 |
| chakraCost        | Chakra Cost, substring, case-insensitive                  |
| printedName       | Printed Name, substring, case-insensitive                 |

Year and Errata are deliberately NOT searchable fields. Do not add
them without an explicit request.

Multi-token behavior: the raw query is lowercased and split on
whitespace. Every token must match (AND). In "All fields" mode, a
token is considered matched if it matches ANY field (OR across
fields). There is no field-prefix syntax, no scoped operators, and
no debounce. Do not add debounce unless profiling shows a real lag.

The match logic lives in FIELD_MATCHERS and cardMatchesSearch().
Add a new searchable field by adding one entry to FIELD_MATCHERS
and one <option> to #scope-filter with a matching value.

### C. Sort Dropdown

The header now has a #sort-select control. Options and their
semantics:

| Option value             | Behavior                                  |
|--------------------------|-------------------------------------------|
| number-asc (default)     | Collector Number, natural sort, ascending |
| number-desc              | Collector Number, natural sort, descending|
| name-asc                 | Display Name, natural sort, ascending     |
| name-desc                | Display Name, natural sort, descending    |
| entranceCost-asc / -desc | Entrance Cost numeric, direction as shown |
| handCost-asc / -desc     | Hand Cost numeric, direction as shown     |
| healthyCombat-asc / -desc| Healthy Combat numeric, direction as shown|
| healthySupport-asc/-desc | Healthy Support numeric, direction as shown|
| type-asc                 | Type, alphabetical                        |
| setFolder-asc            | Set folder (derived from image_path)      |

Rules baked into the sorter:

- Natural sort via Intl.Collator with numeric:true, so N-2 sorts
  before N-10.
- Nulls always sort last regardless of direction. A card with no
  Entrance Cost is not treated as "cost 0" — it moves to the end.
- Ties always fall back to Collector Number ascending, natural sort.
  This makes the grid order deterministic across renders.
- Default is number-asc, set both as the selected <option> in HTML
  and as the fallback string in getSortSpec().

Do not add a Year sort. Do not add direction toggles separate from
the dropdown — direction is baked into each option value so one
select fully describes the sort.

The sort logic lives in getSortSpec() and makeComparator(). Add a
new sortable field by adding one branch to makeComparator() and
one or two <option> entries to #sort-select.

### Header Layout

The header now contains five filter groups, in this order:
Search, In (scope), Type, Set, Sort. On desktop they wrap into up
to two rows. On mobile (<=820px) each group takes a full row via
the existing 1 1 100% flex rule and the inputs stretch to full
width. Do not reorder these groups without a specific reason; the
current order mirrors the flow of "what am I searching for -> in
which field -> what type -> in which set -> in what order".

## Addendum: TTS Export Zone Separation

Earlier versions of exportToTTS() produced a save where all three
deck zones (Mainboard, Reinforcements, Sideboard) spawned at the
same transform position, so Tabletop Simulator stacked them into a
single visual pile. Users could not tell the zones apart on load.

The exporter now offsets each zone along the X axis:

  Mainboard       -> posX: 0
  Reinforcements  -> posX: 3
  Sideboard       -> posX: 6

All three share posY: 1 and posZ: 0. 3 units is roughly one and a
half card widths at scale 1.25, which gives clean visual separation
without overlap. Zones with zero cards are still omitted entirely
(unchanged behavior).

Implementation detail: createTTSDeckObject() takes an offsetX
argument, and each call site passes 0, 3, or 6. The per-card
Transform inside ContainedObjects is intentionally left at
{posX:0, posY:0, posZ:0} because contained cards inherit the deck
object's transform — only the deck itself needs the offset.

Do NOT reset these offsets to 0. Do NOT stack the three zones on
the same position. If more zones are added later, continue the
pattern (posX: 9 for a fourth zone, etc.).

The TTS save structure (ObjectStates array with DeckCustom entries)
is otherwise unchanged. Card Description remains the lowercased
Card ID. Image URLs and card back URL are unchanged. Existing
exports remain importable.