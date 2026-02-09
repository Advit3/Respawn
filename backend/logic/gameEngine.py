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
# TEST RUN (TEMPORARY) for calculating stats
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


#-------------------------------------------------------------------------------------------------



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

"""
# ---------------------------------
# TEST RUN (TEMPORARY) for buffs and debuffs
# ---------------------------------

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
"""


#-------------------------------------------------------------------------------------------------



# -------------------------------
# XP & LEVEL SYSTEM (CONTINUOUS)
# -------------------------------

BASE_XP = 100        # XP needed to reach level 2
XP_INCREMENT = 40    # Extra XP added per new level


def xp_required_for_level(target_level):
    """
    Returns total XP required to reach the given level.
    Level 1 -> 0 XP
    Level 2 -> 100 XP
    Level 3 -> 240 XP
    Level 4 -> 420 XP
    """

    if target_level <= 1:
        return 0

    total_xp = 0
    increment = BASE_XP

    for level in range(2, target_level + 1):
        total_xp += increment
        increment += XP_INCREMENT

    return total_xp


def calculate_level_from_xp(total_xp):
    """
    Determines current level and progress toward next level
    based on continuous XP.
    """

    level = 1

    while total_xp >= xp_required_for_level(level + 1):
        level += 1

    next_level_xp = xp_required_for_level(level + 1)

    return {
        "level": level,
        "total_xp": total_xp,
        "xp_for_next_level": next_level_xp,
        "xp_progress_in_level": total_xp - xp_required_for_level(level)
    }

"""
# ---------------------------------
# TEST RUN (TEMPORARY): XP & LEVEL
# ---------------------------------
if __name__ == "__main__":
    test_xp_values = [0, 50, 100, 180, 240, 300, 420, 640]

    for xp in test_xp_values:
        level_info = calculate_level_from_xp(xp)
        print(f"XP = {xp} → {level_info}")
"""



#-------------------------------------------------------------------------------------------------



# -------------------------------
# CHARACTER & THEME SYSTEM
# -------------------------------

def determine_character_state(stats, effects):
    """
    Determines character appearance and app theme
    based on interpreted effects.
    """

    # Convert effects list to set for easier checks
    effects_set = set(effects)

    # -------- PRIORITY STATES --------

    # 1️⃣ Stressed (highest priority)
    if "low_resilience" in effects_set or "burnout_risk" in effects_set:
        return {
            "character_state": "stressed",
            "theme": "rain"
        }

    # 2️⃣ Tired
    if "fatigue" in effects_set:
        return {
            "character_state": "tired",
            "theme": "night"
        }

    # 3️⃣ Energetic
    if "high_energy" in effects_set and "high_focus" in effects_set:
        return {
            "character_state": "energetic",
            "theme": "sunny"
        }

    # -------- NORMAL (EXPLICIT) --------

    # Stable healthy state OR no effects at all
    if (
        effects_set == set() or
        effects_set.issubset({"good_health", "high_resilience"})
    ):
        return {
            "character_state": "normal",
            "theme": "normal"
        }

    # -------- SAFE FALLBACK --------
    # Should rarely hit this
    return {
        "character_state": "normal",
        "theme": "normal"
    }

"""
# ---------------------------------
# TEST RUN: CHARACTER & THEME
# ---------------------------------
if __name__ == "__main__":

    # Sample stats (already calculated earlier in pipeline)
    test_stats = {
        "health": 55,
        "energy": 45,
        "focus": 30,
        "resilience": 40
    }

    # Try different effect sets ONE BY ONE
    test_cases = {
        "Stressed case": ["low_resilience"],
        "Tired case": ["fatigue"],
        "Energetic case": ["high_energy", "high_focus"],
        "Normal (healthy)": ["good_health", "high_resilience"],
        "Normal (no effects)": []
    }

    for case, effects in test_cases.items():
        result = determine_character_state(test_stats, effects)
        print(f"\n{case}")
        print("Effects:", effects)
        print("Character State:", result["character_state"])
        print("Theme:", result["theme"])
"""


#-------------------------------------------------------------------------------------------------




# -------------------------------
# QUEST TEMPLATES
# -------------------------------

