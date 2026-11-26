---
name: elden-companion
description: Read the user's local Elden Ring PC/Steam save (ER0000.sl2) in strictly read-only mode via `python -m rezur brief --compact` and talk naturally about their build, progress, remaining bosses, and next steps.
---

# Elden Companion

Use this skill whenever the user wants to chat about their Elden Ring run, review their current build, check which bosses or regions they still have left, or debrief right after a play session.

## Rules

1. **Strictly read-only by default.** Only run `python -m rezur brief`. Never invoke write commands (`--apply`, `fix`, `stats --set`, `item --add`, `unlock`, `clear`, etc.) unless the user explicitly asks to modify their save file.
2. **One call is enough.** `python -m rezur brief --compact` already returns character stats, loadout, memorized spells, boss progress (defeated + remaining), great runes, map fragments, and save health in one JSON payload.
3. **Privacy-first.** Do not expose the user's SteamID or full OS path unless they specifically ask for it.
4. **Talk like a companion, not a JSON dumper.** Never recite the raw JSON line by line. Pick out the interesting hooks—their weapon/talisman synergy, notable unkilled bosses, hours played, runes held, or an unvisited region—and start a natural conversation.

## Command

Run from the repository root (auto-detects the newest `%APPDATA%\EldenRing\*\ER0000.sl2`):

```bash
python -m rezur brief --compact
```

Optional flags:
- `--slot N` — inspect a specific character slot (0–9). Defaults to the most-played active character.
- `--save PATH` — inspect a specific `ER0000.sl2` file.
- `--no-boss-locations` — omit boss location hints for an even smaller JSON payload.

## How to Use the Briefing

After running `python -m rezur brief --compact`, synthesize the payload into a conversational response:
- **Build read**: notice their stat spread (e.g. high Faith + Blasphemous Blade + Fire Scorpion Charm = Fire/Faith build) and comment on synergies or missing pieces if they ask.
- **Progress read**: highlight how many bosses they've cleared (`progress.bosses.defeated_count / total_count`) and call out 2–3 standout unkilled bosses from `progress.bosses.remaining` (like Malenia, Placidusax, etc.) as natural next targets.
- **Health check**: only mention `save.md5_ok`, `save.risk_level`, or `character.diagnostics` if something actually needs attention (e.g. Torrent hang bug or non-green risk).

