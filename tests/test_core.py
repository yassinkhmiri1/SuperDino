"""Tests for pygame-free core game rules."""

from __future__ import annotations

from struct import unpack
import tempfile
import unittest
from pathlib import Path
from random import Random

from config import (
    BIRD_COLLISION_SPRITE_SIZE,
    BIRD_FRAME_PATHS,
    BIRD_HEIGHT_OFFSETS,
    BIRD_VERTICAL_SLOPE_PER_HORIZONTAL_PIXEL,
    DINO_CENTER_X,
    DINO_RUN_SPRITE_SIZE,
    GROUND_LINE_Y,
    GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
    MAX_PHYSICS_STEP_SECONDS,
    OBSTACLE_CULL_MARGIN,
    OBSTACLE_MAX_GAP_SECONDS,
    OBSTACLE_MIN_GAP_SECONDS,
    OBSTACLE_SPAWN_OFFSET,
    MAX_SPEED,
    SCORE_PER_PIXEL,
    SPEED_GROWTH_FACTOR,
    SPEED_STEP_SCORE,
    WINDOW_WIDTH,
)
from core.collision import Hitbox, hitboxes_overlap, obstacle_hitbox, player_hitbox
from core.high_score import load_high_score, save_high_score
from core.obstacles import (
    Obstacle,
    bird_vertical_offset,
    choose_obstacle_gap,
    update_obstacles,
)
from core.player import PlayerState, update_player
from core.score import ScoreState, advance_score
from core.speed import speed_for_score
from core.timing import physics_time_steps

class ObstacleRulesTests(unittest.TestCase):
    """Tests for deterministic obstacle spawning and movement."""

    def test_spawn_distance_scales_with_speed(self) -> None:
        """The same random gap in seconds scales linearly with speed."""
        low_speed_gap = choose_obstacle_gap(100.0, Random(42))
        high_speed_gap = choose_obstacle_gap(400.0, Random(42))

        self.assertEqual(high_speed_gap, low_speed_gap * 4)
        self.assertGreaterEqual(
            low_speed_gap,
            100.0 * OBSTACLE_MIN_GAP_SECONDS,
        )
        self.assertLessEqual(
            low_speed_gap,
            100.0 * OBSTACLE_MAX_GAP_SECONDS,
        )

    def test_update_spawns_valid_obstacle_at_right_edge(self) -> None:
        """An expired spawn distance creates an obstacle beyond the screen."""
        result = update_obstacles(
            obstacles=(),
            delta_seconds=0.0,
            speed=GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
            next_spawn_distance=0.0,
            randomizer=Random(1),
        )

        self.assertEqual(len(result.obstacles), 1)
        obstacle = result.obstacles[0]
        self.assertGreaterEqual(obstacle.x, WINDOW_WIDTH + OBSTACLE_SPAWN_OFFSET)
        self.assertIn(obstacle.kind, ("cactus", "bird"))
        self.assertGreater(result.next_spawn_distance, 0.0)

    def test_obstacles_move_and_are_culled_after_leaving_screen(self) -> None:
        """Obstacle positions advance by speed times elapsed seconds."""
        obstacle = Obstacle("cactus", 0, 500.0)
        moved = update_obstacles(
            (obstacle,),
            0.5,
            200.0,
            1_000.0,
            Random(0),
        )
        self.assertEqual(moved.obstacles[0].x, 400.0)

        culled = update_obstacles(
            (Obstacle("bird", 0, -OBSTACLE_CULL_MARGIN - 1.0),),
            0.0,
            200.0,
            1_000.0,
            Random(0),
        )
        self.assertEqual(culled.obstacles, ())

    def test_bird_flies_in_a_straight_diagonal(self) -> None:
        """Each bird maintains its selected vertical direction as it flies."""
        for direction in (-1, 1):
            bird = Obstacle("bird", 1, 500.0, bird_direction=direction)
            moved = update_obstacles(
                (bird,),
                0.5,
                200.0,
                1_000.0,
                Random(0),
            ).obstacles[0]

            self.assertEqual(moved.x, 400.0)
            self.assertEqual(moved.bird_direction, direction)
            self.assertAlmostEqual(
                bird_vertical_offset(moved),
                direction
                * 100.0
                * BIRD_VERTICAL_SLOPE_PER_HORIZONTAL_PIXEL,
            )

    def test_spawned_birds_start_in_random_opposite_directions(self) -> None:
        """New birds randomly choose a persistent upward or downward path."""
        randomizer = Random(19)
        birds = []
        for _ in range(100):
            spawned = update_obstacles(
                (),
                0.0,
                200.0,
                0.0,
                randomizer,
            ).obstacles
            birds.extend(obstacle for obstacle in spawned if obstacle.kind == "bird")

        directions = {bird.bird_direction for bird in birds}
        self.assertEqual(directions, {-1, 1})


