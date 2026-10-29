"""Prepare reproducible loading durations for FlowOps task records.

assign_loading_times accepts task dictionaries, a random seed, and
loading-time bounds in seconds. It returns new dictionaries containing
one sampled loading_time_s per task, preserving the original records.

Loading durations follow an illustrative uniform distribution.
They are assigned in input-list order before robot dispatch.
"""

import random


def assign_loading_times(tasks, seed, low_s=3.0, high_s=7.0):
    """Return task copies with reproducible sampled loading durations."""

    # Require nonnegative bounds in ascending order.
    if not 0 <= low_s <= high_s:
        raise ValueError("Require 0 <= low_s <= high_s")

    # Keep this generator's state separate from global random operations.
    rng = random.Random(seed)
    sampled_tasks = []

    for task in tasks:
        # Copy the record so the caller's original task remains unchanged.
        sampled_task = task.copy()

        # Assign one loading requirement before any robot receives the task.
        sampled_task["loading_time_s"] = rng.uniform(low_s, high_s)
        sampled_tasks.append(sampled_task)

    return sampled_tasks