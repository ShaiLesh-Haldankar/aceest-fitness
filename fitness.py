"""Core business logic for ACEest Fitness & Gym.

Pure functions only (no Flask / DB imports) so they can be unit-tested
in isolation. Logic is ported from the legacy Tkinter versions (v1.0 - v3.2.4).
"""

import random

# Program catalogue (from Aceestver-1.0 / 1.1 / 2.2.4)
PROGRAMS = {
    "FL": {
        "name": "Fat Loss",
        "calorie_factor": 22,
        "workout": [
            "Mon: 5x5 Back Squat + AMRAP",
            "Tue: EMOM 20min Assault Bike",
            "Wed: Bench Press + 21-15-9",
            "Thu: 10RFT Deadlifts/Box Jumps",
            "Fri: 30min Active Recovery",
        ],
        "diet": [
            "B: 3 Egg Whites + Oats Idli",
            "L: Grilled Chicken + Brown Rice",
            "D: Fish Curry + Millet Roti",
        ],
    },
    "MG": {
        "name": "Muscle Gain",
        "calorie_factor": 35,
        "workout": [
            "Mon: Squat 5x5",
            "Tue: Bench 5x5",
            "Wed: Deadlift 4x6",
            "Thu: Front Squat 4x8",
            "Fri: Incline Press 4x10",
            "Sat: Barbell Rows 4x10",
        ],
        "diet": [
            "B: 4 Eggs + PB Oats",
            "L: Chicken Biryani (250g Chicken)",
            "D: Mutton Curry + Jeera Rice",
        ],
    },
    "BG": {
        "name": "Beginner",
        "calorie_factor": 26,
        "workout": [
            "Circuit Training: Air Squats, Ring Rows, Push-ups",
            "Focus: Technique Mastery & Form (90% Threshold)",
        ],
        "diet": [
            "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati",
            "Protein: 120g/day",
        ],
    },
}

# AI-style program templates (from Aceestver-3.2.4)
PROGRAM_TEMPLATES = {
    "FL": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "MG": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "BG": ["Full Body 3x/week", "Light Strength + Mobility"],
}

WORKOUT_TYPES = ("Strength", "Hypertrophy", "Cardio", "Mobility")

GYM_METRICS = {"capacity_users": 150, "area_sq_ft": 10000, "break_even_members": 250}


class ValidationError(ValueError):
    """Raised when user-supplied data is invalid."""


def get_program(code):
    """Return a program by code (case-insensitive) or raise KeyError."""
    key = (code or "").upper()
    if key not in PROGRAMS:
        raise KeyError(f"Unknown program '{code}'")
    return PROGRAMS[key]


def calculate_calories(weight_kg, program_code):
    """Daily calorie target = body weight (kg) x program calorie factor."""
    weight = _positive_number(weight_kg, "weight")
    return int(weight * get_program(program_code)["calorie_factor"])


def calculate_bmi(weight_kg, height_cm):
    """Return BMI rounded to 1 decimal place."""
    weight = _positive_number(weight_kg, "weight")
    height_m = _positive_number(height_cm, "height") / 100.0
    return round(weight / (height_m * height_m), 1)


def bmi_category(bmi):
    """WHO BMI categories (same thresholds as Aceestver-2.2.4)."""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def validate_adherence(value):
    """Adherence is a percentage in the range 0-100."""
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise ValidationError("adherence must be an integer") from None
    if not 0 <= val <= 100:
        raise ValidationError("adherence must be between 0 and 100")
    return val


def validate_workout(workout_type, duration_min):
    if workout_type not in WORKOUT_TYPES:
        raise ValidationError(f"workout_type must be one of {', '.join(WORKOUT_TYPES)}")
    try:
        duration = int(duration_min)
    except (TypeError, ValueError):
        raise ValidationError("duration_min must be an integer") from None
    if duration <= 0 or duration > 300:
        raise ValidationError("duration_min must be between 1 and 300")
    return workout_type, duration


def generate_program(program_code=None, rng=None):
    """Pick a training template, optionally constrained to a program code."""
    rng = rng or random
    code = (program_code or rng.choice(list(PROGRAM_TEMPLATES))).upper()
    if code not in PROGRAM_TEMPLATES:
        raise KeyError(f"Unknown program '{program_code}'")
    return {"program": code, "template": rng.choice(PROGRAM_TEMPLATES[code])}


def average_adherence(values):
    values = list(values)
    return round(sum(values) / len(values), 1) if values else 0.0


def _positive_number(value, field):
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number") from None
    if num <= 0:
        raise ValidationError(f"{field} must be greater than 0")
    return num
