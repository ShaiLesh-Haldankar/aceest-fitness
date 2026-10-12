"""Unit tests for pure business logic in fitness.py."""

import random

import pytest

import fitness
from fitness import ValidationError


class TestPrograms:
    def test_all_programs_have_required_fields(self):
        for prog in fitness.PROGRAMS.values():
            assert {"name", "calorie_factor", "workout", "diet"} <= prog.keys()
            assert prog["workout"] and prog["diet"]

    @pytest.mark.parametrize("code", ["FL", "fl", "Mg", "BG"])
    def test_get_program_case_insensitive(self, code):
        assert fitness.get_program(code) is fitness.PROGRAMS[code.upper()]

    @pytest.mark.parametrize("code", ["XX", "", None])
    def test_get_program_unknown(self, code):
        with pytest.raises(KeyError):
            fitness.get_program(code)


class TestCalories:
    @pytest.mark.parametrize(
        "weight,program,expected",
        [(80, "FL", 1760), (80, "MG", 2800), (70, "BG", 1820), (72.5, "FL", 1595)],
    )
    def test_calculate_calories(self, weight, program, expected):
        assert fitness.calculate_calories(weight, program) == expected

    @pytest.mark.parametrize("weight", [0, -5, "abc", None])
    def test_invalid_weight(self, weight):
        with pytest.raises(ValidationError):
            fitness.calculate_calories(weight, "FL")


class TestBMI:
    def test_calculate_bmi(self):
        assert fitness.calculate_bmi(70, 175) == 22.9

    @pytest.mark.parametrize(
        "bmi,category",
        [(17.0, "Underweight"), (18.5, "Normal"), (24.9, "Normal"),
         (25.0, "Overweight"), (29.9, "Overweight"), (30.0, "Obese")],
    )
    def test_bmi_category_boundaries(self, bmi, category):
        assert fitness.bmi_category(bmi) == category

    def test_bmi_invalid_height(self):
        with pytest.raises(ValidationError):
            fitness.calculate_bmi(70, 0)


class TestValidation:
    @pytest.mark.parametrize("value", [0, 50, 100, "75"])
    def test_valid_adherence(self, value):
        assert fitness.validate_adherence(value) == int(value)

    @pytest.mark.parametrize("value", [-1, 101, "high", None])
    def test_invalid_adherence(self, value):
        with pytest.raises(ValidationError):
            fitness.validate_adherence(value)

    def test_valid_workout(self):
        assert fitness.validate_workout("Cardio", "45") == ("Cardio", 45)

    @pytest.mark.parametrize("wtype,duration", [("Yoga", 30), ("Cardio", 0), ("Cardio", 301), ("Cardio", "x")])
    def test_invalid_workout(self, wtype, duration):
        with pytest.raises(ValidationError):
            fitness.validate_workout(wtype, duration)


class TestProgramGenerator:
    def test_generate_for_specific_program(self):
        result = fitness.generate_program("MG", rng=random.Random(42))
        assert result["program"] == "MG"
        assert result["template"] in fitness.PROGRAM_TEMPLATES["MG"]

    def test_generate_random_program(self):
        result = fitness.generate_program(rng=random.Random(1))
        assert result["template"] in fitness.PROGRAM_TEMPLATES[result["program"]]

    def test_generate_unknown_program(self):
        with pytest.raises(KeyError):
            fitness.generate_program("ZZ")


def test_average_adherence():
    assert fitness.average_adherence([80, 90, 100]) == 90.0
    assert fitness.average_adherence([]) == 0.0