class CollisionMathTests(unittest.TestCase):
    """Tests for collision hitboxes and overlap boundaries."""

    def test_player_and_cactus_hitboxes_are_tight(self) -> None:
        """Hitboxes detect real overlap while excluding image margins."""
        player = player_hitbox(PlayerState(), DINO_CENTER_X, GROUND_LINE_Y)
        cactus = obstacle_hitbox(
            Obstacle("cactus", 0, DINO_CENTER_X),
            GROUND_LINE_Y,
        )

        self.assertTrue(hitboxes_overlap(player, cactus))
        self.assertLess(player.left, player.right)
        self.assertLess(cactus.top, cactus.bottom)
        self.assertGreater(player.left, DINO_CENTER_X - DINO_RUN_SPRITE_SIZE[0] / 2)
        self.assertLess(player.right, DINO_CENTER_X + DINO_RUN_SPRITE_SIZE[0] / 2)

    def test_edge_contact_is_not_a_collision(self) -> None:
        """Touching rectangle edges without overlapping area is safe."""
        first = Hitbox(0.0, 0.0, 10.0, 10.0)
        second = Hitbox(10.0, 0.0, 20.0, 10.0)

        self.assertFalse(hitboxes_overlap(first, second))

    def test_jump_height_and_bird_height_affect_collision(self) -> None:
        """Vertical anchors correctly affect player and bird hitboxes."""
        airborne = PlayerState(ground_offset=120.0, grounded=False)
        player = player_hitbox(
            airborne,
            DINO_CENTER_X,
            GROUND_LINE_Y - airborne.ground_offset,
        )
        cactus = obstacle_hitbox(
            Obstacle("cactus", 0, DINO_CENTER_X),
            GROUND_LINE_Y,
        )
        bird = obstacle_hitbox(
            Obstacle("bird", len(BIRD_HEIGHT_OFFSETS) - 1, DINO_CENTER_X),
            GROUND_LINE_Y,
        )

        self.assertFalse(hitboxes_overlap(player, cactus))
        self.assertLess(bird.bottom, GROUND_LINE_Y)

    def test_bird_hitbox_uses_largest_animation_frame(self) -> None:
        """The collision envelope covers both differently sized bird frames."""
        frame_sizes = []
        for frame_path in BIRD_FRAME_PATHS:
            with frame_path.open("rb") as frame:
                header = frame.read(24)
            frame_sizes.append(unpack(">II", header[16:24]))

        largest_frame = (
            max(width for width, _ in frame_sizes),
            max(height for _, height in frame_sizes),
        )
        self.assertEqual(BIRD_COLLISION_SPRITE_SIZE, largest_frame)