QUEST_POOL = [
    # ---------- SLEEP ----------
    {
        "id": "sleep_7h",
        "title": "Sleep at least 7 hours",
        "type": "corrective",
        "completion_type": "input",
        "condition": {"sleep_hours": 7},
        "xp": 25,
        "targets": ["energy", "focus"],
        "cooldown": 1
    },

    # ---------- SCREEN TIME ----------
    {
        "id": "screen_under_4h",
        "title": "Keep screen time under 4 hours",
        "type": "corrective",
        "completion_type": "input",
        "condition": {"screen_time_max": 4},
        "xp": 20,
        "targets": ["focus"],
        "cooldown": 1
    },

    # ---------- WATER ----------
    {
        "id": "water_3l",
        "title": "Drink at least 3L of water",
        "type": "support",
        "completion_type": "input",
        "condition": {"water_intake": 3},
        "xp": 15,
        "targets": ["energy"],
        "cooldown": 1
    },

    # ---------- BREATHING ----------
    {
        "id": "breathing_10min",
        "title": "10-minute breathing exercise",
        "type": "support",
        "completion_type": "manual",
        "xp": 10,
        "targets": ["resilience"],
        "cooldown": 1
    },

    # ---------- WALK ----------
    {
        "id": "short_walk",
        "title": "Take a short walk",
        "type": "preventive",
        "completion_type": "manual",
        "xp": 10,
        "targets": ["health", "resilience"],
        "cooldown": 2
    },

    # ---------- PLANNING ----------
    {
        "id": "plan_day",
        "title": "Plan tomorrow’s tasks",
        "type": "preventive",
        "completion_type": "manual",
        "xp": 10,
        "targets": [],
        "cooldown": 2
    }
]

# -------------------------------
# WEAK STAT DETECTION
# -------------------------------

def detect_weak_stats(stats):
    weak = []

    if stats["energy"] < 40:
        weak.append("energy")
    if stats["focus"] < 40:
        weak.append("focus")
    if stats["resilience"] < 40:
        weak.append("resilience")

    return weak


# -------------------------------
# QUEST GENERATION
# -------------------------------

def generate_daily_quests(stats, effects, recent_quests=None):
    """
    Generates up to 4 quests based on weak stats and variety rules.
    recent_quests: list of quest IDs from yesterday (can be None)
    """

    recent_quests = recent_quests or []
    weak_stats = detect_weak_stats(stats)

    selected = []

    # 1️⃣ Corrective quests for weak stats
    for stat in weak_stats:
        for quest in QUEST_POOL:
            if (
                stat in quest["targets"]
                and quest["id"] not in recent_quests
                and quest not in selected
                and quest["type"] == "corrective"
            ):
                selected.append(quest)
                break

    # 2️⃣ Support quests if space remains
    for quest in QUEST_POOL:
        if (
            quest["type"] == "support"
            and quest["id"] not in recent_quests
            and quest not in selected
        ):
            selected.append(quest)
        if len(selected) >= 3:
            break

    # 3️⃣ Preventive quest for variety
    for quest in QUEST_POOL:
        if (
            quest["type"] == "preventive"
            and quest["id"] not in recent_quests
            and quest not in selected
        ):
            selected.append(quest)
            break

    # Limit to 4
    return selected[:4]


# -------------------------------
# QUEST COMPLETION & XP
# -------------------------------

def check_quest_completion(quests, daily_input, manual_completions=None):
    """
    Checks which quests are completed today.
    Returns completed quests and XP gained.
    """

    manual_completions = manual_completions or []
    completed = []
    xp_gained = 0

    for quest in quests:
        if quest["completion_type"] == "manual":
            if quest["id"] in manual_completions:
                completed.append(quest)
                xp_gained += quest["xp"]

        elif quest["completion_type"] == "input":
            condition = quest["condition"]
            completed_flag = True

            for key, value in condition.items():
                if key.endswith("_max"):
                    real_key = key.replace("_max", "")
                    if daily_input.get(real_key, 0) > value:
                        completed_flag = False
                else:
                    if daily_input.get(key, 0) < value:
                        completed_flag = False

            if completed_flag:
                completed.append(quest)
                xp_gained += quest["xp"]

    return {
        "completed_quests": completed,
        "xp_gained": xp_gained
    }

"""
# ---------------------------------
# TEST RUN: QUEST SYSTEM
# ---------------------------------
if __name__ == "__main__":
    test_input = {
        "sleep_hours": 5,
        "screen_time": 6,
        "exercise": False,
        "stress_level": 4,
        "water_intake": 1
    }

    stats = calculate_stats(test_input)
    effects = determine_effects(stats)

    quests = generate_daily_quests(stats, effects)
    result = check_quest_completion(quests, test_input, manual_completions=[])

    print("\nStats:", stats)
    print("Effects:", effects)
    print("\nGenerated Quests:")
    for q in quests:
        print("-", q["title"])

    print("\nCompleted Quests:", [q["id"] for q in result["completed_quests"]])
    print("XP Gained:", result["xp_gained"])
"""


#-------------------------------------------------------------------------------------------------



# -------------------------------
# BOSS MODEL
# -------------------------------

def create_boss(name, boss_type="stat", days_remaining=3):
    return {
        "name": name,
        "type": boss_type,   # "stat" or "calendar"
        "hp": 100,
        "max_hp": 100,
        "days_remaining": days_remaining,
        "active": True,
        "defeated": False
    }


# -------------------------------
# STAT TREND CALCULATION
# -------------------------------

def calculate_stat_trend(prev_stats, curr_stats):
    """
    Returns trend score based on energy, focus, resilience.
    +1 improvement, 0 no change, -1 decline
    """

    score = 0
    tracked_stats = ["energy", "focus", "resilience"]

    for stat in tracked_stats:
        if curr_stats[stat] > prev_stats[stat]:
            score += 1
        elif curr_stats[stat] < prev_stats[stat]:
            score -= 1

    return score


