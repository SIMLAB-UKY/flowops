"""Simulate one robot performing sequential material-handling deliveries.

Each task includes loading, loaded travel, unloading, and an empty return
to pickup. Configuration inputs are distance_m (one-way distance in meters),
speed_m_s (travel speed in meters per second), loading_time_s and
unloading_time_s (service durations in seconds), and task_ids (delivery
identifiers in execution order).

The model assumes constant speed, identical outbound and return routes,
and no congestion or resource contention. Console output reports event
times and delivery durations, excluding empty return travel. The robot
returns to pickup after the final delivery.
"""

import csv
import simpy

distance_m = 2.0
speed_m_s = 0.1
loading_time_s = 5
unloading_time_s = 10
task_ids = ["T001", "T002", "T003", "T004", "T005"]  # List of task IDs


# Accept a shared loading station while preserving the unconstrained baseline.
def transport_task(
    env, task_id, distance_m, speed_m_s,
    loading_time_s, unloading_time_s, loading_station=None
):
    """Execute a delivery, including any loading-station wait.

    start_time_s marks task handling before station access.
    task_duration_s includes station waiting but excludes empty return.
    """
    start_time_s = env.now
    if speed_m_s <= 0:
        raise ValueError("speed_m_s must be greater than zero")
    if distance_m < 0:
        raise ValueError("distance_m must be nonnegative")

    if loading_time_s < 0:
        raise ValueError("loading_time_s must be nonnegative")

    if unloading_time_s < 0:
        raise ValueError("unloading_time_s must be nonnegative")
    
    travel_time_s = distance_m / speed_m_s
    # Measure station waiting separately from waiting for an available robot.
    loading_request_time_s = env.now



    if loading_station is None:
        # The baseline allows loading to begin immediately.
        loading_start_time_s = env.now
        loading_wait_time_s = 0
        print(f"{env.now}: Task {task_id}: Loading started")
        yield env.timeout(loading_time_s)
        print(f"{env.now}: Task {task_id}: Loading completed")
    else:
        # Hold the shared station only during loading.
        with loading_station.request() as request:
            yield request

            loading_start_time_s = env.now
            loading_wait_time_s = env.now - loading_request_time_s
            print(f"{env.now}: Task {task_id}: Loading started")
            yield env.timeout(loading_time_s)
            print(f"{env.now}: Task {task_id}: Loading completed")


    print(f"{env.now}: Task {task_id}: Transport started")
    yield env.timeout(travel_time_s)
    print(f"{env.now}: Task {task_id}: Transport completed")
    print(f"{env.now}: Task {task_id}: Unloading started")
    yield env.timeout(unloading_time_s)
    print(f"{env.now}: Task {task_id}: Unloading completed")
    # Delivery duration excludes the empty return handled by robot_workflow.
    task_duration_s = env.now - start_time_s
    print(f"{env.now}: Task {task_id}: Total task duration: {task_duration_s} seconds")

    # Preserve task timing and expose the delay caused by loading capacity.
    return {
        "task_id": task_id,
        "start_time_s": start_time_s,
        "loading_start_time_s": loading_start_time_s,
        "loading_wait_time_s": loading_wait_time_s,
        "end_time_s": env.now,
        "task_duration_s": task_duration_s,
    }


def robot_workflow(env, task_ids, distance_m, speed_m_s,
                   loading_time_s, unloading_time_s):
    """Complete deliveries in order, returning to pickup after each."""
   
    results = []
    
    for tid in task_ids:
        # Complete one delivery before beginning the empty return.
        result = yield env.process(
            transport_task(
                env, tid, distance_m, speed_m_s,
                loading_time_s, unloading_time_s
            )
        )
        results.append(result)

        # Return to pickup using the same route and speed.
        print(f"{env.now}: Task {tid}: Empty return started")
        yield env.timeout(distance_m / speed_m_s)
        print(f"{env.now}: Task {tid}: Empty return completed")
    
    
    # Return all delivery records when the workflow finishes.
    return results         

