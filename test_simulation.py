"""Verify the deterministic single-robot baseline.

Five deliveries use a 2 m route, 0.1 m/s speed, 5 s loading,
and 10 s unloading. Each delivery takes 35 s, with a 20 s
empty return separating consecutive deliveries.
"""
import simpy

import unittest
from simulation import run_simulation, arrival_workflow
from simulation import task_source, robot_worker
"""Check delivery counts, orderm and timing for the baseline scenario."""

class TestSimulation(unittest.TestCase):

    def test_five_delivery_baseline(self):
        task_ids = ["T001", "T002", "T003", "T004", "T005"]

        results = run_simulation(
            task_ids=task_ids,
            distance_m=2.0,
            speed_m_s=0.1,
            loading_time_s=5,
            unloading_time_s=10
        )

        #Che that every requested delivery appears once and in order.
        self.assertEqual(len(results), len(task_ids))
        self.assertEqual(
            [record["task_id"] for record in results],
            task_ids
        )

        #Expected starts include the emppty return between deliveries.
        expected_starts = [0, 55, 110, 165, 220]
        expected_ends = [35, 90, 145, 200, 255]
        for i, record in enumerate(results):
            self.assertAlmostEqual(record["start_time_s"], expected_starts[i])
            self.assertAlmostEqual(record["end_time_s"], expected_ends[i])
            self.assertAlmostEqual(record["task_duration_s"], 35)

    def test_zero_speed_rejected(self):
        """Reject zero speed before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "speed_m_s must be greater than zero"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0,
                loading_time_s=5,
                unloading_time_s=10,
            )


    def test_negative_distance_rejected(self):
        """Reject negative distance before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "distance_m must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=-1.0,
                speed_m_s=0.1,
                loading_time_s=5,
                unloading_time_s=10,
            )


    def test_negative_loading_time_rejected(self):
        """Reject negative loading time before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "loading_time_s must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0.1,
                loading_time_s=-5,
                unloading_time_s=10,
            )

    def test_negative_unloading_time_rejected(self):
        """Reject negative unloading time before calculating travel duration."""
        with self.assertRaisesRegex(
            ValueError, "unloading_time_s must be nonnegative"
        ):
            run_simulation(
                task_ids=["T001"],
                distance_m=2.0,
                speed_m_s=0.1,
                loading_time_s=5,
                unloading_time_s=-10,
            )

    def test_arrivals_waiting_and_idle(self):
        """Verify that arrivals are queued and idle time is measured."""
        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 10},
            {"task_id": "T003", "arrival_time_s": 130},
        ]

        env = simpy.Environment()
        workflow = env.process(
            arrival_workflow(
                env, tasks, distance_m=2.0, speed_m_s=0.1,
                loading_time_s=5, unloading_time_s=10,
            )
        )
        env.run()
        results = workflow.value


        # Expected values come from the hand-calculated scenario.
        self.assertEqual(len(results), 3)
        expected_starts = [0, 55, 130]
        expected_waits = [0, 45, 0]
        expected_flows = [35, 80, 35]

        for i, record in enumerate(results):
            self.assertAlmostEqual(record["start_time_s"], expected_starts[i])
            self.assertAlmostEqual(record["waiting_time_s"], expected_waits[i])
            self.assertAlmostEqual(record["flow_time_s"], expected_flows[i])

        # Simulation completion includes the last empty return.
        self.assertAlmostEqual(env.now, 185)

        
    def test_negative_arrival_rejected(self):
        """Reject negative arrival times before calculating waiting time."""
        tasks = [
            {"task_id": "T001", "arrival_time_s":-1}
            ]

        env = simpy.Environment()

         # Validation runs when the simulation executes the process.
        with self.assertRaisesRegex(
            ValueError, "arrival_time_s must be nonnegative"
        ):
            env.process(
                arrival_workflow(
                    env, tasks, distance_m=2.0, speed_m_s=0.1,
                    loading_time_s=5, unloading_time_s=10,
                )
            )
            env.run()
        
    def test_unordered_arrival_rejected(self):
        """Reject unordered arrival times before calculating waiting time."""
        tasks = [
            {"task_id": "T001", "arrival_time_s": 10},
            {"task_id": "T002", "arrival_time_s": 5}
            ]

        env = simpy.Environment()

         # Validation runs when the simulation executes the process.
        with self.assertRaisesRegex(
            ValueError, "arrival_time_s must be nondecreasing"
        ):
            env.process(
                arrival_workflow(
                    env, tasks, distance_m=2.0, speed_m_s=0.1,
                    loading_time_s=5, unloading_time_s=10,
                )
            )
            env.run()


    def test_queue_based_deliveries(self):
        """Verify FIFO delivery records and completion after the final return."""
        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 10},
            {"task_id": "T003", "arrival_time_s": 130},
        ]

        # Connect independent arrivals and one robot through a shared queue.
        env = simpy.Environment()
        task_queue = simpy.Store(env)

        # Release requests independently while the robot performs deliveries.
        env.process(task_source(env, tasks, task_queue))

        worker = env.process(
            robot_worker(
                env, task_queue, distance_m=2.0, speed_m_s=0.1,
                loading_time_s=5, unloading_time_s=10,
            )
        )

        # Run through the robot's final return and explicit shutdown.
        env.run(until=worker)
        results = worker.value

        # confirm each task is served once in the arrival order.    

        self.assertEqual(len(results), 3)
        self.assertEqual(
            [record["task_id"] for record in results],
            ["T001", "T002", "T003"]
        )

        # Compare against the independently calculated benchmark.
        expected_starts = [0, 55, 130]
        expected_waits = [0, 45, 0]
        expected_flows = [35, 80, 35]

        for i, record in enumerate(results):
            self.assertAlmostEqual(record["start_time_s"], expected_starts[i])
            self.assertAlmostEqual(record["waiting_time_s"], expected_waits[i])
            self.assertAlmostEqual(record["flow_time_s"], expected_flows[i])
            # Each delivery must identify the worker that completed it.
            self.assertEqual(record["robot_id"], "R001")

          # The worker stops after its final return and consumes the stop signal.
        self.assertAlmostEqual(env.now, 185)
        self.assertEqual(task_queue.items, [])  # Stop signal remains in the queue.


    def test_two_robot_deliveries(self):
        """Verify concurrent deliveries and complete fleet shutdown."""

        # Use known arrivals so expected timings can be calculated by hand.
        tasks = [
            {"task_id": "T001", "arrival_time_s": 0},
            {"task_id": "T002", "arrival_time_s": 10},
            {"task_id": "T003", "arrival_time_s": 130},
        ]
        robot_ids = ["R001", "R002"]

        # Both workers receive tasks from the same queue.
        env = simpy.Environment()
        task_queue = simpy.Store(env)
        env.process(
            task_source(
                env, tasks, task_queue,
                num_robots=len(robot_ids),
            )
        )

        # Keep each process reference to inspect its results and completion.
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

        # Waiting for all workers exposes missing shutdown signals.
        env.run(until=env.all_of(workers))

        # Combine records without assuming which robot finishes first.
        results = []
        for worker in workers:
            self.assertTrue(worker.processed)
            results.extend(worker.value)

        # Count-aware comparison detects missing or duplicated deliveries.
        self.assertCountEqual(
            [record["task_id"] for record in results],
            ["T001", "T002", "T003"],
        )
        self.assertEqual(
            {record["robot_id"] for record in results},
            set(robot_ids),
        )

        # Match expected timings by task ID rather than collection order.
        expected = {
            "T001": (0, 35),
            "T002": (10, 45),
            "T003": (130, 165),
        }
        for record in results:
            expected_start, expected_end = expected[record["task_id"]]
            self.assertAlmostEqual(record["start_time_s"], expected_start)
            self.assertAlmostEqual(record["end_time_s"], expected_end)
            self.assertAlmostEqual(record["waiting_time_s"], 0)
            self.assertAlmostEqual(record["flow_time_s"], 35)

        # Completion includes the final return and consumption of both signals.
        self.assertAlmostEqual(env.now, 185)
        self.assertEqual(task_queue.items, [])