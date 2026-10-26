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


import simpy

distance_m = 2.0
speed_m_s = 0.1
loading_time_s = 5
unloading_time_s = 10
task_ids = ["T001", "T002", "T003", "T004", "T005"]  # List of task IDs

def transport_task(env, task_id, distance_m, speed_m_s, loading_time_s, unloading_time_s):
    """Execute one delivery from loading through unloading."""
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


def robot_workflow(env, task_ids=task_ids, distance_m=distance_m, speed_m_s=speed_m_s, loading_time_s=loading_time_s, unloading_time_s=unloading_time_s):
    """Complete deliveries in order, returning to pickup after each."""
    for tid in task_ids:
        yield env.process(transport_task(env, tid, distance_m, speed_m_s, loading_time_s, unloading_time_s))
        print(f"{env.now}: Task {tid}: Empty Return started")
        # Empty return uses the same distance and speed as loaded travel.
        yield env.timeout(distance_m / speed_m_s)
        print(f"{env.now}: Task {tid}: Empty Return completed")


env = simpy.Environment()
env.process(robot_workflow(env, task_ids=task_ids, distance_m=distance_m, speed_m_s=speed_m_s, loading_time_s=loading_time_s, unloading_time_s=unloading_time_s))
env.run()