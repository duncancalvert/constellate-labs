"""Tests for sampling utils."""

import random

import numpy as np

from constellate_labs.utils.sampling import poisson_disk_2d, poisson_disk_along_path


def test_poisson_empty() -> None:
    out = poisson_disk_along_path(np.empty((0, 2)), 1.0)
    assert out.shape == (0, 2)


def test_poisson_single_point() -> None:
    pts = np.array([[1.0, 2.0]])
    out = poisson_disk_along_path(pts, 1.0)
    assert out.shape == (1, 2)
    np.testing.assert_array_almost_equal(out[0], [1.0, 2.0])


def test_poisson_line() -> None:
    pts = np.array([[0.0, 0.0], [10.0, 0.0]])
    out = poisson_disk_along_path(pts, 2.0)
    assert out.shape[0] >= 2
    d = np.linalg.norm(np.diff(out, axis=0), axis=1)
    assert np.all(d >= 1.5)  # approx min_distance


def test_poisson_disk_2d() -> None:
    rng = random.Random(42)
    out = poisson_disk_2d(0, 0, 100, 100, min_distance=10.0, n_points=20, rng=rng)
    assert out.shape[0] <= 20
    assert out.shape[1] == 2
    assert np.all(out[:, 0] >= 0) and np.all(out[:, 0] <= 100)
    assert np.all(out[:, 1] >= 0) and np.all(out[:, 1] <= 100)
    if out.shape[0] >= 2:
        for i in range(out.shape[0]):
            for j in range(i + 1, out.shape[0]):
                d = np.linalg.norm(out[i] - out[j])
                assert d >= 9.0  # min_distance 10 with small tolerance
