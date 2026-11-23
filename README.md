<img width="800" height="530" alt="image" src="https://github.com/user-attachments/assets/8ddd5187-dbbc-457e-8a39-7997d0916a03" />


# DB Explorer: Read-Only SQLite Browser & Character Map

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt%20for%20Python-green.svg)](https://doc.qt.io/qtforpython-6/)
[![SQLite](https://img.shields.io/badge/SQLite-read--only-lightgrey.svg)](https://www.sqlite.org/)
[![Languages](https://img.shields.io/badge/UI-ไทย%20%7C%20English-ff5fa2.svg)](#-key-features)

> *"A fast, safe, desktop explorer for large SQLite databases, with a one-page Character Map and XUnity-ready exports for Princess Connect! Re:Dive master data."*

<!-- Add a screenshot here, e.g. ![DB Explorer](assets/screenshot.png) -->


---

## 🔭 Overview

The Princess Connect! Re:Dive master database (`PriconneMasterDatabase_*.db`) holds hundreds of tables. Finding everything about one character usually means opening a generic SQLite tool and hand-writing joins across `unit_data`, `unit_profile`, `skill_data`, `skill_action`, `story_detail`, and more.

**DB Explorer** removes that work. It opens any SQLite file **strictly read-only**, lets you page, filter, search and query every table, and adds a **Character Map** that gathers one character's data from all related tables into a single page, with skill actions decoded into readable damage formulas and effects.

It works with any SQLite database. The Character Map and skill export are tuned for the Priconne master DB schema.

---

## ✨ Key Features

### 1. Safe by Design (Read-Only)
- **Read-only connection**: databases open through a `mode=ro` URI with `PRAGMA query_only=ON`, so the original file can never be modified.
- **Safe SQL console**: only reads are possible, even if you type a write statement.
- **Tolerant decoding**: text is decoded as UTF-8 with replacement, so odd bytes never crash a query.

### 2. Home Dashboard
- Instant stats: **table count, total rows, empty tables, file size**.
- **Global search box** that looks across every table at once.
- **Favorite tables** and **Recently opened** shortcuts (remembered between sessions).
- **Quick cards** for common Priconne tables (`unit_data`, `unit_profile`, `skill_data`, `skill_action`, `enemy_parameter`, `quest_data`, `item_data`, `equipment_data`, `gacha_data`, `unit_rarity`, `clan_battle_period`, `shop_item`) and a list of the **largest tables**.

### 3. Table Browser
- **Server-side paging** at 50 / 100 / 250 / 500 / 1000 rows per page, so huge tables stay responsive.
- **Per-column filter boxes** in the header: `>100`, `=5`, `!=0`, `null`.
- **Search all columns** of the table, with column sorting.
- **Hide empty / 0 columns** to cut the noise in wide tables.
- **Schema tab**: columns, types, PK / NOT NULL / defaults, indexes, and the full `CREATE` statement, plus a one-click **Open in SQL**.
- **Export to CSV** that respects the current filters, search and sort.

### 4. Row Details & Cross-Table Navigation
- Select a row to open the **Row details** panel on the right.
- **Follow a value**: click any column value to list every other table that has the same value in a same-named column (for example, every table that references a given `unit_id`), then jump straight to it.
- Copy any cell with one click.

### 5. SQL Console
- Syntax-highlighted editor, run with **Ctrl + Enter**.
- **Query history** (last 30 queries, saved between sessions).
- Results capped at **5,000 rows** with a truncation notice and execution time.
- **Export results to CSV** (UTF-8 with BOM, ready for Excel).

### 6. Global Search
- Type a name, text or ID (for example `Hiyori` or `100101`) and DB Explorer scans **every non-empty table**, then lists the tables with matches and their row counts.
- Double-click a result to open that table with the search already applied.
- **Quick Find (Ctrl + K)**: a command palette to jump to any table by name.

### 7. Character Map
Type a character name (EN or JP) or a **Unit ID** and get one scrollable page with:

| Section | What you get |
|---|---|
| **Basic info** | Stats and base data from `unit_data` |
| **Profile** | Profile fields, with display overrides when present |
| **Skills** | UB, Skill 1/2, EX and their `+` / `++` evolutions, with every action decoded into a readable formula (damage, heal, buffs, barriers, conditions) |
| **Story** | Story episodes and their love-level bonuses |
| **Comments / Voice** | Unit comments, album voice lines |
| **Room** | Room comments by affection step |
| **Unique equipment** | UE data, enhancement rates, and required items |
| **Related tables** | Every table that holds rows for this unit, with counts |

- Step through characters with **‹ ›** buttons.
- Show **skill icons** by pointing the app at a folder of `icon_skill_*.png` files.

### 8. XUnity Export (JP=EN)
Export a character in the translation-file style used by XUnity.AutoTranslator dictionaries:

- **Profile + Skills** (`AlmondEye.txt` style): `##Profile## ##UB## ##S1## ##S2## ##EX##`, with a dialog to choose which skills, which profile fields, UE text, descriptions, action regex lines, and whether to fill the English text after `=`.
- **Comments / Voice** (`AlmondEye_HS_TH.txt` style): one voice or comment line per line.

### 9. Customization & Comfort
- 🌓 **Dark / Light** themes.
- 🌐 **Thai / English** UI, switchable on the fly.
- **Drag & drop** a `.db` file onto the window; the last opened file reopens on launch.
- **Editable condition names** via `condition_names.json` (see below).

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Description |
|---|---|---|
| **Ctrl + K** | Quick Find | Jump to any table by name |
| **Ctrl + O** | Open File | Open a SQLite `.db` file |
| **Ctrl + W** | Close Tab | Close the current tab |
| **F5** | Reload | Reload the current database |
| **Ctrl + Enter** | Run Query | Execute the SQL in the console |
| **Enter** (in search / Character Map) | Search / Show | Run the search or open the character |
| **Double-click** a row | Row details | Open the details panel for that row |

---

## 🚀 Quickstart

### Prerequisites

- **Python 3.9+** (Windows launchers expect it on `PATH`).
- **PySide6**:

  ```bash
  pip install PySide6
  ```

### Launching DB Explorer

Double-click **`run_DBExplorer.bat`** (auto-detects `py` / `python` and installs PySide6 if missing), or run:

```bash
python dbexplorer_app.py
```

Open a database directly from the command line:

```bash
python dbexplorer_app.py "DB\PriconneMasterDatabase_10071700.db"
```

…or just drag a `.db` file onto the window.

> **Note:** the master database and game icons are **not** included in this repository. Place your own `.db` file in the `DB/` folder (or anywhere) and open it.

### Building a standalone `.exe`

Run **`CreateEXE.bat`**. It installs PySide6 and PyInstaller, then builds a single-file windowed executable:

```bash
python -m PyInstaller --noconsole --onefile --name DBExplorer dbexplorer_app.py
```

The result is written to `dist\DBExplorer.exe`.

### Optional: Skill Icons

To show skill icons in the Character Map, put the `icon_skill_*.png` files in a `skill/` folder next to the app (or choose a folder from the **🖼 Skill icon folder…** button). Without icons the app still works normally.

### Optional: Custom Condition Names

Some skill actions are conditions identified only by a numeric code. Edit **`condition_names.json`** (keep it next to `dbexplorer_app.py`) to give them readable labels:

```json
{
  "28:741": "Your label here",
  "45:1": { "th": "ชื่อภาษาไทย", "en": "English label" }
}
```

Keys are `"<action_type>:<code>"` (or just `"<code>"`). Values are plain text or a `{ "th": ..., "en": ... }` object. The grey `[T28 · 741]` tag shown on each condition row tells you the exact key to use.

---

## 📁 Project Structure

```
DB-Explorer/
├── dbexplorer_app.py        # Main PySide6 application (UI, DB layer, Character Map, exports)
├── condition_names.json     # Editable names for skill condition codes
├── run_DBExplorer.bat       # Launcher: auto-detects Python, installs PySide6, starts the app
├── Open.bat                 # Minimal launcher (pythonw)
├── CreateEXE.bat            # Builds dist\DBExplorer.exe with PyInstaller
├── DBExplorer.spec          # PyInstaller spec
├── DB/                      # Put your .db files here (not tracked)
└── skill/                   # Optional skill icons: icon_skill_*.png (not tracked)
```

---

## 🧩 How It Works

| Layer | Role |
|---|---|
| `DB` | Read-only connection, paging, WHERE-builder for filters/search, CSV export, schema, SQL runner, global search, `char_map()` aggregation, cross-table reference lookup |
| `Task` (`QThread`) | Runs queries off the UI thread so the window never freezes |
| `PageModel` / `Grid` | Lightweight table model and view for large result sets |
| `decode_action()` | Turns raw `skill_action` rows into readable names, formulas and durations |
| `CharTab` | Renders the Character Map and drives the XUnity exports |

---

## ⚖️ License & Disclaimer

Add a `LICENSE` file of your choice before publishing.

Princess Connect! Re:Dive, its characters, database contents and icons are trademarks and copyright of Cygames, Inc. This is an unofficial fan tool and is not affiliated with or endorsed by Cygames. Game data and assets are not distributed with this project.