# -------------------------------
# BOSS UPDATE LOGIC
# -------------------------------

def update_boss(boss, prev_stats, curr_stats):
    trend = calculate_stat_trend(prev_stats, curr_stats)

    if trend >= 1:
        boss["hp"] -= 30
    elif trend == 0:
        boss["hp"] -= 10
    else:
        boss["hp"] += 15

    # Clamp HP
    boss["hp"] = max(0, min(boss["hp"], boss["max_hp"]))

    # Reduce remaining days
    boss["days_remaining"] -= 1

    # Check defeat or expiration
    if boss["hp"] <= 0:
        boss["defeated"] = True
        boss["active"] = False

    elif boss["days_remaining"] <= 0:
        boss["active"] = False

    return boss


# -------------------------------
# BOSS FAILURE PENALTY
# -------------------------------

def boss_failure_penalty(boss):
    if not boss["defeated"] and boss["days_remaining"] <= 0:
        return {
            "effect": "demotivated",
            "energy_penalty": 5,
            "focus_penalty": 5,
            "duration_days": 1
        }
    return None


# -------------------------------
# CALENDAR EVENT HANDLING
# -------------------------------

def check_calendar_event(event):
    """
    event = {
        "name": "Exam",
        "days_left": 3
    }
    Boss appears when days_left <= 3
    """

    if event["days_left"] <= 3:
        return create_boss(
            name=f"{event['name']} Stress",
            boss_type="calendar",
            days_remaining=event["days_left"]
        )

    return None

"""
# ---------------------------------
# TEST RUN: BOSS & CALENDAR
# ---------------------------------
if __name__ == "__main__":
    prev_stats = {"energy": 40, "focus": 30, "resilience": 45}
    curr_stats = {"energy": 50, "focus": 25, "resilience": 45}

    boss = create_boss("Burnout Beast")
    print("Day 1:", update_boss(boss, prev_stats, curr_stats))

    penalty = boss_failure_penalty(boss)
    print("Penalty:", penalty)

    event = {"name": "Exam", "days_left": 3}
    event_boss = check_calendar_event(event)
    print("Calendar Boss:", event_boss)
"""


#-------------------------------------------------------------------------------------------------



# -------------------------------
# MASTER DAILY PROCESSOR
# -------------------------------

def process_day(
    daily_input,
    previous_state,
    manual_completions=None
):
    manual_completions = manual_completions or []

    # -----------------
    # 1. Previous data
    # -----------------
    prev_stats = previous_state.get("stats", BASE_STATS.copy())
    total_xp = previous_state.get("xp", {}).get("total_xp", 0)
    active_boss = previous_state.get("boss", None)
    recent_quests = [q["id"] for q in previous_state.get("active_quests", [])]
    calendar_event = previous_state.get("calendar_event", None)

    # -----------------
    # 2. Calculate stats & effects
    # -----------------
    stats = calculate_stats(daily_input)
    effects = determine_effects(stats)

    # -----------------
    # 3. Character & theme
    # -----------------
    character = determine_character_state(stats, effects)

    # -----------------
    # 4. Quest generation & completion
    # -----------------
    active_quests = generate_daily_quests(stats, effects, recent_quests)
    quest_result = check_quest_completion(
        active_quests,
        daily_input,
        manual_completions
    )

    completed_quests = quest_result["completed_quests"]
    xp_from_quests = quest_result["xp_gained"]

    total_xp += xp_from_quests
    xp_info = calculate_level_from_xp(total_xp)

    # -----------------
    # 5. Boss handling
    # -----------------
    penalty = None

    # Calendar-based boss trigger
    if calendar_event and not active_boss:
        active_boss = check_calendar_event(calendar_event)

    # Update active boss
    if active_boss and active_boss["active"]:
        active_boss = update_boss(active_boss, prev_stats, stats)

        # Boss failure penalty
        penalty = boss_failure_penalty(active_boss)

    # -----------------
    # 6. Return full state
    # -----------------
    return {
        "stats": stats,
        "effects": effects,
        "character": character,
        "quests": {
            "active": active_quests,
            "completed": completed_quests
        },
        "xp": xp_info,
        "boss": active_boss,
        "penalty": penalty
    }



# ---------------------------------
# TEST RUN: FULL DAILY CYCLE
# ---------------------------------
if __name__ == "__main__":
    prev_state = {
        "stats": {"health": 45, "energy": 40, "focus": 30, "resilience": 45},
        "xp": {"total_xp": 100},
        "boss": create_boss("Burnout Beast"),
        "active_quests": []
    }

    daily_input = {
        "sleep_hours": 7,
        "screen_time": 3,
        "exercise": True,
        "stress_level": 2,
        "water_intake": 3
    }

    result = process_day(daily_input, prev_state)
    print(result)
