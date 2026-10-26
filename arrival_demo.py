"""Run a three-request scenario demonstrating robot queues and idle time.

Arrival times are measured in seconds from simulation start.
The scenario includes one request that queues and one that arrives
after the robot has returned to pickup.
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

    env.process(task_source(env, tasks, task_queue))

    worker = env.process(
        robot_worker(
            env, task_queue, distance_m=2.0, speed_m_s=0.1,
            loading_time_s=5, unloading_time_s=10,
        )
    )

    # Run through the robot's final return and explicit shutdown.
    env.run(until=worker)

    for result in worker.value:
        print(result)
    print(f"Robot finished at: {env.now} seconds")



if __name__ == "__main__":
    main()