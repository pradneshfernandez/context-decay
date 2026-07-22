import pandas as pd

from answer_correctness import (
    ANSWER_CHECKERS,
    annotate,
    check_answer,
    check_banana_color,
    check_capital_of_france,
    check_planet,
    check_spider_legs,
)


class TestCheckCapitalOfFrance:
    def test_pass(self):
        assert check_capital_of_france("THE CAPITAL OF FRANCE IS PARIS!") is True

    def test_pass_case_insensitive(self):
        assert check_capital_of_france("paris is the capital.") is True

    def test_fail_wrong_answer(self):
        assert check_capital_of_france("The capital of France is Lyon.") is False

    def test_edge_empty_string(self):
        assert check_capital_of_france("") is False

    def test_edge_substring_not_word(self):
        # "parisian" contains "paris" but isn't the word "Paris"
        assert check_capital_of_france("A parisian cafe.") is False


class TestCheckPlanet:
    def test_pass(self):
        assert check_planet("MARS IS A PLANET IN OUR SOLAR SYSTEM!") is True

    def test_pass_any_recognized_planet(self):
        assert check_planet("I'll say Neptune.") is True

    def test_fail_not_a_planet(self):
        assert check_planet("The moon is not a planet.") is False

    def test_edge_empty_string(self):
        assert check_planet("") is False


class TestCheckBananaColor:
    def test_pass(self):
        assert check_banana_color("A ripe banana is yellow.") is True

    def test_fail_wrong_color(self):
        assert check_banana_color("A ripe banana is green.") is False

    def test_edge_empty_string(self):
        assert check_banana_color("") is False


class TestCheckSpiderLegs:
    def test_pass_word(self):
        assert check_spider_legs("A spider has eight legs.") is True

    def test_pass_digit(self):
        assert check_spider_legs("A spider has 8 legs.") is True

    def test_fail_wrong_count(self):
        assert check_spider_legs("A spider has six legs.") is False

    def test_edge_empty_string(self):
        assert check_spider_legs("") is False


class TestCheckAnswer:
    def test_recognized_query_correct(self):
        assert check_answer("What is the capital of France?", "Paris.") is True

    def test_recognized_query_incorrect(self):
        assert check_answer("What is the capital of France?", "Lyon.") is False

    def test_unrecognized_query_returns_none(self):
        assert check_answer("What is 2 + 2?", "4") is None

    def test_all_queries_have_checkers(self):
        # Sanity: ANSWER_CHECKERS must stay in sync with
        # constraint_decay_toolkit.QUERIES if that list ever changes.
        assert len(ANSWER_CHECKERS) == 4


class TestAnnotate:
    def _df(self, rows):
        return pd.DataFrame(rows)

    def test_correct_answer_marked_1(self):
        df = self._df([{"query": "What color is a ripe banana?",
                         "output_snippet": "Yellow!", "success": 1}])
        out = annotate(df)
        assert out["answer_correct"].tolist() == [1]

    def test_incorrect_answer_marked_0(self):
        df = self._df([{"query": "What color is a ripe banana?",
                         "output_snippet": "Green!", "success": 1}])
        out = annotate(df)
        assert out["answer_correct"].tolist() == [0]

    def test_error_row_excluded(self):
        df = self._df([{"query": "What color is a ripe banana?",
                         "output_snippet": "ERROR: timeout", "success": -1}])
        out = annotate(df)
        assert out["answer_correct"].tolist() == [-1]

    def test_unrecognized_query_excluded(self):
        df = self._df([{"query": "What is 2 + 2?",
                         "output_snippet": "4", "success": 1}])
        out = annotate(df)
        assert out["answer_correct"].tolist() == [-1]
