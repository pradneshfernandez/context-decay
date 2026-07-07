from constraint_decay_toolkit import (
    validate_end_token,
    validate_json_schema,
    validate_no_the,
    validate_prefix,
    validate_uppercase,
)


class TestValidateUppercase:
    def test_pass(self):
        assert validate_uppercase("HELLO WORLD") is True

    def test_pass_with_digits_and_punctuation(self):
        assert validate_uppercase("HELLO, WORLD! 123") is True

    def test_fail_mixed_case(self):
        assert validate_uppercase("Hello World") is False

    def test_fail_all_lowercase(self):
        assert validate_uppercase("hello") is False

    def test_edge_empty_string(self):
        assert validate_uppercase("") is False

    def test_edge_whitespace_only(self):
        assert validate_uppercase("   \n\t") is False

    def test_edge_no_letters(self):
        assert validate_uppercase("123 !!! 456") is False


class TestValidateNoThe:
    def test_pass_no_the(self):
        assert validate_no_the("A cat sat on mat") is True

    def test_fail_the_present(self):
        assert validate_no_the("The cat sat on the mat") is False

    def test_fail_case_insensitive(self):
        assert validate_no_the("Look over THE fence") is False

    def test_edge_empty_string(self):
        assert validate_no_the("") is True

    def test_edge_whitespace_only(self):
        assert validate_no_the("   ") is True

    def test_edge_word_boundary_not_substring(self):
        # "there" and "theme" contain "the" but are not the word "the"
        assert validate_no_the("there is a theme here") is True


class TestValidateJsonSchema:
    def test_pass(self):
        assert validate_json_schema('{"answer": "Paris", "confidence": 0.9}') is True

    def test_pass_with_markdown_fence(self):
        text = '```json\n{"answer": "Paris", "confidence": 0.9}\n```'
        assert validate_json_schema(text) is True

    def test_pass_with_bare_fence(self):
        text = '```\n{"answer": "Paris", "confidence": 0.9}\n```'
        assert validate_json_schema(text) is True

    def test_pass_boundary_confidence_zero(self):
        assert validate_json_schema('{"answer": "x", "confidence": 0}') is True

    def test_pass_boundary_confidence_one(self):
        assert validate_json_schema('{"answer": "x", "confidence": 1}') is True

    def test_fail_malformed_json(self):
        assert validate_json_schema('{"answer": "Paris"') is False

    def test_fail_missing_key(self):
        assert validate_json_schema('{"answer": "Paris"}') is False

    def test_fail_extra_key(self):
        text = '{"answer": "Paris", "confidence": 0.9, "extra": 1}'
        assert validate_json_schema(text) is False

    def test_fail_confidence_out_of_range(self):
        assert validate_json_schema('{"answer": "x", "confidence": 1.5}') is False

    def test_fail_confidence_negative(self):
        assert validate_json_schema('{"answer": "x", "confidence": -0.1}') is False

    def test_fail_confidence_is_bool(self):
        assert validate_json_schema('{"answer": "x", "confidence": true}') is False

    def test_fail_answer_not_string(self):
        assert validate_json_schema('{"answer": 5, "confidence": 0.5}') is False

    def test_fail_not_an_object(self):
        assert validate_json_schema('["answer", "confidence"]') is False

    def test_edge_empty_string(self):
        assert validate_json_schema("") is False

    def test_edge_whitespace_only(self):
        assert validate_json_schema("   ") is False


class TestValidatePrefix:
    def test_pass(self):
        assert validate_prefix("[AGENT-7]: Hello there") is True

    def test_pass_with_leading_whitespace(self):
        assert validate_prefix("   \n[AGENT-7]: Hello") is True

    def test_fail_tag_not_at_start(self):
        assert validate_prefix("Hello [AGENT-7]: there") is False

    def test_fail_wrong_case(self):
        assert validate_prefix("[Agent-7]: Hello") is False

    def test_edge_empty_string(self):
        assert validate_prefix("") is False

    def test_edge_whitespace_only(self):
        assert validate_prefix("   ") is False


class TestValidateEndToken:
    def test_pass(self):
        assert validate_end_token("The answer is 5 ##END##") is True

    def test_pass_with_trailing_whitespace(self):
        assert validate_end_token("The answer is 5 ##END##   \n") is True

    def test_fail_token_not_at_end(self):
        assert validate_end_token("##END## The answer is 5") is False

    def test_edge_empty_string(self):
        assert validate_end_token("") is False

    def test_edge_whitespace_only(self):
        assert validate_end_token("   ") is False
