"""Compare robot fleets serving three requests through one loading station.

Requests arrive at 0, 0, and 130 seconds. Each delivery requires loading
for 5 seconds, traveling 2 meters at 0.1 m/s, and unloading for 10 seconds,
followed by an empty return. Robots share a FIFO task queue and one
loading position. Travel and unloading have no shared capacity limits.

run_scenario returns delivery records, per-robot counts, and a performance
summary. main displays these outputs for an interactive demonstration.
All time measures use seconds.
"""

import simpy

from simulation import task_source, robot_worker
from metrics import summarize_results

def run_scenario(num_robots=2, verbose=True):
    """Run the fixed arrival scenario and return its records and metrics."""

        # Simultaneous requests reveal whether loading capacity is constrained.
    tasks = [
        {"task_id": "T001", "arrival_time_s": 0},
        {"task_id": "T002", "arrival_time_s": 0},
        {"task_id": "T003", "arrival_time_s": 130},
    ]

    # Run the simulation with specified parameters.
    env = simpy.Environment()
    task_queue = simpy.Store(env)
    
    # All robots share this single loading position.
    loading_station = simpy.Resource(env, capacity=1)

    #Release requests independently while the robot performs deliveries.

     # Give each robot an identity and send one shutdown signal per worker.
        # Reject invalid fleet sizes before creating workers.
    if isinstance(num_robots, bool) or not isinstance(num_robots, int):
        raise ValueError("num_robots must be a positive integer")
    if num_robots < 1:
        raise ValueError("num_robots must be a positive integer")

    # Generate R001, R002, and so on for the requested fleet size.
    robot_ids = []
    for i in range(num_robots):
        robot_ids.append(f"R{i + 1:03d}")

    env.process(
        task_source(env, tasks, task_queue, num_robots=len(robot_ids), verbose=verbose)
    )

    # Start independent robot processes that share the task queue.
    workers = []

    for robot_id in robot_ids:
        worker = env.process(
            robot_worker(
                env, task_queue,
                distance_m=2.0,
                speed_m_s=0.1,
                loading_time_s=5,
                unloading_time_s=10,
                robot_id=robot_id,
                loading_station=loading_station,
                verbose=verbose,
            )
        )
        workers.append(worker)

        # Finish the simulation only after every robot process has completed.
    env.run(until=env.all_of(workers))
     # Combine each robot's delivery records into one fleet result list.
    results = []
    for worker in workers:
        results.extend(worker.value)

    # Display records in service-start order.
    results.sort(key=lambda record: record["start_time_s"])

    # Include every robot, even if it completes no deliveries.
    delivery_per_robot = {}
    for robot_id in robot_ids:
        delivery_per_robot[robot_id] = 0

    # Count completed deliveries using the recorded robot identities.
    for record in results:
        delivery_per_robot[record["robot_id"]] += 1

    # Calculate metrics after all workers finish their final empty returns.
    summary = summarize_results(
        results,
        num_robots=num_robots,
        fleet_finish_time_s=env.now,
    )

    # Return structured data so callers can display, export, or analyze it.
    return {
        "results": results,
        "deliveries_per_robot": delivery_per_robot,
        "summary": summary,
    }


def main(num_robots=2):
    """Run the demonstration, display its outputs, and return its summary."""

    # Retrieve the structured outputs from the simulation runner.
    output = run_scenario(num_robots=num_robots)
    results = output["results"]
    deliveries_per_robot = output["deliveries_per_robot"]
    summary = output["summary"]

    # Display how completed deliveries were distributed across the fleet.
    print("\nDeliveries per robot:")
    for robot_id, count in deliveries_per_robot.items():
        print(f"{robot_id}: {count}")

    for result in results:
        print(result)

    # Round only the displayed values; preserve precision in the dictionary.
    print(f"Completed deliveries: {summary['completed_deliveries']}")
    print(f"Fleet finished at: {summary['fleet_finish_time_s']:.1f} seconds")
    print(f"Mean waiting for robot: {summary['mean_robot_wait_s']:.2f} s")
    print(f"Mean waiting for loading: {summary['mean_loading_wait_s']:.2f} s")
    print(f"Mean flow time: {summary['mean_flow_time_s']:.2f} s")

    # Preserve the current interface used by compare_fleets.py.
    return summary

if __name__ == "__main__":
    main()