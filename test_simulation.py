"""Verify the deterministic single-robot baseline.

Five deliveries use a 2 m route, 0.1 m/s speed, 5 s loading,
and 10 s unloading. Each delivery takes 35 s, with a 20 s
empty return separating consecutive deliveries.
"""

import unittest
from simulation import run_simulation
"""Check delivery counts, orderm and timing for the baseline scenario."""

class TestSimulation(unittest.TestCase):

    def test_five_delivery_baseline(self):
        task_ids = ["T001", "T002", "T003", "T004", "T005"]

        results = run_simulation(
            task_ids=task_ids,
            distance_m=2.0,
            speed_m_s=0.1,
            loading_time_s=5,
            unloading_time_s=10
        )

        #Che that every requested delivery appears once and in order.
        self.assertEqual(len(results), len(task_ids))
        self.assertEqual(
            [record["task_id"] for record in results],
            task_ids
        )

        #Expected starts include the emppty return between deliveries.
        expected_starts = [0, 55, 110, 165, 220]
        expected_ends = [35, 90, 145, 200, 255]
        for i, record in enumerate(results):
            self.assertAlmostEqual(record["start_time_s"], expected_starts[i])
            self.assertAlmostEqual(record["end_time_s"], expected_ends[i])
            self.assertAlmostEqual(record["task_duration_s"], 35)

    def test_zero_speed_rejected(self):
        """Reject zero speed before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "speed_m_s must be greater than zero"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0,
                loading_time_s=5,
                unloading_time_s=10,
            )


    def test_negative_distance_rejected(self):
        """Reject negative distance before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "distance_m must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=-1.0,
                speed_m_s=0.1,
                loading_time_s=5,
                unloading_time_s=10,
            )


    def test_negative_loading_time_rejected(self):
        """Reject negative loading time before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "loading_time_s must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0.1,
                loading_time_s=-5,
                unloading_time_s=10,
            )

    def test_negative_unloading_time_rejected(self):
        """Reject negative unloading time before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "unloading_time_s must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0.1,
                loading_time_s=5,
                unloading_time_s=-10,
            )


    