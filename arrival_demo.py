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

def main():
    """Run the arrival scenario and display its delivery records."""

    # Define the tasks with their arrival times.
    tasks = [
        {"task_id": "T001", "arrival_time_s": 0},
        {"task_id": "T002", "arrival_time_s": 10},
        {"task_id": "T003", "arrival_time_s": 130},
    ]

    # Run the simulation with specified parameters.
    env = simpy.Environment()
    task_queue = simpy.Store(env)

    #Release requests independently while the robot performs deliveries.

     # Give each robot an identity and send one shutdown signal per worker.
    robot_ids = ["R001", "R002"]

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

    for result in results:
        print(result)

    print(f"Completed deliveries: {len(results)}")
    print(f"Fleet finished at: {env.now} seconds")

if __name__ == "__main__":
    main()