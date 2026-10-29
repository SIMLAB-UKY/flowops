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

if __name__ == "__main__":
    unittest.main()