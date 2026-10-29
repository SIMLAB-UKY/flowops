"""Verify reproducible task preparation without changing source records."""

import unittest

from scenario_inputs import assign_loading_times


class TestScenarioInputs(unittest.TestCase):
    """Check the loading-time input generator."""

    def test_loading_samples_reproducible_and_preserve_inputs(self):
        """Repeat the same seeded sampling without modifying source tasks."""

        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 0},
            {"task_id": "T003", "arrival_time_s": 130},
        ]
        original_tasks = [task.copy() for task in tasks]

        # Each call creates a fresh generator with the same starting seed.
        first = assign_loading_times(tasks, seed=42)
        second = assign_loading_times(tasks, seed=42)

        self.assertEqual(first, second)
        self.assertEqual(tasks, original_tasks)
        self.assertEqual(len(first), len(tasks))

        # Preserve task identity and arrivals while adding valid durations.
        for original, sampled in zip(tasks, first):
            self.assertIsNot(original, sampled)
            self.assertEqual(sampled["task_id"], original["task_id"])
            self.assertEqual(
                sampled["arrival_time_s"], original["arrival_time_s"]
            )
            self.assertGreaterEqual(sampled["loading_time_s"], 3.0)
            self.assertLessEqual(sampled["loading_time_s"], 7.0)


if __name__ == "__main__":
    unittest.main()