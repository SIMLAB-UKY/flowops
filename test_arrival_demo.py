"""Verify the reusable scenario runner against the Phase 2 baseline.

Both scenarios use requests arriving at 0, 0, and 130 seconds and one
shared loading position. Expected times are measured in seconds.
"""

import unittest

from arrival_demo import run_scenario

# Capture printed output so tests can inspect it.
from contextlib import redirect_stdout
from io import StringIO


class TestArrivalDemo(unittest.TestCase):
    """Protect the deterministic baseline during further development."""

    def test_fleet_comparison_baseline(self):
        """Check runner outputs for one-robot and two-robot scenarios."""

        # Each case specifies fleet size and its expected mean delays.
        cases = [
            (1, 55 / 3, 0, 160 / 3),
            (2, 0, 5 / 3, 110 / 3),
        ]

        for num_robots, robot_wait, loading_wait, flow_time in cases:
            # Identify which fleet configuration fails, if either does.
            with self.subTest(num_robots=num_robots):
                output = run_scenario(num_robots=num_robots)
                summary = output["summary"]

                # Every request must appear exactly once in the results.
                self.assertCountEqual(
                    [record["task_id"] for record in output["results"]],
                    ["T001", "T002", "T003"],
                )

                # Per-robot counts must account for all three deliveries.
                self.assertEqual(
                    len(output["deliveries_per_robot"]), num_robots
                )
                self.assertEqual(
                    sum(output["deliveries_per_robot"].values()), 3
                )

                # Preserve the analytically verified scenario metrics.
                self.assertEqual(summary["num_robots"], num_robots)
                self.assertEqual(summary["completed_deliveries"], 3)
                self.assertAlmostEqual(summary["fleet_finish_time_s"], 185)
                self.assertAlmostEqual(
                    summary["mean_robot_wait_s"], robot_wait
                )
                self.assertAlmostEqual(
                    summary["mean_loading_wait_s"], loading_wait
                )
                self.assertAlmostEqual(
                    summary["mean_flow_time_s"], flow_time
                )
    def test_verbose_controls_output_only(self):
        """Verify that quiet mode suppresses output without changing results."""

        # Capture any text produced by the quiet scenario.
        quiet_output = StringIO()
        with redirect_stdout(quiet_output):
            quiet_results = run_scenario(num_robots=2, verbose=False)

        # Capture event messages from the same scenario in verbose mode.
        verbose_output = StringIO()
        with redirect_stdout(verbose_output):
            verbose_results = run_scenario(num_robots=2, verbose=True)

        # Quiet mode must print nothing; verbose mode must report events.
        self.assertEqual(quiet_output.getvalue(), "")
        self.assertIn("Loading started", verbose_output.getvalue())

        # Printing must not change records, robot counts, or summary metrics.
        self.assertEqual(quiet_results, verbose_results)


    def test_seeded_scenario_reproducible(self):
        """Reproduce complete scenario outputs with the same loading seed."""

        # Each run creates fresh simulation objects and a seeded generator.
        first = run_scenario(
            num_robots=2, verbose=False, loading_seed=42
        )
        second = run_scenario(
            num_robots=2, verbose=False, loading_seed=42
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first["results"]), 3)

        for record in first["results"]:
            # The recorded loading requirement must respect the input bounds.
            self.assertGreaterEqual(record["loading_time_s"], 3.0)
            self.assertLessEqual(record["loading_time_s"], 7.0)

            # Delivery duration includes station waiting but excludes return.
            expected_duration_s = (
                record["loading_wait_time_s"]
                + record["loading_time_s"]
                + 20.0
                + 10.0
            )
            self.assertAlmostEqual(
                record["task_duration_s"], expected_duration_s
            )

    def test_fleet_sizes_share_seeded_loading_times(self):
        """Give each task the same loading requirement across fleet sizes."""

        # Change fleet size while preserving the seed and task schedule.
        one_robot = run_scenario(
            num_robots=1, verbose=False, loading_seed=42
        )
        two_robots = run_scenario(
            num_robots=2, verbose=False, loading_seed=42
        )

        # Match inputs by task identity, independently of result ordering.
        one_robot_loading = {
            record["task_id"]: record["loading_time_s"]
            for record in one_robot["results"]
        }
        two_robot_loading = {
            record["task_id"]: record["loading_time_s"]
            for record in two_robots["results"]
        }

        self.assertEqual(
            set(one_robot_loading), {"T001", "T002", "T003"}
        )
        self.assertEqual(one_robot_loading, two_robot_loading)

    def test_simultaneous_arrival_schedule(self):
        """Verify a supplied schedule against fixed-time analytical results."""

        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 0},
            {"task_id": "T003", "arrival_time_s": 0},
        ]
        original_tasks = [task.copy() for task in tasks]

        # Each case specifies fleet size, expected mean flow, and final return.
        cases = [
            (1, 90.0, 165.0),
            (2, 55.0, 110.0),
        ]

        for num_robots, expected_flow, expected_finish in cases:
            with self.subTest(num_robots=num_robots):
                output = run_scenario(
                    num_robots=num_robots,
                    verbose=False,
                    tasks=tasks,
                )

                self.assertCountEqual(
                    [record["task_id"] for record in output["results"]],
                    ["T001", "T002", "T003"],
                )
                self.assertAlmostEqual(
                    output["summary"]["mean_flow_time_s"],
                    expected_flow,
                )
                self.assertAlmostEqual(
                    output["summary"]["fleet_finish_time_s"],
                    expected_finish,
                )

        # Running either fleet must leave the supplied schedule unchanged.
        self.assertEqual(tasks, original_tasks)

    def test_simultaneous_arrivals_match_analytical_reduction(self):
        """Verify each paired fleet benefit against the analytical formula."""

        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 0},
            {"task_id": "T003", "arrival_time_s": 0},
        ]

        # Check every seed used in the thirty-replication experiment.
        for seed in range(42, 72):
            with self.subTest(loading_seed=seed):
                one_robot = run_scenario(
                    num_robots=1,
                    verbose=False,
                    loading_seed=seed,
                    tasks=tasks,
                )
                two_robots = run_scenario(
                    num_robots=2,
                    verbose=False,
                    loading_seed=seed,
                    tasks=tasks,
                )

                # Index by task ID rather than assuming a result-list position.
                records_by_id = {
                    record["task_id"]: record
                    for record in one_robot["results"]
                }
                second_loading_s = records_by_id["T002"]["loading_time_s"]

                # Derive the expected benefit independently of the summary code.
                expected_reduction_s = (100 + second_loading_s) / 3

                observed_reduction_s = (
                    one_robot["summary"]["mean_flow_time_s"]
                    - two_robots["summary"]["mean_flow_time_s"]
                )

                self.assertAlmostEqual(
                    observed_reduction_s,
                    expected_reduction_s,
                )






if __name__ == "__main__":
    unittest.main()