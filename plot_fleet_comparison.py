"""Plot the components of mean delivery flow time by fleet size.

Read fleet_comparison.csv and save fleet_comparison.png.
Stack mean waiting for a robot, mean waiting for loading capacity,
and active delivery time. All durations are in seconds and exclude
empty return travel.
"""

import csv
import matplotlib.pyplot as plt


def main():
    """Read the scenario summaries and create a comparison chart."""

    # Read one dictionary per fleet configuration.
    with open("fleet_comparison.csv", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    # Convert CSV strings into numeric values for plotting.
    fleet_sizes = [int(row["num_robots"]) for row in rows]
    robot_wait = [float(row["mean_robot_wait_s"]) for row in rows]
    loading_wait = [float(row["mean_loading_wait_s"]) for row in rows]
    flow_time = [float(row["mean_flow_time_s"]) for row in rows]
        # Recover active delivery time without counting either wait twice.
    active_time = [
        flow - robot - loading
        for flow, robot, loading in zip(flow_time, robot_wait, loading_wait)
    ]
    combined_wait = [
        robot + loading
        for robot, loading in zip(robot_wait, loading_wait)
    ]

    # Stack the components so each bar's total height equals mean flow time.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(fleet_sizes, robot_wait, label="Waiting for robot", color="#DB982A")
    ax.bar(
        fleet_sizes, loading_wait, bottom=robot_wait,
        label="Waiting for loading station", color="#3996C6",
    )
    ax.bar(
        fleet_sizes, active_time, bottom=combined_wait,
        label="Active delivery", color="#203E96",
    )

    # Label each bar with its total mean flow time.
    for fleet_size, total in zip(fleet_sizes, flow_time):
        ax.text(
            fleet_size, total + 1, f"{total:.2f} s",
            ha="center", va="bottom",
        )

    ax.set_xlabel("Number of robots")
    ax.set_ylabel("Mean flow time (s)")
    ax.set_title("Fleet comparison with one shared loading station")
    ax.set_xticks(fleet_sizes)
    ax.set_ylim(0, max(flow_time) * 1.25)
    ax.legend()
    fig.tight_layout()

    # Save a reproducible figure suitable for the repository README.
    fig.savefig("fleet_comparison.png", dpi=200)
    plt.close(fig)
    print("Saved fleet_comparison.png")

# Run the plotting workflow only when this file is executed directly.
if __name__ == "__main__":
    main()