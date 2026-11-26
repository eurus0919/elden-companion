"""AI-first, strictly read-only Elden Ring save briefing.

Aggregates character stats, loadout, memorized spells, world/boss progression,
and save health into a single clean, English-keyed JSON payload designed for
LLM / Agent consumption.
"""

import struct

from .. import risk as riskmod
from ..core import gaitem, items_db
from ..core.profiles import roster
from ..core.slots import Slot
from ..diag import run_diagnostics
from .spells import _magic as magic_table
from .spells import equipped as spells_equipped
from .stats import STAT_NAMES
from .world import view as world_view

SCHEMA_VERSION = "1.0"

_NOISE_BOSS_PREFIXES = (
    "Boss defeated —",
    "Divine Tower —",
)
_NOISE_BOSS_SUBSTRS = (
    "(DLC reserved slot)",
)

_ZONE_PREFIX = {
    "weapon": (0x00000000,),
    "ammo": (0x00000000,),
    "armor": (0x10000000,),
    "talisman": (0x20000000,),
}


def _slot_zone(k):
    if 0 <= k <= 5:
        return "weapon"
    if 6 <= k <= 11:
        return "ammo"
    if 12 <= k <= 16:
        return "armor"
    return "talisman"


def _resolve_equipped_name(zone, iid, gid):
    """Resolve an equipped item name prioritizing its slot category prefix.

    Avoids cross-category ID collisions (e.g. an armor piece colliding with a
    weapon ID when raw item_id is checked first).
    """
    prefixes = list(_ZONE_PREFIX.get(zone, (0x00000000,)))
    fallback = [0x00000000, 0x10000000, 0x20000000, 0x40000000, 0x80000000]
    for p in fallback:
        if p not in prefixes:
            prefixes.append(p)

    raw_ids = [iid]
    if gid is not None and gid != iid:
        raw_ids.append(gid)

    for prefix in prefixes:
        for val in raw_ids:
            cand = (val & 0x0FFFFFFF) | prefix
            if cand:
                nm, _cat = items_db.resolve(cand)
                if nm:
                    return nm
    return f"Unknown (0x{iid:08X})"


def _read_loadout(save, slot_idx, s):
    ids = list(struct.unpack_from("<22I", s.raw, s.offsets["item_ids"]))
    hs = list(struct.unpack_from("<22I", s.raw, s.offsets["ga_handles"]))
    entries, _ = gaitem.walk(s.raw, s.version, expect_end=s.offsets["pgd"])
    by_handle = {e["handle"]: e for e in entries if e["handle"]}

    weapons, ammo, armor, talismans = [], [], [], []
    for k, (iid, h) in enumerate(zip(ids, hs)):
        if iid in (0, 0xFFFFFFFF):
            continue
        zone = _slot_zone(k)
        gid = by_handle[h]["item_id"] if h in by_handle else None
        name = _resolve_equipped_name(zone, iid, gid)
        if zone == "weapon":
            if name == "Unarmed":
                continue
            hand = "right" if k % 2 == 1 else "left"
            weapons.append({"slot": k, "hand": hand, "name": name})
        elif zone == "ammo":
            ammo.append(name)
        elif zone == "armor":
            armor.append(name)
        else:
            talismans.append(name)

    spells_raw = spells_equipped(save, slot_idx)["spells"]
    mtab = magic_table()
    spells = []
    for sp in spells_raw:
        if sp["empty"]:
            continue
        base_id = (sp["id"] or 0) & 0x0FFFFFFF
        meta = mtab.get(base_id)
        spells.append({
            "name": sp["name"],
            "kind": meta["kind"] if meta else "unknown",
        })

    return {
        "weapons": weapons,
        "ammo": ammo,
        "armor": armor,
        "talismans": talismans,
        "spells": spells,
    }


def _is_noise_boss(name):
    if name.startswith(_NOISE_BOSS_PREFIXES):
        return True
    return any(sub in name for sub in _NOISE_BOSS_SUBSTRS)


