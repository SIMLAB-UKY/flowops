"""Plot paired flow-time reductions for the simultaneous-arrival scenario.

The left panel shows individual replication differences. The right panel
shows the sample mean and an approximate 95% Student's t confidence
interval. Both panels include the analytical mean of 35 seconds.

The confidence-interval critical value requires exactly 30 replications.
All reductions use seconds. Positive values favor the two-robot fleet.
"""

import csv
from math import sqrt
from statistics import mean, stdev

import matplotlib.pyplot as plt


def main():
    """Read paired results and plot variability separately from mean uncertainty."""

    scenario_name = "simultaneous_arrivals"
    input_filename = f"paired_differences_{scenario_name}.csv"
    output_filename = f"paired_differences_{scenario_name}.png"

    # Convert CSV text into numerical observations.
    with open(input_filename, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if any(row["scenario_name"] != scenario_name for row in rows):
        raise ValueError("The file contains an unexpected scenario")

    rows.sort(key=lambda row: int(row["replication_id"]))

    replication_ids = [int(row["replication_id"]) for row in rows]
    reductions = [float(row["flow_time_reduction_s"]) for row in rows]

    # Use the same interval calculation as the analysis script.
    n = len(reductions)
    if n != 30:
        raise ValueError("This plot requires 30 paired replications")

    mean_reduction_s = mean(reductions)
    standard_error_s = stdev(reductions) / sqrt(n)
    margin_s = 2.045229642 * standard_error_s

    # A shared vertical scale makes the two panels directly comparable.
    fig, axes = plt.subplots(
        1, 2, figsize=(11, 5), sharey=True,
        gridspec_kw={"width_ratios": [2, 1]},
        constrained_layout=True,
    )

    # Individual points describe variation between sampled workloads.
    axes[0].scatter(
        replication_ids, reductions,
        color="#203E96", label="Replication reduction",
    )
    axes[0].set_title("Individual paired replications")
    axes[0].set_xlabel("Replication")
    axes[0].set_ylabel("Mean flow-time reduction (s)")

    # The error bar describes uncertainty in the estimated population mean.
    axes[1].errorbar(
        [1], [mean_reduction_s],
        yerr=[margin_s],
        fmt="o", capsize=8,
        color="#203E96",
        label="Sample mean and 95% CI",
    )
    axes[1].set_title("Estimated mean benefit")
    axes[1].set_xticks([1])
    axes[1].set_xticklabels(["Two robots versus one"])
    axes[1].set_xlim(0.5, 1.5)

    # Show the known theoretical mean on both panels.
    for ax in axes:
        ax.axhline(
            35.0, color="#D99024", linestyle="--",
            label="Analytical mean: 35 s",
        )
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=9)

    fig.suptitle("Simultaneous arrivals: paired fleet comparison")
    fig.savefig(output_filename, dpi=200)
    plt.close(fig)

    print(f"Saved {output_filename}")


if __name__ == "__main__":
    main()