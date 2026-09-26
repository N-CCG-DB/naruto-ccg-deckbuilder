================================================================================
PROJECT HANDOFF — NARUTO CCG CARD DATABASE
================================================================================

--------------------------------------------------------------------------------
OVERVIEW
--------------------------------------------------------------------------------

This document summarizes work done to build a master card database for a Naruto
Collectible Card Game (CCG) web/digital project. It describes the input files,
the transformations applied, the final file structure, and known issues so that
a future AI assistant (or developer) can pick up work without re-deriving
everything.

--------------------------------------------------------------------------------
PROJECT GOAL
--------------------------------------------------------------------------------

Build a single, authoritative JSON file (narutoccgdatabase.json) containing
every card in the game, with each card's full metadata AND a path to its scanned
image. This file will drive a card browser / deck builder / whatever the
frontend ends up being.

--------------------------------------------------------------------------------
INPUT FILES
--------------------------------------------------------------------------------

1) NarutoCCG Master Database.xlsx

   An Excel workbook (multiple sheets — one sheet per card set) containing the
   canonical card metadata. Column headers include:

     Card ID, Collector Number, Printed Name, Display Name, Type, Set, Year,
     Symbols, Entrance Cost, Hand Cost, Healthy Combat, Healthy Support,
     Injured Combat, Injured Support, Combat Attribute, Chakra Cost,
     Characteristics, Effect Title, Effect Text, Keywords, Errata

   Notes:
   - Some cells contain real line breaks (from Alt+Enter in Excel). These are
     preserved through the pipeline and appear as \n in the JSON.
   - Many cells are empty (NaN when read by pandas). These should become null
     in the JSON, NOT the literal token NaN (which is invalid JSON).

2) cards.json

   A separate JSON file containing image scan data for each physical card.
   Structure (one entry):

     {
       "cardnumber": "ex001",
       "name": "Naruto Uzumaki",
       "cardtype": "Ninja",
       "setfolder": "promos",
       "imgname": "ex001.webp",
       "set": "Promos",
       "image_path": "promos/ex001.webp",
       "entrancecost": "0",
       "handcost": "0",
       "symbol": "Lightning",
       "combath": "1",
       "supporth": "0",
       "combati": "3",
       "supporti": "0",
       "attribute": "Oil",
       "effect": "",
       "jutsucost": "",
       "rarity": "",
       "flavor": "",
       "characteristics": "Leaf/Genin/Male/Growth"
     }

   The ONLY field we care about from this file is image_path, keyed by
   cardnumber.

   Approximately 4,284 entries exist in cards.json.

--------------------------------------------------------------------------------
OUTPUT FILE
--------------------------------------------------------------------------------

narutoccgdatabase.json
(final, renamed from "NarutoCCG Master Database (with images).json")

Top-level structure: a dict keyed by sheet name, each value an array of card
objects.

  {
    "Promo Cards": [ { ...card... }, ... ],
    "01 Path to Hokage": [ ... ],
    "02 Coils of the Snake": [ ... ],
    ...
    "28 Ultimate Ninja Storm 3": [ ... ]
  }

Each card object is the Master DB row plus an injected image_path field (placed
at the END of the object):

  {
    "Card ID": "ex001",
    "Collector Number": "EX-001",
    "Printed Name": "Naruto Uzumaki",
    ...
    "Keywords": "GROWTH",
    "Errata": null,
    "image_path": "promos/ex001.webp"
  }

MATCH RATE: 4405 / 4406  (99.98%)

--------------------------------------------------------------------------------
THE ID MATCHING PROBLEM
--------------------------------------------------------------------------------

The two files use different ID schemes for the same cards. Bridging them was
the core of this work.

Master DB (Card ID) vs cards.json (cardnumber) mapping rules:

  Master Card ID suffix     cards.json cardnumber suffix
  ---------------------     -----------------------------
  (none)                    (none) — direct match
  _alt                      a
  _errata                   e
  _alt_errata               ae
  _promo                    a  (ambiguous with _alt)
  _original                 a or plain base

Additional complications discovered:

1) Case mismatches. The Master DB uses uppercase region codes (nUS001, jUS001,
   mUS001, nC001, cUS001, etc.), while cards.json stores them lowercase
   (nus001, jus001, ...). Fix: lowercase both sides before comparing.

2) Plain cards in Master DB with only suffixed variants in cards.json.
   Example: Master has n024 but cards.json only has n024e.
   Resolution: probe the base ID with common suffixes
   ("e", "a", "ae", "be", "bea", "b", "ba", "ra", "rae", "r", "re").

3) _alt → plain fallback.
   Example: nus010_alt in Master corresponds to nus010 (no suffix) in cards.json
   because no _alt variant image exists.

4) "r" suffix (reprint).
   Example: Master pr005r → cards.json pr005rae.
   Handled with a dedicated probe branch.

