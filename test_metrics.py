"""Verify summary calculations against the Phase 2 reference results."""

import unittest

from metrics import summarize_results


class TestMetrics(unittest.TestCase):
    """Check scenario summaries independently of simulation execution."""

    def test_two_robot_summary(self):
        """Reproduce the known shared-loading-station averages."""

        # Only fields read by the summary function are needed here.
        results = [
            {
                "waiting_time_s": 0,
                "loading_wait_time_s": 0,
                "flow_time_s": 35,
            },
            {
                "waiting_time_s": 0,
                "loading_wait_time_s": 5,
                "flow_time_s": 40,
            },
            {
                "waiting_time_s": 0,
                "loading_wait_time_s": 0,
                "flow_time_s": 35,
            },
        ]

        summary = summarize_results(
            results,
            num_robots=2,
            fleet_finish_time_s=185,
        )

        self.assertEqual(summary["num_robots"], 2)
        self.assertEqual(summary["completed_deliveries"], 3)
        self.assertAlmostEqual(summary["fleet_finish_time_s"], 185)
        self.assertAlmostEqual(summary["mean_robot_wait_s"], 0)
        self.assertAlmostEqual(summary["mean_loading_wait_s"], 5 / 3)
        self.assertAlmostEqual(summary["mean_flow_time_s"], 110 / 3)

    def test_empty_results_rejected(self):
        """Reject an undefined mean rather than reporting a false zero."""

        with self.assertRaises(ValueError):
            summarize_results([], num_robots=2, fleet_finish_time_s=0)


if __name__ == "__main__":
    unittest.main()