class PhysicsTimingTests(unittest.TestCase):
    """Tests for stable physics updates across rendered frame durations."""

    def test_physics_steps_partition_elapsed_time(self) -> None:
        """Physics steps remain bounded and account for all elapsed time."""
        for delta_seconds in (0.0, 1 / 60, 0.1, 1.6):
            steps = tuple(physics_time_steps(delta_seconds))

            self.assertGreaterEqual(len(steps), 1)
            self.assertAlmostEqual(sum(steps), delta_seconds)
            self.assertLessEqual(max(steps), MAX_PHYSICS_STEP_SECONDS)

    def test_physics_steps_reject_invalid_elapsed_time(self) -> None:
        """Negative or non-finite elapsed time cannot enter the simulation."""
        for delta_seconds in (-0.1, float("nan"), float("inf")):
            with self.subTest(delta_seconds=delta_seconds):
                with self.assertRaises(ValueError):
                    tuple(physics_time_steps(delta_seconds))

    def test_substeps_detect_obstacles_crossing_during_a_stalled_frame(
        self,
    ) -> None:
        """Cacti and birds cannot pass through the player between checks."""
        for initial_obstacle in (
            Obstacle("cactus", 0, 400.0),
            Obstacle("bird", 0, 400.0),
        ):
            with self.subTest(kind=initial_obstacle.kind):
                obstacles = (initial_obstacle,)
                randomizer = Random(0)
                player = PlayerState()
                collided = False
                first_step = True

                for step_seconds in physics_time_steps(1.6):
                    obstacles = update_obstacles(
                        obstacles,
                        step_seconds,
                        GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
                        100_000.0,
                        randomizer,
                    ).obstacles
                    player = update_player(
                        player,
                        step_seconds,
                        jump_pressed=first_step,
                        duck_held=False,
                    )
                    first_step = False
                    player_box = player_hitbox(
                        player,
                        DINO_CENTER_X,
                        GROUND_LINE_Y - player.ground_offset,
                    )
                    collided = any(
                        hitboxes_overlap(
                            player_box,
                            obstacle_hitbox(obstacle, GROUND_LINE_Y),
                        )
                        for obstacle in obstacles
                    )
                    if collided:
                        break

                self.assertTrue(collided)


