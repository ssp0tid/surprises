"""Main application."""

from __future__ import annotations

import signal
import sys
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Static

from .game import GameContext, GameState
from .game.engine import GameLoop, GameLoopDriver
from .game.entities.base import EntityFactory
from .game.systems import (
    CollisionSystem,
    MovementSystem,
    SpawnerSystem,
    SpawnConfig,
    DifficultySystem,
    ScoringSystem,
)
from .input.handler import InputHandler, InputAction
from .persistence.high_scores import HighScoreManager
from .ui.menu_screen import MenuScreen, StartGameEvent, ShowHighScoresEvent, QuitGameEvent
from .ui.pause_screen import PauseScreen
from .ui.game_over_screen import GameOverScreen
from .ui.high_scores_screen import HighScoresScreen
from .ui.game_screen import GameScreen
from .ui.hud import HUD
from .game.config import CONFIG


class AsteroidRunnerApp(App):
    """Main application class for Asteroid Runner."""

    CSS = """
    Screen {
        background: $surface;
    }

    #title-art {
        width: 100%;
        height: auto;
        content-align: center middle;
        color: $accent;
    }

    .title {
        width: 100%;
        text-align: center;
    }

    .ship {
        width: 100%;
        text-align: center;
        color: $success;
    }

    #menu-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        width: 20;
    }

    Button.selected {
        background: $accent;
        color: $text;
    }

    .hint {
        width: 100%;
        text-align: center;
        color: $text-muted;
    }

    #game-container {
        width: 100%;
        height: 100%;
    }

    #hud {
        width: 100%;
        height: 1;
        color: $text;
    }

    #game-screen {
        width: 100%;
        height: 100%;
    }

    #pause-content {
        width: 30;
        height: auto;
        align: center middle;
        background: $surface;
        border: solid $accent;
    }

    #pause-title {
        width: 100%;
        text-align: center;
        color: $accent;
    }

    #gameover-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #gameover-title {
        width: 100%;
        text-align: center;
        color: $error;
    }

    #gameover-stats {
        width: 100%;
        text-align: center;
    }

    .highlight {
        width: 100%;
        text-align: center;
        color: $warning;
    }

    #scores-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    .score-entry {
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS = [
        Binding("escape", "handle_escape", "Handle Escape", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._context = GameContext()
        self._input_handler = InputHandler()
        self._high_score_manager = HighScoreManager()

        self._collision_system = CollisionSystem()
        self._movement_system = MovementSystem(
            world_width=CONFIG.DEFAULT_WIDTH,
            world_height=CONFIG.DEFAULT_HEIGHT,
        )
        self._spawner_system = SpawnerSystem(
            config=SpawnConfig(),
            world_width=CONFIG.DEFAULT_WIDTH,
            world_height=CONFIG.DEFAULT_HEIGHT,
        )
        self._difficulty_system = DifficultySystem()
        self._scoring_system = ScoringSystem(self._difficulty_system)

        self._spawner_system.register_factory("asteroid", EntityFactory.create_asteroid)
        self._spawner_system.register_factory("enemy", EntityFactory.create_enemy)

        self._game_loop: Optional[GameLoop] = None
        self._game_loop_driver: Optional[GameLoopDriver] = None

        self._game_screen: Optional[GameScreen] = None
        self._hud: Optional[HUD] = None

        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self._cleanup()
        sys.exit(0)

    def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        if self._game_loop:
            self._game_loop.stop()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield MenuScreen(id="menu-screen")

    def on_mount(self) -> None:
        """Initialize the application."""
        self._context.state_machine.on_transition(self._on_state_change)

    def _on_state_change(self, from_state: GameState, to_state: GameState) -> None:
        """Handle state transitions."""
        if to_state == GameState.PLAYING:
            self._start_game()
        elif to_state == GameState.PAUSED:
            self._pause_game()
        elif to_state == GameState.MENU:
            self._show_menu()
        elif to_state == GameState.GAME_OVER:
            self._show_game_over()
        elif to_state == GameState.HIGH_SCORES:
            self._show_high_scores()

    def _start_game(self) -> None:
        """Initialize and start a new game."""
        self._context.reset_session()
        self._context.state_machine.transition(GameState.PLAYING)

        self._context.player = EntityFactory.create_player()
        self._context.player.position.x = self._context.world_width // 2
        self._context.player.position.y = self._context.world_height - 5

        self._context.session.health = CONFIG.PLAYER_MAX_HEALTH
        self._context.session.max_health = CONFIG.PLAYER_MAX_HEALTH

        self._spawner_system.reset_timers()
        self._input_handler.reset()
        self._scoring_system = ScoringSystem(self._difficulty_system)

        self.mount(GameScreen(id="game-screen"), before="#menu-screen")
        self.mount(HUD(id="hud"), before="#game-screen")

        self._game_screen = self.query_one("#game-screen", GameScreen)
        self._hud = self.query_one("#hud", HUD)

        self._game_loop = GameLoop(
            update_callback=self._update,
            render_callback=self._render,
            input_callback=self._process_input,
        )
        self._game_loop_driver = GameLoopDriver(self._game_loop)
        self._game_loop.start()

        self.set_interval(1 / 60, self._tick)

    def _tick(self) -> None:
        """Called every frame."""
        if self._game_loop and self._game_loop.is_running:
            self._game_loop.tick()

    def _process_input(self) -> None:
        """Process input state."""
        state = self._input_handler.state

        if not self._context.player or not self._context.player.active:
            return

        speed = CONFIG.PLAYER_SPEED

        if state.up:
            self._context.player.velocity.vy = -speed
        elif state.down:
            self._context.player.velocity.vy = speed
        else:
            self._context.player.velocity.vy = 0

        if state.left:
            self._context.player.velocity.vx = -speed
        elif state.right:
            self._context.player.velocity.vx = speed
        else:
            self._context.player.velocity.vx = 0

        if state.shoot and self._input_handler.can_shoot():
            self._fire_bullet()
            self._input_handler.fire_shot()

    def _fire_bullet(self) -> None:
        """Fire a bullet from the player."""
        if not self._context.player:
            return

        bullet = EntityFactory.create_bullet(
            x=self._context.player.position.x,
            y=self._context.player.position.y - 2,
            vy=-CONFIG.PLAYER_BULLET_SPEED,
            is_player=True,
        )
        self._context.entities[bullet.id] = bullet
        self._context.session.shots_fired += 1

    def _update(self, dt: float) -> None:
        """Update game state."""
        if self._context.state_machine.state != GameState.PLAYING:
            return

        self._input_handler.update(dt)

        self._spawner_system.update(self._context, dt)
        self._movement_system.update(self._context, dt)

        collisions = self._collision_system.detect_collisions(self._context)
        self._handle_collisions(collisions)

        self._cleanup_dead_entities()

        self._context.session.play_time += dt
        self._context.session.health = (
            self._context.player.health.current
            if self._context.player and self._context.player.health
            else 0
        )

        if self._context.player and self._context.player.health:
            if self._context.player.health.current <= 0:
                self._game_over()

    def _handle_collisions(self, collisions: list[tuple]) -> None:
        """Process collision results."""
        for entity_a, entity_b in collisions:
            effects = self._collision_system.resolve_collision(entity_a, entity_b)

            for effect in effects:
                if effect.startswith("score_"):
                    points = int(effect.split("_")[1])
                    final_points = self._scoring_system.add_kill(points)
                    self._context.add_score(final_points)
                    self._context.session.enemies_killed += 1
                    self._context.session.shots_hit += 1
                elif effect.startswith("destroy_"):
                    entity_a.active = False
                    entity_b.active = False

                    explosion_a = EntityFactory.create_explosion(
                        entity_a.position.x, entity_a.position.y
                    )
                    self._context.entities[explosion_a.id] = explosion_a

                    explosion_b = EntityFactory.create_explosion(
                        entity_b.position.x, entity_b.position.y
                    )
                    self._context.entities[explosion_b.id] = explosion_b
                elif effect.startswith("damage_"):
                    if "PLAYER" in effect and self._context.player:
                        self._scoring_system.take_damage()

    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities."""
        self._context.entities = {
            eid: entity for eid, entity in self._context.entities.items() if entity.active
        }

    def _render(self, alpha: float) -> None:
        """Render the game."""
        if self._game_screen:
            self._game_screen.refresh()
        if self._hud and self._context.player:
            self._hud.update(
                score=self._context.session.score,
                level=self._context.session.level,
                health=self._context.session.health,
                max_health=self._context.session.max_health,
                fps=self._game_loop.stats.fps if self._game_loop else 60.0,
            )

    def _pause_game(self) -> None:
        """Pause the game."""
        if self._game_loop:
            self._game_loop.pause()

        menu_screen = self.query_one("#menu-screen", MenuScreen)
        menu_screen.remove()

        pause_screen = PauseScreen(id="pause-screen")
        self.mount(pause_screen, before="#game-screen")

    def _resume_game(self) -> None:
        """Resume the game."""
        if self._game_loop:
            self._game_loop.resume()

        pause_screen = self.query_one("#pause-screen", PauseScreen)
        pause_screen.remove()

    def _game_over(self) -> None:
        """Handle game over."""
        if self._game_loop:
            self._game_loop.stop()

        self._context.state_machine.transition(GameState.GAME_OVER)

    def _show_menu(self) -> None:
        """Show the main menu."""
        for screen_id in ["game-screen", "hud", "pause-screen", "gameover-screen", "scores-screen"]:
            screen = self.query_one(f"#{screen_id}", Container)
            screen.remove()

        if not self.query_one("#menu-screen", MenuScreen):
            self.mount(MenuScreen(id="menu-screen"))

    def _show_game_over(self) -> None:
        """Show game over screen."""
        for screen_id in ["game-screen", "hud", "pause-screen"]:
            existing = self.query(screen_id)
            if existing:
                existing.remove()

        is_high_score = self._high_score_manager.is_high_score(self._context.session.score)

        gameover_screen = GameOverScreen(
            score=self._context.session.score,
            level=self._context.session.level,
            kills=self._context.session.enemies_killed,
            is_high_score=is_high_score,
            id="gameover-screen",
        )
        self.mount(gameover_screen)

        if is_high_score:
            self._high_score_manager.add_score("PLAYER", self._context.session.score)

    def _show_high_scores(self) -> None:
        """Show high scores screen."""
        for screen_id in ["game-screen", "hud", "pause-screen", "gameover-screen"]:
            existing = self.query(screen_id)
            if existing:
                existing.remove()

        scores = self._high_score_manager.get_scores()
        scores_screen = HighScoresScreen(scores=scores, id="scores-screen")
        self.mount(scores_screen)

    def action_handle_escape(self) -> None:
        """Handle escape key."""
        state = self._context.state_machine.state

        if state == GameState.PLAYING:
            self._context.state_machine.transition(GameState.PAUSED)
        elif state == GameState.PAUSED:
            self._resume_game()

    def on_key(self, event) -> None:
        """Handle key events."""
        if hasattr(event, "key"):
            action = self._input_handler.process_key(event)
            if action == InputAction.PAUSE:
                self.action_handle_escape()

    def on_menu_screen_start_game(self, event: StartGameEvent) -> None:
        """Handle start game request."""
        self._context.state_machine.transition(GameState.PLAYING)

    def on_menu_screen_show_high_scores(self, event: ShowHighScoresEvent) -> None:
        """Handle show high scores request."""
        self._context.state_machine.transition(GameState.HIGH_SCORES)

    def on_menu_screen_quit_game(self, event: QuitGameEvent) -> None:
        """Handle quit request."""
        self._cleanup()
        self.exit()

    def on_pause_screen_resume(self, event: PauseScreen.Resume) -> None:
        """Handle resume request."""
        self._resume_game()

    def on_pause_screen_restart(self, event: PauseScreen.Restart) -> None:
        """Handle restart request."""
        pause_screen = self.query_one("#pause-screen", PauseScreen)
        pause_screen.remove()
        self._context.state_machine.transition(GameState.PLAYING)

    def on_pause_screen_quit(self, event: PauseScreen.Quit) -> None:
        """Handle quit to menu request."""
        self._context.state_machine.transition(GameState.MENU)

    def on_game_over_screen_play_again(self, event: GameOverScreen.PlayAgain) -> None:
        """Handle play again request."""
        gameover_screen = self.query_one("#gameover-screen", GameOverScreen)
        gameover_screen.remove()
        self._context.state_machine.transition(GameState.PLAYING)

    def on_game_over_screen_main_menu(self, event: GameOverScreen.MainMenu) -> None:
        """Handle main menu request."""
        self._context.state_machine.transition(GameState.MENU)

    def on_high_scores_screen_back(self, event: HighScoresScreen.Back) -> None:
        """Handle back request."""
        self._context.state_machine.transition(GameState.MENU)
