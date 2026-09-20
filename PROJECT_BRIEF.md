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
- JSON for card data and set metadata.

## File Layout (project root)

    naruto-ccg-deckbuilder/
    ├── index.html                    the app (single file: HTML+CSS+JS)
    ├── cards.json                    canonical card database (site reads this)
    ├── sets.json                     set display names + dropdown order
    ├── cardback.webp                 card back for Tabletop Simulator export
    ├── list_images.py                walks cards_database/ to cards_from_images.json
    ├── merge_cards.py                merges images + exports/card_database.json to cards.json
    ├── compress.py                   (legacy) image compression pipeline
    ├── run_pipeline.py               (legacy) driver script
    ├── sync_sheets.py                (legacy) Google Sheets sync
    ├── update_database_from_scraped.py (legacy) scrape to DB script
    ├── cards_from_images.json        output of list_images.py
    ├── cards.json.backup             auto-backup written by merge_cards.py
    ├── missing_data.json             (optional) cards needing manual data
    ├── cards_database/               ALL card images, one folder per set
    ├── exports/
    │   └── card_database.json        rich card data source (names, stats, effects)
    ├── incoming_cards/               staging (not used by the site)
    ├── scraped_naruto_cards.json     raw scrape (not used by the site)
    └── .processed_manifest.json      pipeline bookkeeping

## Canonical Card Schema (cards.json)

Every card has exactly these fields:

| Field | Type | Notes |
|---|---|---|
| cardnumber | string | Lowercase. e.g. n370, pr005ra, ex001 |
| name | string | Display name, no trailing card number |
| cardtype | string | Ninja / Jutsu / Mission / Client / blank |
| setfolder | string | Folder under cards_database/, no dots |
| imgname | string | Filename only, lowercase |
| set | string | Display name (legacy; site prefers sets.json) |
| entrancecost | string | Empty for Jutsu |
| handcost | string | Empty for Jutsu |
| symbol | string | e.g. Fire, Fire/Water |
| combath | string | Healthy combat |
| supporth | string | Healthy support |
| combati | string | Injured combat |
| supporti | string | Injured support |
| attribute | string | "Combat Attribute" in the UI |
| effect | string | Card text; may contain <br> |
| jutsucost | string | Jutsu cost string, e.g. "L L 1" |
| rarity | string | |
| flavor | string | Italic quote in the inspector |
| characteristics | string | e.g. "Leaf / Genin / Male / Growth" |

Do not rename fields. index.html references them directly.

## Image Path Convention

index.html builds URLs like:

    ./cards_database/{setfolder}/{imgname}

Rules:
- All images live under cards_database/
- One subfolder per set
- Filenames are lowercase and match imgname exactly
- GitHub Pages is case-sensitive. If imgname says N370.webp but the
  file is n370.webp, the image will 404 on the live site even if
  it works locally.

## Set Folders (canonical list)

Folder keys must match exactly. Dots are removed from folder names
(set_17.5 becomes set_175) even though the display name keeps the dot.

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
| promos | Promos |

sets.json is the authoritative list for the dropdown order (array,
top-to-bottom).

## Card Type Rules (from cardnumber prefix)

Used by merge_cards.py when the DB doesn't specify a type:

| Prefix | Type |
|---|---|
| n, nus | Ninja |
| j, jus | Jutsu |
| m, mus | Mission |
| c, cus | Client |
| p, pr, prus, ps | Unknown — promos, manual entry required |

Suffix letters on card numbers:
- e (errata), a (alt art), r, ra — same data as base card
- b — legit separate card, do not fall back

merge_cards.py walks backward stripping e/a/r until it finds a
non-stub entry. It never strips b.

## Data Pipeline

Run from the project root:

### 1. Rebuild image list

    python list_images.py

Walks cards_database/, writes cards_from_images.json.
Run this any time you add, remove, or rename card images.

### 2. Merge with rich card data

    python merge_cards.py

Reads cards_from_images.json + exports/card_database.json,
writes cards.json (backing up the old one to cards.json.backup).

Rules the merge enforces:
- cardtype guessed from prefix if DB doesn't provide one
- Jutsu cards get blank entrancecost / handcost
- Card name has any trailing card number stripped
- Suffixed variants (e, a, r, ra) inherit data from their base card
- b-suffix cards are kept independent
- setfolder dots stripped to match disk folders

### 3. Commit and push

    git add .
    git commit -m "describe what changed"
    git push

## What index.html Reads

- fetch('cards.json')    card data
- fetch('sets.json')     set dropdown order + display names
- Image URLs built from cards_database/{setfolder}/{imgname}

No build step. Open with Live Server, or git push for GitHub Pages
to pick it up.

## Known Issues / TODO

- ~129 promo cards (p prefix) have no cardtype — manual entry needed
- ~217 cards had no matching data in exports/card_database.json
  during the last merge — they display with their cardnumber as the
  name and blank stats
- exports/card_database.json contains stub entries (name equals
  card_number, all fields empty) for some variants. merge_cards.py
  treats these as misses and looks up the base card instead. If the
  base is missing too, the entry is written blank.

## Rules for AI Assistants Working on This Project

1. Never rename fields in cards.json. index.html references them.
2. Never add dots to setfolder values. Disk folders have no dots.
3. Never assume case-insensitive paths. GitHub Pages is case-sensitive.
4. Ask before restructuring the pipeline. list_images.py and
   merge_cards.py are the two scripts that matter. The other Python
   files are legacy.
5. Test in a browser after every change. The site should still filter,
   build decks, and export.
6. Commit working states before making risky changes.