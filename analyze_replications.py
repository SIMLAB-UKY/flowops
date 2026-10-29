"""Analyze paired fleet comparisons from replication_results.csv.

Each replication must contain one result for each fleet size: one and
two robots, using the same loading seed. A positive flow-time reduction
means the two-robot fleet achieved a lower mean delivery flow time.

The script exports paired_differences.csv and reports the mean reduction
and its sample standard deviation. All time measures use seconds.
"""

import csv
from statistics import mean, stdev
# Calculate the square root used in the standard error.
from math import sqrt

def main():
    """Match fleet results by replication and summarize their differences."""

    # Keep input and output filenames tied to the same scenario.
    scenario_name = "simultaneous_arrivals"
    input_filename = f"replication_results_{scenario_name}.csv"
    output_filename = f"paired_differences_{scenario_name}.csv"
    
    
    paired_runs = {}

    # CSV fields arrive as strings, so convert identifiers and measurements.
    with open(
        input_filename, newline="", encoding="utf-8"
    ) as file:
        for row in csv.DictReader(file):
            replication_id = int(row["replication_id"])
            num_robots = int(row["num_robots"])


            # Reject a file containing results from a different scenario.
            if row["scenario_name"] != scenario_name:
                raise ValueError(
                    f"Unexpected scenario: {row['scenario_name']}"
                )
            # Create a separate collection for each replication.
            if replication_id not in paired_runs:
                paired_runs[replication_id] = {}

            # Reject duplicate results rather than silently replacing them.
            if num_robots in paired_runs[replication_id]:
                raise ValueError(
                    f"Duplicate fleet result in replication {replication_id}"
                )

            paired_runs[replication_id][num_robots] = {
                "loading_seed": int(row["loading_seed"]),
                "mean_flow_time_s": float(row["mean_flow_time_s"]),
            }

    differences = []

    # Pair by replication ID, independently of CSV row order.
    for replication_id in sorted(paired_runs):
        fleets = paired_runs[replication_id]

        if set(fleets) != {1, 2}:
            raise ValueError(
                f"Replication {replication_id} must contain fleets 1 and 2"
            )

        one_robot = fleets[1]
        two_robots = fleets[2]

        if one_robot["loading_seed"] != two_robots["loading_seed"]:
            raise ValueError(
                f"Seed mismatch in replication {replication_id}"
            )

        # Positive values represent a reduction from adding the second robot.
        reduction_s = (
            one_robot["mean_flow_time_s"]
            - two_robots["mean_flow_time_s"]
        )

        

         # Retain the scenario identity alongside each paired reduction.
        differences.append({
                "scenario_name": scenario_name,
                "replication_id": replication_id,
                "loading_seed": one_robot["loading_seed"],
                "flow_time_reduction_s": reduction_s,
            })

    # A sample standard deviation requires at least two observations.
    if len(differences) < 2:
        raise ValueError("At least two paired replications are required")

    reductions = [
        record["flow_time_reduction_s"] for record in differences
    ]

     # Summarize the paired differences using their full stored precision.
    n = len(reductions)
    mean_reduction_s = mean(reductions)
    sample_sd_s = stdev(reductions)
    standard_error_s = sample_sd_s / sqrt(n)

    # This Student's t critical value applies only to 29 degrees of freedom.
    if n != 30:
        raise ValueError(
            "This confidence-interval calculation requires 30 replications"
        )

    t_critical = 2.045229642
    margin_s = t_critical * standard_error_s

    ci_lower_s = mean_reduction_s - margin_s
    ci_upper_s = mean_reduction_s + margin_s

    fieldnames = [
        "scenario_name",
        "replication_id",
        "loading_seed",
        "flow_time_reduction_s",
    ]

    with open(
        output_filename, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(differences)

    # Report sample statistics for comparison with the analytical benchmark.
    print(f"Scenario: {scenario_name}")
    print(f"Paired replications: {len(reductions)}")
    print(f"Mean flow-time reduction: {mean(reductions):.4f} s")
    print(f"Sample standard deviation: {stdev(reductions):.4f} s")
    print(f"Minimum reduction: {min(reductions):.4f} s")
    print(f"Maximum reduction: {max(reductions):.4f} s")
    print(f"Saved {output_filename}")
    # Report uncertainty in the estimated mean paired reduction.
    print(f"Standard error: {standard_error_s:.4f} s")
    print(f"95% CI half-width: {margin_s:.4f} s")
    print(
        f"Approximate 95% CI for mean reduction: "
        f"[{ci_lower_s:.4f}, {ci_upper_s:.4f}] s"
    )

if __name__ == "__main__":
    main()