class ScoreRulesTests(unittest.TestCase):
    """Tests for distance-based scoring and speed progression."""

    def test_score_accumulates_distance_across_updates(self) -> None:
        """Fractional score carries over between updates."""
        first = advance_score(ScoreState(), 0.5, 10.0)
        second = advance_score(first, 0.5, 10.0)

        self.assertEqual(first.points, 0)
        self.assertAlmostEqual(first.score_remainder, 0.15)
        self.assertEqual(second.points, 0)
        self.assertAlmostEqual(second.score_remainder, 0.3)

    def test_score_gain_scales_with_distance_and_speed(self) -> None:
        """One second at higher speed earns proportionally more score."""
        base_speed_score = advance_score(ScoreState(), 1.0, 330.0)
        higher_speed_score = advance_score(ScoreState(), 1.0, 500.0)
        base_total = (
            base_speed_score.points + base_speed_score.score_remainder
        )
        higher_total = (
            higher_speed_score.points + higher_speed_score.score_remainder
        )

        self.assertAlmostEqual(base_total, 330.0 * SCORE_PER_PIXEL)
        self.assertAlmostEqual(higher_total, 500.0 * SCORE_PER_PIXEL)
        self.assertGreater(higher_total, base_total)

    def test_score_is_independent_of_time_step_partition(self) -> None:
        """Two small steps award the same score as one equivalent long step."""
        one_step = advance_score(ScoreState(), 1.0, 330.0)
        two_steps = advance_score(
            advance_score(ScoreState(), 0.5, 330.0),
            0.5,
            330.0,
        )

        self.assertEqual(two_steps.points, one_step.points)
        self.assertAlmostEqual(
            two_steps.score_remainder,
            one_step.score_remainder,
        )

    def test_speed_matches_compounding_model_at_requested_scores(self) -> None:
        """Speed follows the compounding formula through the cap."""
        base_speed = GROUND_SCROLL_SPEED_PIXELS_PER_SECOND
        cap_score = next(
            score
            for score in range(0, 100_000, SPEED_STEP_SCORE)
            if base_speed
            * SPEED_GROWTH_FACTOR ** (score // SPEED_STEP_SCORE)
            >= MAX_SPEED
        )

        for score in (0, 99, 100, 1_000, 3_000, cap_score):
            expected = min(
                base_speed
                * SPEED_GROWTH_FACTOR ** (score // SPEED_STEP_SCORE),
                MAX_SPEED,
            )
            with self.subTest(score=score):
                self.assertAlmostEqual(speed_for_score(score), expected)

    def test_speed_never_decreases_as_score_increases(self) -> None:
        """The capped growth model is monotonic for all tested scores."""
        speeds = [speed_for_score(score) for score in range(0, 10_001)]

        self.assertTrue(
            all(previous <= current for previous, current in zip(speeds, speeds[1:]))
        )
        self.assertEqual(speeds[-1], MAX_SPEED)

    def test_score_rejects_invalid_elapsed_time(self) -> None:
        """Negative or non-finite elapsed time is rejected."""
        for delta_seconds in (-0.1, float("nan"), float("inf")):
            with self.subTest(delta_seconds=delta_seconds):
                with self.assertRaises(ValueError):
                    advance_score(ScoreState(), delta_seconds, 100.0)

    def test_jump_duration_and_distance_are_longer(self) -> None:
        """The simulated jump provides enough airtime to clear obstacles."""
        player = update_player(PlayerState(), 0.0, True, False)
        elapsed_seconds = 0.0
        frame_duration = 1.0 / 60.0
        peak_height = 0.0
        while not player.grounded:
            player = update_player(player, frame_duration, False, False)
            peak_height = max(peak_height, player.ground_offset)
            elapsed_seconds += frame_duration
        horizontal_distance = (
            elapsed_seconds * GROUND_SCROLL_SPEED_PIXELS_PER_SECOND
        )

        self.assertGreater(elapsed_seconds, 0.8)
        self.assertGreater(horizontal_distance, 270.0)
        self.assertLessEqual(peak_height, 205.0)
        self.assertEqual(player.ground_offset, 0.0)


class HighScoreStorageTests(unittest.TestCase):
    """Tests for atomic high-score persistence."""

    def test_high_score_round_trip_uses_atomic_replacement(self) -> None:
        """Saved scores can be loaded and leave no temporary files."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "high_score.txt"

            save_high_score(path, 1_234)

            self.assertEqual(load_high_score(path), 1_234)
            self.assertEqual(path.read_text(encoding="utf-8"), "1234\n")
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_reset_to_zero_uses_atomic_replacement(self) -> None:
        """A reset persists zero and leaves no temporary file behind."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "high_score.txt"
            save_high_score(path, 1_234)

            save_high_score(path, 0)

            self.assertEqual(load_high_score(path), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), "0\n")
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_missing_or_corrupt_high_score_starts_from_zero(self) -> None:
        """Missing and invalid contents return zero with warnings."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "high_score.txt"
            with self.assertLogs("core.high_score", level="WARNING"):
                self.assertEqual(load_high_score(path), 0)

            path.write_text("not a score", encoding="utf-8")
            with self.assertLogs("core.high_score", level="WARNING"):
                self.assertEqual(load_high_score(path), 0)

    def test_score_rate_matches_configured_score_per_pixel(self) -> None:
        """The base-speed rate equals distance times configured score rate."""
        state = advance_score(
            ScoreState(),
            1.0,
            GROUND_SCROLL_SPEED_PIXELS_PER_SECOND,
        )
        self.assertAlmostEqual(
            state.points + state.score_remainder,
            GROUND_SCROLL_SPEED_PIXELS_PER_SECOND * SCORE_PER_PIXEL,
        )


if __name__ == "__main__":
    unittest.main()
