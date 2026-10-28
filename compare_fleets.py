"""Compare one and two robots serving the same delivery requests.

Both scenarios use one loading station and identical arrival times,
travel parameters, and service durations defined in arrival_demo.
Collect one summary dictionary per fleet size for subsequent export
and plotting.
"""


# Use Python's built-in module to export the comparison.
import csv


from arrival_demo import main as run_scenario


def main():
    """Run both fleet configurations and display their summaries."""
    summaries = []

    # Change fleet size while keeping the scenario inputs fixed.
    for num_robots in [1, 2]:
        summary = run_scenario(num_robots=num_robots)
        summaries.append(summary)

    # Display the collected comparison after both simulations finish.
    print("\nFleet comparison:")
    for summary in summaries:
        print(summary)

        # Define a consistent column order for the comparison file.
    fieldnames = [
        "num_robots",
        "completed_deliveries",
        "fleet_finish_time_s",
        "mean_robot_wait_s",
        "mean_loading_wait_s",
        "mean_flow_time_s",
    ]

    # Replace the previous export with the results from this run.
    with open(
        "fleet_comparison.csv", "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print("\nSaved fleet_comparison.csv")


if __name__ == "__main__":
    main()