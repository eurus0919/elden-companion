# Elden Companion CLI (Rezur AI-First Fork)

An **AI-first, zero-dependency CLI & Agent Skill** for **Elden Ring** (PC / Steam `ER0000.sl2`), built on top of the [Rezur Saves Configurator](https://github.com/Rezurmas/rezur) binary save engine.

Instead of another GUI save editor, this project turns your local `ER0000.sl2` into a **single, stateless, strictly read-only JSON briefing** + a drop-in **`SKILL.md` (`elden-companion`)**—so your AI assistant can instantly read your real build, boss progress, and exploration state and chat with you right after a session.

- **100% offline & read-only by default**: `python -m rezur brief` never writes to your save file or config.
- **Zero third-party dependencies**: runs on pure Python standard library (`>= 3.10`).
- **One command = full context**: character stats, weapons/armor/talismans/spells, defeated & remaining bosses, great runes, map fragments, and save health in one English-keyed JSON payload.
- **Privacy-conscious**: hides your full OS path and SteamID by default.
- **Agent-ready**: ships with [`skills/elden-companion/SKILL.md`](skills/elden-companion/SKILL.md) for any Agent / IDE / CLI that supports `SKILL.md`.

---

## Quick Start

```bash
git clone https://github.com/eurus0919/elden-companion.git
cd elden-companion

# Pretty-printed JSON briefing (auto-detects newest %APPDATA%\EldenRing\*\ER0000.sl2)
python -m rezur brief

# Compact single-line JSON (lowest token usage for AI Agents)
python -m rezur brief --compact

# Target a specific character slot or save file
python -m rezur brief --slot 0 --save "C:\path\to\ER0000.sl2"
```

---

## Using the `elden-companion` Skill

Copy or symlink [`skills/elden-companion`](skills/elden-companion) into your Agent's skills directory (for example, `.gemini/skills/`, `.claude/skills/`, or your workspace skills folder), then invoke it whenever you finish playing Elden Ring:

> `/elden-companion` — *"Just finished a session, what's left on my run?"*

The skill instructs the AI to:
1. Run `python -m rezur brief --compact` (strictly read-only).
2. Read your current build, level, playtime, and unkilled bosses.
3. Respond like a natural gaming companion instead of dumping raw JSON.


---

## Example Output (`python -m rezur brief`)

```json
{
  "schema_version": "1.0",
  "save": {
    "file_name": "ER0000.sl2",
    "md5_ok": true,
    "md5_sections": "12/12",
    "risk_level": "GREEN",
    "modified_by_rezur": false,
    "active_slots": [
      { "slot": 0, "name": "Tarnished", "level": 150, "hours": 75.0 }
    ]
  },
  "character": {
    "slot": 0,
    "name": "Tarnished",
    "level": 150,
    "hours_played": 75.0,
    "runes_held": 124500,
    "runes_memory": 8322279,
    "stats": {
      "vigor": 50,
      "mind": 30,
      "endurance": 25,
      "strength": 22,
      "dexterity": 15,
      "intelligence": 10,
      "faith": 60,
      "arcane": 17
    },
    "map_id": "m15_00_00_00",
    "torrent_state": "INACTIVE",
    "diagnostics": []
  },
  "build": {
    "weapons": [
      { "slot": 0, "hand": "left", "name": "Godslayer's Seal +7" },
      { "slot": 1, "hand": "right", "name": "Blasphemous Blade +10" }
    ],
    "armor": ["Tree-and-Beast Surcoat", "Malformed Dragon Gauntlets"],
    "talismans": ["Shard of Alexander", "Fire Scorpion Charm", "Ritual Sword Talisman"],
    "spells": [
      { "name": "Golden Vow", "kind": "incantation" },
      { "name": "Flame, Grant Me Strength", "kind": "incantation" }
    ]
  },
  "progress": {
    "bosses": {
      "defeated_count": 32,
      "total_count": 48,
      "remaining": [
        { "name": "Dragonlord Placidusax", "location": "Crumbling Farum Azula" },
        { "name": "Malenia, Blade of Miquella", "location": "Miquella's Haligtree" }
      ]
    },
    "great_runes": {
      "acquired": ["Godrick's Great Rune", "Radahn's Great Rune"],
      "remaining": ["Malenia's Great Rune"]
    },
    "map_fragments": { "acquired_count": 18, "total_count": 19 }
  }
}
```

---

## CLI Options (`brief`)

| Flag | Description |
|---|---|
| `--save PATH` | Explicit path to `ER0000.sl2` (defaults to newest Steam save under `%APPDATA%\EldenRing`) |
| `--slot N` | Character slot `0..9` (defaults to the most-played active character) |
| `--compact` | Single-line minified JSON for minimal LLM token usage |
| `--include-path` | Include the full local save file path in `save.path` |
| `--no-boss-locations` | Return remaining boss names as plain strings without location descriptions |

---

## Upstream Engine & Credits

This repository is built on top of **[Rezur Saves Configurator](https://github.com/Rezurmas/rezur)** (MIT License), which provides the byte-verified `.sl2` parser, checksum verification, diagnostics, and full CLI/GUI editing engine. All original `rezur` subcommands (`info`, `doctor`, `fix`, `backups`, `risk`, etc.) remain intact—run `python -m rezur --help` to see them.

Game names, text, and content belong to **FromSoftware / Bandai Namco**. This is an unofficial hobby tool for your own save files.
