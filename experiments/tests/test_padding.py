import random

import pytest

from constraint_decay_toolkit import make_padding


def padding_for(condition, n_blocks, seed, level):
    rng = random.Random(seed * 7919 + level)
    return make_padding(condition, n_blocks, rng)


@pytest.mark.parametrize("condition", ["lorem", "prose", "distractor"])
def test_same_seed_and_level_identical_padding(condition):
    a = padding_for(condition, n_blocks=4, seed=1000, level=8)
    b = padding_for(condition, n_blocks=4, seed=1000, level=8)
    assert a == b


@pytest.mark.parametrize("condition", ["prose", "distractor"])
def test_different_level_changes_padding(condition):
    # level feeds the seed formula directly, so a different level must
    # change the rng stream even with the same base seed.
    a = padding_for(condition, n_blocks=4, seed=1000, level=8)
    b = padding_for(condition, n_blocks=4, seed=1000, level=16)
    assert a != b


@pytest.mark.parametrize("condition", ["prose", "distractor"])
def test_different_seed_changes_padding(condition):
    a = padding_for(condition, n_blocks=4, seed=1000, level=8)
    b = padding_for(condition, n_blocks=4, seed=2000, level=8)
    assert a != b


def test_lorem_is_seed_independent():
    # lorem blocks are fixed text with no rng draw, by design.
    a = padding_for("lorem", n_blocks=3, seed=1000, level=8)
    b = padding_for("lorem", n_blocks=3, seed=9999, level=8)
    assert a == b


@pytest.mark.parametrize("condition", ["lorem", "prose", "distractor"])
def test_zero_blocks_is_empty(condition):
    assert padding_for(condition, n_blocks=0, seed=1000, level=0) == ""


@pytest.mark.parametrize("condition", ["lorem", "prose", "distractor"])
def test_block_count_scales_with_n_blocks(condition):
    one = padding_for(condition, n_blocks=1, seed=1000, level=8)
    four = padding_for(condition, n_blocks=4, seed=1000, level=8)
    assert one.count("\n\n") == 0
    assert four.count("\n\n") == 3


def test_unknown_condition_raises():
    rng = random.Random(1)
    with pytest.raises(ValueError):
        make_padding("bogus", 2, rng)
