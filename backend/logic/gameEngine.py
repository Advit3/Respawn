"""
RESPAWN – CORE GAME LOGIC ENGINE

This file contains all core logic:
- Stats calculation
- Buffs & debuffs
- Quest generation
- Boss evaluation

This works independently of UI & backend.
"""

# -------------------------------
# CONFIG & CONSTANTS
# -------------------------------

STAT_MIN = 0
STAT_MAX = 100

BASE_STATS = {
    "health": 50,
    "energy": 50,
    "focus": 50,
    "resilience": 50,
}

# how many bad days in a row before a boss appears
BOSS_TRIGGER_DAYS = 2

# XP config
XP_DAILY_LOG = 10
XP_QUEST_COMPLETION = 5

def clamp(value, min_value=STAT_MIN, max_value=STAT_MAX):
    return max(min_value, min(value, max_value))


def calculate_stats(daily_input):
    stats = BASE_STATS.copy()

    # -----------------
    # Inputs with limits
    # -----------------
    sleep = daily_input.get("sleep_hours", 0)
    sleep = max(0, min(sleep, 12))          # max 12 hrs

    screen_time = daily_input.get("screen_time", 0)
    screen_time = max(0, min(screen_time, 16))  # max 16 hrs

    stress = daily_input.get("stress_level", 0)
    stress = max(0, min(stress, 5))          # scale 0–5

    water = daily_input.get("water_intake", 0)
    water = max(0, min(water, 6))            # max 6 litres

    exercise = bool(daily_input.get("exercise", False))

    # -----------------
    # Sleep logic
    # -----------------
    if 7 <= sleep <= 9:
        stats["energy"] += 10
        stats["focus"] += 5
    elif sleep < 5:
        stats["energy"] -= 15
        stats["focus"] -= 10
    elif sleep > 10:                          # oversleep → laziness
        stats["energy"] -= 5

    # -----------------
    # Screen time logic
    # -----------------
    if screen_time < 1:
        stats["focus"] += 10
    elif screen_time > 4:
        stats["focus"] -= 10

    # -----------------
    # Exercise logic
    # -----------------
    if exercise:
        stats["health"] += 10
        stats["energy"] += 5

    # -----------------
    # Stress logic
    # -----------------
    if stress >= 4:
        stats["focus"] -= 10
        stats["health"] -= 5

    # -----------------
    # Resilience logic
    # -----------------
    if sleep >= 7 and exercise:
        stats["resilience"] += 10

    if stress >= 4 and sleep < 6:
        stats["resilience"] -= 10

    # -----------------
    # Water intake logic
    # -----------------
    if water < 2:
        stats["energy"] -= 5
    elif water >= 3:
        stats["energy"] += 5

    # -----------------
    # Clamp all stats (0–100)
    # -----------------
    for key in stats:
        stats[key] = clamp(stats[key])

    return stats


"""
# ---------------------------------
# TEST RUN (TEMPORARY)
# ---------------------------------
if __name__ == "__main__":
    test_input = {
        "sleep_hours": 6,
        "screen_time": 8,
        "exercise": False,
        "stress_level": 4,
        "water_intake": 2
    }

    stats = calculate_stats(test_input)
    print(stats)
"""

# -------------------------------
# EFFECTS SYSTEM (BUFFS / DEBUFFS)
# -------------------------------

def determine_effects(stats):
    """
    Determines active buffs and debuffs based on current stats.
    Effects are descriptive labels used by:
    - UI (themes, character appearance)
    - Boss triggering
    - Recovery logic
    """

    effects = []

    # ---------- ENERGY ----------
    if stats["energy"] < 40:
        effects.append("fatigue")

    if stats["energy"] > 70:
        effects.append("high_energy")

    # ---------- FOCUS ----------
    if stats["focus"] < 40:
        effects.append("low_focus")

    if stats["focus"] > 70:
        effects.append("high_focus")

    # ---------- HEALTH ----------
    if stats["health"] < 40:
        effects.append("burnout_risk")

    if stats["health"] > 70:
        effects.append("good_health")

    # ---------- RESILIENCE ----------
    if stats["resilience"] < 40:
        effects.append("low_resilience")

    if stats["resilience"] > 70:
        effects.append("high_resilience")

    return effects


if __name__ == "__main__":
    sample_input = {
        "sleep_hours": 6,
        "screen_time": 8,
        "exercise": False,
        "stress_level": 4,
        "water_intake": 2
    }

    stats = calculate_stats(sample_input)
    effects = determine_effects(stats)

    print("Stats:", stats)
    print("Effects:", effects)
