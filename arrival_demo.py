"""Simulate two robots serving three requests from a shared FIFO queue.

Requests arrive at 0, 10, and 130 seconds. Each robot loads for 5 seconds,
travels 2 meters at 0.1 m/s, unloads for 10 seconds, and returns empty.
The scenario demonstrates concurrent deliveries and independent robot
identities. Loading and unloading have no shared capacity limits yet.

All requests start immediately. The fleet finishes its final return
at 185 seconds.
"""

import simpy

from simulation import task_source, robot_worker

def main(num_robots=2):
    """Run the arrival scenario and display its delivery records."""

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
        task_source(env, tasks, task_queue, num_robots=len(robot_ids))
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

    delivery_per_robot = {}
    for robot_id in robot_ids:
        delivery_per_robot[robot_id] = 0

    for record in results:
        delivery_per_robot[record["robot_id"]] += 1

    print("\nDeliveries per robot:")
    for robot_id, count in delivery_per_robot.items():
        print(f"{robot_id}: {count}")

    for result in results:
        print(result)

    print(f"Completed deliveries: {len(results)}")
    print(f"Fleet finished at: {env.now} seconds")

    # Summarize delays across completed deliveries.
    completed = len(results)

    if completed > 0:
        mean_robot_wait_s = sum(
            record["waiting_time_s"] for record in results
        ) / completed

        mean_loading_wait_s = sum(
            record["loading_wait_time_s"] for record in results
        ) / completed

        mean_flow_time_s = sum(
            record["flow_time_s"] for record in results
        ) / completed

        print(f"Mean waiting for robot: {mean_robot_wait_s:.2f} s")
        print(f"Mean waiting for loading: {mean_loading_wait_s:.2f} s")
        print(f"Mean flow time: {mean_flow_time_s:.2f} s")


         # Return scenario metrics for comparison, CSV export, and plotting.
        return {
            "num_robots": num_robots,
            "completed_deliveries": completed,
            "fleet_finish_time_s": env.now,
            "mean_robot_wait_s": mean_robot_wait_s,
            "mean_loading_wait_s": mean_loading_wait_s,
            "mean_flow_time_s": mean_flow_time_s,
        }

if __name__ == "__main__":
    main()