def _read_progress(save, slot_idx, s, include_boss_locations=True):
    bosses_raw = [
        row
        for row in world_view(save, slot_idx, "boss_defeat", limit=200)["entries"]
        if not _is_noise_boss(row["name"])
    ]
    defeated = []
    remaining = []
    for row in bosses_raw:
        if row["value"]:
            defeated.append(row["name"])
        else:
            if include_boss_locations and row.get("desc"):
                remaining.append({"name": row["name"], "location": row["desc"]})
            else:
                remaining.append(row["name"])

    gr_raw = world_view(save, slot_idx, "great_rune", limit=50)["entries"]
    great_runes_on = [r["name"] for r in gr_raw if r["value"]]
    great_runes_off = [r["name"] for r in gr_raw if not r["value"]]

    maps_raw = world_view(save, slot_idx, "map_fragment", limit=50)["entries"]
    maps_on = sum(1 for r in maps_raw if r["value"])

    endings_raw = world_view(save, slot_idx, "ending", limit=20)["entries"]
    endings_on = [r["name"] for r in endings_raw if r["value"]]

    ng_raw = world_view(save, slot_idx, "ng_cycle", limit=20)["entries"]
    ng_on = [r["name"] for r in ng_raw if r["value"]]

    return {
        "bosses": {
            "defeated_count": len(defeated),
            "total_count": len(bosses_raw),
            "defeated": defeated,
            "remaining": remaining,
        },
        "great_runes": {
            "acquired": great_runes_on,
            "remaining": great_runes_off,
        },
        "map_fragments": {
            "acquired_count": maps_on,
            "total_count": len(maps_raw),
        },
        "endings_triggered": endings_on,
        "ng_cycles_flags": ng_on,
    }


def _pick_default_slot(save, r):
    active = [row for row in r if row["used"]]
    if not active:
        raise ValueError("no active character slots found in this save file")
    best = max(active, key=lambda x: (x.get("seconds", 0), x.get("level", 0)))
    return best["slot"]


def build_brief(save, slot_idx=None, include_path=False, include_boss_locations=True):
    """Build a strictly read-only, AI-friendly JSON dict for a save slot."""
    r = roster(save)
    active_slots = [
        {
            "slot": row["slot"],
            "name": row["name"],
            "level": row["level"],
            "hours": round(row["seconds"] / 3600, 1),
        }
        for row in r
        if row["used"]
    ]

    if slot_idx is None:
        slot_idx = _pick_default_slot(save, r)

    s = Slot(save, slot_idx)
    if s.is_empty:
        raise ValueError(f"slot {slot_idx} is empty")
    prof = r[slot_idx]
    if not s.parse(prof["name"], prof["level"]):
        raise ValueError(f"slot {slot_idx} could not be parsed: {s.reason}")

    ch = s.character()
    stats_map = dict(zip(STAT_NAMES, ch["stats"]))

    md5_rows = save.section_md5_status()
    md5_ok_n = sum(1 for m in md5_rows if m["ok"])
    md5_total = len(md5_rows)

    findings = run_diagnostics(save)
    slot_diags = [
        {"level": f.level, "code": f.code, "slot": f.slot}
        for f in findings
        if f.slot in (None, slot_idx)
    ]

    risk_rep = riskmod.scan(save, only_slot=slot_idx)
    verdict = str(risk_rep.get("verdict", "green")).upper()

    save_info = {
        "file_name": save.path.name,
        "md5_ok": md5_ok_n == md5_total,
        "md5_sections": f"{md5_ok_n}/{md5_total}",
        "risk_level": verdict,
        "modified_by_rezur": bool(risk_rep.get("journal", {}).get("modified")),
        "active_slots": active_slots,
    }
    if include_path:
        save_info["path"] = str(save.path)

    return {
        "schema_version": SCHEMA_VERSION,
        "save": save_info,
        "character": {
            "slot": slot_idx,
            "name": ch["name"],
            "level": ch["level"],
            "hours_played": round(ch["seconds"] / 3600, 1),
            "runes_held": ch["runes"],
            "runes_memory": ch["runes_memory"],
            "stats": stats_map,
            "map_id": ch["map_name"],
            "last_rested_grace_id": s.last_rested_grace,
            "torrent_state": ch["horse"]["state_name"],
            "patch_base": ch["patch"]["version"],
            "diagnostics": slot_diags,
        },
        "build": _read_loadout(save, slot_idx, s),
        "progress": _read_progress(
            save, slot_idx, s, include_boss_locations=include_boss_locations
        ),
    }
