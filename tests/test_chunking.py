from __future__ import annotations

import pytest

from dist_rsa.core.chunking import build_chunks, calculate_search_limit, iter_chunks


def test_calculate_search_limit():
    assert calculate_search_limit(49) == 7
    assert calculate_search_limit(50) == 7


@pytest.mark.parametrize("n", [0, 1, -5])
def test_calculate_search_limit_invalid(n: int):
    with pytest.raises(ValueError):
        calculate_search_limit(n)


def test_build_chunks_creates_expected_ranges():
    chunks = build_chunks(n=100, chunk_size=3)
    assert [(c.start, c.end) for c in chunks] == [(2, 4), (5, 7), (8, 10)]
    assert all(c.chunk_id == idx for idx, c in enumerate(chunks))


def test_iter_chunks_matches_build_chunks():
    assert list(iter_chunks(n=36, chunk_size=4)) == build_chunks(n=36, chunk_size=4)
