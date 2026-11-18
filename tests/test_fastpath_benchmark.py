from __future__ import annotations

import pytest

from runner_mcp.fastpath_benchmark import (
    benchmark_synthetic_framing,
    percentile_ns,
    summarize,
    synthetic_poll_detection_delay_ms,
)


def test_exact_nearest_rank_percentiles():
    assert percentile_ns([10, 20, 30, 40, 50], 50) == 30
    assert percentile_ns([10, 20, 30, 40, 50], 95) == 50
    assert percentile_ns([10, 20, 30, 40, 50], 99) == 50


@pytest.mark.parametrize("invalid", [[], [True], [-1], [1, -1], [1, 1.5]])
def test_invalid_samples_rejected(invalid):
    with pytest.raises(ValueError):
        percentile_ns(invalid, 50)


@pytest.mark.parametrize("percentile", [0, -1, 101, float("nan"), True])
def test_invalid_percentile_rejected(percentile):
    with pytest.raises(ValueError):
        percentile_ns([1, 2, 3], percentile)


def test_summarize_known_wall_metrics():
    result = summarize([10, 20, 30, 40], 1000, bytes_per_call=400)
    assert result["p50_ns"] == 20
    assert result["p95_ns"] == 40
    assert result["calls_per_second"] == 4_000_000
    assert result["bytes_per_call"] == 400


def test_poll_boundaries_and_no_negative_delay():
    assert synthetic_poll_detection_delay_ms(0) == 0
    assert synthetic_poll_detection_delay_ms(1) == 499
    assert synthetic_poll_detection_delay_ms(100) == 400
    assert synthetic_poll_detection_delay_ms(499) == 1
    assert synthetic_poll_detection_delay_ms(500) == 0
    assert synthetic_poll_detection_delay_ms(501) == 499
    assert synthetic_poll_detection_delay_ms(900, polling_interval_ms=100) == 0


@pytest.mark.parametrize("offset,interval", [(-1, 500), (True, 500), (1, 0), (1, 60001)])
def test_invalid_poll_arguments_fail(offset, interval):
    with pytest.raises(ValueError):
        synthetic_poll_detection_delay_ms(offset, polling_interval_ms=interval)


def test_synthetic_measurement_contract_has_no_network_and_no_false_rtt_claim():
    result = benchmark_synthetic_framing(repetitions=3)
    assert result["schema_version"] == "runner-mcp/synthetic-fastpath-benchmark/v1"
    assert result["measurement_scope"] == "local_json_only_not_mcp_rtt"
    assert result["repetitions"] == 3
    assert result["synthetic_polling_delay_ms"]["job_100_ms"] == 400
    assert set(result["results"]) == {"tiny", "medium", "large"}
    for measurement in result["results"].values():
        for name in ("json_encode", "json_decode"):
            metrics = measurement[name]
            assert metrics["samples"] == 3
            assert 0 <= metrics["p50_ns"] <= metrics["p95_ns"] <= metrics["p99_ns"]
            assert metrics["bytes_per_call"] > 0
            assert metrics["calls_per_second"] > 0


@pytest.mark.parametrize("count", [0, -1, 10001, True])
def test_repetition_bound_fail_closed(count):
    with pytest.raises(ValueError):
        benchmark_synthetic_framing(repetitions=count)
