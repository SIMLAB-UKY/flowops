"""Run paired fleet experiments with variable loading durations.

Each replication compares one and two robots using the same loading seed.
Across replications, seeds change to generate different task workloads.
Loading durations follow the runner's illustrative Uniform(3, 7) model.

The script writes one summary row per fleet size and replication to
replication_results.csv. All performance durations use seconds.
"""

import csv

from arrival_demo import run_scenario


def main():
    """Run thirty paired replications and export their summary records."""

    num_replications = 30
    base_seed = 42
    fleet_sizes = [1, 2]
    rows = []


     # All three requests compete for robots from simulation time zero.
    scenario_name = "simultaneous_arrivals"
    tasks = [
        {"task_id": "T001", "arrival_time_s": 0},
        {"task_id": "T002", "arrival_time_s": 0},
        {"task_id": "T003", "arrival_time_s": 0},
    ]
    # Select a different loading seed for each replication.
    for replication_id in range(1, num_replications + 1):
        loading_seed = base_seed + replication_id - 1

        # Both fleet sizes receive the same workload within this replication.
        for num_robots in fleet_sizes:
            output = run_scenario(
                num_robots=num_robots,
                verbose=False,
                loading_seed=loading_seed,
                tasks=tasks,
            )

            # Copy the summary before attaching experiment metadata.
            row = output["summary"].copy()
            row["scenario_name"] = scenario_name
            row["replication_id"] = replication_id
            row["loading_seed"] = loading_seed
            rows.append(row)

    # Fix the column order so the experiment file is easy to inspect.
    fieldnames = [
        "replication_id",
        "loading_seed",
        "scenario_name",
        "num_robots",
        "completed_deliveries",
        "fleet_finish_time_s",
        "mean_robot_wait_s",
        "mean_loading_wait_s",
        "mean_flow_time_s",
    ]

    output_filename = f"replication_results_{scenario_name}.csv"
    
    with open(
        output_filename, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Completed replications per fleet: {num_replications}")
    print(f"Scenario runs: {len(rows)}")
    print(f"Saved {output_filename}")


if __name__ == "__main__":
    main()