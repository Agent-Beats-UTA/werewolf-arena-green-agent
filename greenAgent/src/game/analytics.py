from __future__ import annotations

from typing import Any, Dict
from collections import defaultdict

from src.game.GameData import GameData
from src.models.enum.EliminationType import EliminationType


def _word_count(text: str) -> int:
    if not text:
        return 0
    return len(text.strip().split())


def compute_game_analytics(state: GameData) -> Dict[str, Any]:
    """
    Compute end-of-game analytics from GameData.
    Returns JSON-serializable dict for DataPart.
    """

    # Determine rounds played 
    round_keys = set()
    round_keys.update(getattr(state, "events", {}).keys())
    round_keys.update(getattr(state, "bids", {}).keys())
    round_keys.update(getattr(state, "chat_history", {}).keys())
    round_keys.update(getattr(state, "eliminations", {}).keys())
    rounds_played = max(round_keys) if round_keys else getattr(state, "current_round", 1)

    # Average bid per agent
    bid_sum = defaultdict(int)
    bid_cnt = defaultdict(int)
    for bids in getattr(state, "bids", {}).values():
        for b in bids:
            pid = getattr(b, "participant_id", None)
            amt = getattr(b, "amount", None)
            if pid is None or amt is None:
                continue
            bid_sum[pid] += int(amt)
            bid_cnt[pid] += 1
    avg_bid_per_agent = {pid: bid_sum[pid] / bid_cnt[pid] for pid in bid_cnt}

    # Average word count per agent
    words_sum = defaultdict(int)
    msg_cnt = defaultdict(int)
    for msgs in getattr(state, "chat_history", {}).values():
        for m in msgs:
            sid = getattr(m, "sender_id", None)
            content = getattr(m, "content", "")
            if sid is None:
                continue
            words_sum[sid] += _word_count(content)
            msg_cnt[sid] += 1
    avg_words_per_agent = {pid: words_sum[pid] / msg_cnt[pid] for pid in msg_cnt}

    # Seer checks (if being recorded)
    seer_checks_raw = getattr(state, "seer_checks", []) or []
    seer_checks = []
    for item in seer_checks_raw:
        try:
            checked_player, is_wolf = item
            seer_checks.append({"checked_player": checked_player, "is_werewolf": bool(is_wolf)})
        except Exception:
            continue
    seer_found_werewolf = any(x["is_werewolf"] for x in seer_checks)

    # Werewolf kills (proxy metric)
    werewolf_kills = 0
    for elims in getattr(state, "eliminations", {}).values():
        for e in elims:
            if getattr(e, "elimination_type", None) == EliminationType.NIGHT_KILL:
                werewolf_kills += 1

    winner = getattr(state, "winner", None)

    return {
        "winner": winner,
        "rounds_played": rounds_played,
        "avg_bid_per_agent": avg_bid_per_agent,
        "avg_words_per_agent": avg_words_per_agent,
        "seer_checks": seer_checks,
        "seer_found_werewolf": seer_found_werewolf,
        "werewolf_kills": werewolf_kills,
    }


def render_summary_text(analytics: Dict[str, Any]) -> str:
    return (
        "Game complete.\n"
        f"- Winner: {analytics.get('winner', 'unknown')}\n"
        f"- Rounds played: {analytics.get('rounds_played', '?')}\n"
        f"- Werewolf kills: {analytics.get('werewolf_kills', 0)}\n"
        f"- Seer found werewolf: {analytics.get('seer_found_werewolf', False)}\n"
    )
