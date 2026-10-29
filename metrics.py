"""Calculate scenario-level performance measures from delivery records.

Inputs are results (a list of completed-delivery dictionaries),
num_robots (the fleet size), and fleet_finish_time_s (simulation time
after every robot's final return). All time measures use seconds.

The function returns a summary dictionary without modifying the records,
printing output, or writing files. At least one delivery is required.
"""


def summarize_results(results, num_robots, fleet_finish_time_s):
    """Return delivery counts and mean waiting and flow times."""

    completed = len(results)

    # An empty scenario has no defined mean delivery performance.
    if completed == 0:
        raise ValueError("At least one completed delivery is required")

    # Select each record's metric, sum the values, and divide by the count.
    mean_robot_wait_s = sum(
        record["waiting_time_s"] for record in results
    ) / completed

    mean_loading_wait_s = sum(
        record["loading_wait_time_s"] for record in results
    ) / completed

    mean_flow_time_s = sum(
        record["flow_time_s"] for record in results
    ) / completed

    # Preserve the existing CSV field names and full numeric precision.
    return {
        "num_robots": num_robots,
        "completed_deliveries": completed,
        "fleet_finish_time_s": fleet_finish_time_s,
        "mean_robot_wait_s": mean_robot_wait_s,
        "mean_loading_wait_s": mean_loading_wait_s,
        "mean_flow_time_s": mean_flow_time_s,
    }