5) Bare "b" suffix (alt-art variant b).
   Example: Master n1272b → cards.json has only n1272 (no "b" variant).
   Resolution: fall back to the plain base image.

6) "bea" combined suffix.
   Example: Master n371b → cards.json n371bea.
   Added to the probe list.

--------------------------------------------------------------------------------
CONVERSION PIPELINE
--------------------------------------------------------------------------------

The full pipeline is two scripts, run in order.

SCRIPT 1 — Excel → JSON
-----------------------

Reads the Excel workbook, one sheet per key, writes
"NarutoCCG Master Database.json".

Key details:
- pd.read_excel(..., sheet_name=None) returns all sheets as
  {sheet_name: DataFrame}.
- Must replace NaN with None AFTER casting the DataFrame to object dtype
  (otherwise pandas re-casts None back to NaN for float columns).
- json.dump(..., allow_nan=False) should be passed so that any escaping NaN
  raises an error instead of silently producing invalid JSON.
- indent=2, ensure_ascii=False, default=str are used for readable output that
  preserves non-ASCII characters and can serialize Timestamp/Decimal values.
- Effect Text line breaks are preserved — the \n characters in the JSON are
  real newlines, needed for multi-line display in the UI.

SCRIPT 2 — Image path injection
-------------------------------

Reads cards.json and the Master DB JSON, builds a lowercased
cardnumber → image_path lookup, then walks every card in the Master DB,
resolves its Card ID to a cards.json key using the matching rules above, and
injects image_path.

The matching function tries candidates in PRIORITY ORDER:

  1. Suffix-aware translation (_alt → a, _errata → e, etc.)
  2. The ID itself (exact match, lowercased)
  3. Base ID with each known suffix
     ("", "e", "a", "ae", "be", "bea", "b", "ba", "ra", "rae", "r", "re")
  4. Special "r" handling
  5. Special bare-"b" fallback

Each card gets the FIRST candidate that exists in the lookup. If none match,
image_path is set to null and the Card ID is added to a report list.

--------------------------------------------------------------------------------
SUGGESTED NEXT STEPS / THINGS TO KNOW
--------------------------------------------------------------------------------

- Re-runnability: Script 2 always reads the ORIGINAL
  "NarutoCCG Master Database.json" and writes a fresh output. Safe to re-run
  after any fix without corrupting state.

- If the Excel is updated: Re-run Script 1 first to regenerate the Master DB
  JSON, then re-run Script 2.

- If cards.json is updated with new images: Just re-run Script 2.

- Case sensitivity: All key comparisons are done lowercased. This was essential
  for the US/C region cards.

- image_path placement: Currently last in each card object. If order matters
  for the frontend, the injection code can be modified to insert it right after
  Card ID by rebuilding each dict in a custom order.

- Data shape: The top-level is a dict of {sheet_name: [cards]}. If a flat array
  of all cards (with a "set" field instead) is preferred, a small
  post-processing pass can flatten it.

- Filenames:
    Final file:        narutoccgdatabase.json
    Intermediate file: NarutoCCG Master Database.json
    Source image data: cards.json
    Original workbook: NarutoCCG Master Database.xlsx

--------------------------------------------------------------------------------
FILE INVENTORY (what should exist in the project folder)
--------------------------------------------------------------------------------

  FILE                                   PURPOSE                          STATUS
  ------------------------------------   ------------------------------   ----------------
  NarutoCCG Master Database.xlsx         Source metadata                  Original (do not edit)
  cards.json                             Source image paths               Original (do not edit)
  NarutoCCG Master Database.json         Intermediate: Excel → JSON       Regenerable
  narutoccgdatabase.json                 FINAL OUTPUT (DB + image paths)  Primary artifact
  excel_to_json.py                       Script 1                         Keep
  inject_images.py                       Script 2                         Keep

--------------------------------------------------------------------------------
QUICK-START FOR A NEW AI SESSION
--------------------------------------------------------------------------------

If you are an AI assistant reading this to onboard:

  1. The project is a Naruto CCG card database.

  2. The main artifact is narutoccgdatabase.json — a dict of
     {set_name: [card_objects]}, each card having full metadata plus an
     image_path.

  3. The source files are "NarutoCCG Master Database.xlsx" (metadata) and
     cards.json (image paths).

  4. The two ID schemes differ in non-obvious ways — see THE ID MATCHING
     PROBLEM section above before writing any code that joins them.

  5. image_path: null means the card has no scan available. Only j162 currently
     falls into this category.

  6. If asked to modify the data, prefer writing new scripts that read the
     source files and regenerate the output, rather than editing
     narutoccgdatabase.json in place — this keeps the pipeline reproducible.

  7. Effect text uses real \n characters for multi-line display — preserve them.

================================================================================
END OF DOCUMENT
================================================================================