def arrival_workflow(env, tasks, distance_m, speed_m_s,
                   loading_time_s, unloading_time_s):
    """Serve tasks in arrival order and record waiting and flow times.

    Tasks must have nonnegative arrival times in nondecreasing order.
    The robot returns to pickup after every delivery, including the last.
    """

    previous_arrival_time_s = 0
    for task in tasks:
        arrival_time_s = task["arrival_time_s"]
        if arrival_time_s < 0:
            raise ValueError("arrival_time_s must be nonnegative")
        if arrival_time_s < previous_arrival_time_s:
            raise ValueError("arrival_time_s must be nondecreasing")
        previous_arrival_time_s = arrival_time_s

    results = []

    for task in tasks:
        task_id = task["task_id"]
        arrival_time_s = task["arrival_time_s"]

        if env.now < arrival_time_s:
            # Wait until the task arrives.
            yield env.timeout(arrival_time_s - env.now)

        waiting_time_s = env.now - arrival_time_s

        result = yield env.process(
            transport_task(
                env, task_id, distance_m, speed_m_s,
                loading_time_s, unloading_time_s
            )
        )

        # Add waiting time to the result record.
        result["arrival_time_s"] = arrival_time_s
        result["waiting_time_s"] = waiting_time_s
        result["flow_time_s"] = result["end_time_s"] - arrival_time_s
        results.append(result)


        # return travel keep the robot busy until the next task arrives.
        yield env.timeout(distance_m / speed_m_s)

    return results


def task_source(env, tasks, task_queue, num_robots=1):
    """Release task records into a shared queue at their arrival times.

    Arrival times are absolute simulation times in seconds.
    Tasks must be listed in nondecreasing arrival order.
    """

    # A valid fleet size determines how many shutdown signals to send.
    if isinstance(num_robots, bool) or not isinstance(num_robots, int):
        raise ValueError("num_robots must be a positive integer")
    if num_robots < 1:
        raise ValueError("num_robots must be a positive integer")
    
    # Validate the complete schedule before releasing any requests.
    previous_arrival_s = 0
    for task in tasks:
        arrival_time_s = task["arrival_time_s"]

        if arrival_time_s < 0:
            raise ValueError("arrival_time_s must be nonnegative")
        if arrival_time_s < previous_arrival_s:
            raise ValueError("arrival_time_s must be nondecreasing")
        previous_arrival_s = arrival_time_s

    for task in tasks:
        #convert the absolute arrival time into a delay from the current simulation time.
        delay_s = task["arrival_time_s"] - env.now
        yield env.timeout(delay_s)

        # make therequest available independently of robot activity.

        yield task_queue.put(task)
        print(f"{env.now}: Task {task['task_id']}: Arrived")

    # Each worker consumes one stop signal and then returns its results.
    for _ in range(num_robots):
        yield task_queue.put(None)

def robot_worker(env, task_queue, distance_m, speed_m_s,
                 loading_time_s, unloading_time_s, robot_id="R001", loading_station=None):
    """Serve queued deliveries in FIFO order until a None stop signal.

    Record waiting and flow times in seconds. Complete an empty return
    after every delivery before requesting the next queue item.
    """

    results = []

    while True:
        # Wait for the next task to arrive in the queue.
        task = yield task_queue.get()

        # Stop explicitly after all preceding requests have been served.

        if task is None:
            return results

        task_id = task["task_id"]
        arrival_time_s = task["arrival_time_s"]
        waiting_time_s = env.now - arrival_time_s

        # Complete this delivery before beginning another request.
        result = yield env.process(
            transport_task(
                env, task_id, distance_m, speed_m_s,
                loading_time_s, unloading_time_s,
                loading_station=loading_station,
            )
        )

        # Preserve the arrival-based metrics alongside delivery timing.
        result["arrival_time_s"] = arrival_time_s
        result["waiting_time_s"] = waiting_time_s
        result["flow_time_s"] = result["end_time_s"] - arrival_time_s
        result["robot_id"] = robot_id
        results.append(result)

        # the robot remains occupied until it returns to pickup.
        print(f"{env.now}: Task {task_id}: Empty return started")
        yield env.timeout(distance_m / speed_m_s)
        print(f"{env.now}: Task {task_id}: Empty return completed")



def run_simulation(task_ids, distance_m, speed_m_s,
                   loading_time_s, unloading_time_s):
    """Run one robot's delivery sequence and return its delivery records."""
    # create the environment and start the robot workflow process
    env = simpy.Environment()

    # Keep the process reference so its results can be read after completion.
    workflow = env.process(
        robot_workflow(
            env, task_ids, distance_m, speed_m_s,
            loading_time_s, unloading_time_s
        )
    )

    env.run()

    # Retrieve the delivery records returned by the completed workflow.
    return workflow.value  # Access the results from the completed process
 

def main():
    """Run the robot workflow baseline simulation scenario, display results, and export delivery records."""
    # create the environment and start the robot workflow process
    results = run_simulation(
        task_ids, distance_m, speed_m_s,
        loading_time_s, unloading_time_s
    )
    print(f"\nCompleted deliveries: {len(results)}")
    for result in results:
        print(result)


    fieldnames = ["task_id", "start_time_s", "end_time_s", "task_duration_s"]
    with open("delivery_results.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)



if __name__ == "__main__":
    main()