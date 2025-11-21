"""
Group 2 Flood Control Game - Ant Colony Optimization
Main game module with comprehensive ACO parameter controls
"""

import pygame
import math
from config import *
from aco import City, Ant, ACO


class Game:
    """Main game controller with ACO parameter controls"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Group 2 - Ant Colony Optimization")
        self.clock = pygame.time.Clock()
        
        # Layout state
        self.cell_size = CELL_SIZE
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.recalculate_layout(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        
        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 32)
        self.tiny_font = pygame.font.Font(None, 16)
        
        # Configuration
        self.starting_budget = DEFAULT_BUDGET
        self.rain_intensity = RAIN_INTENSITY_DEFAULT
        
        # ACO Parameters (user-configurable)
        self.num_ants = DEFAULT_NUM_ANTS
        self.alpha = ACO_ALPHA
        self.beta = ACO_BETA
        self.evaporation_rate = DEFAULT_EVAPORATION_RATE
        
        self.city = City(GRID_SIZE, self.starting_budget)
        self.aco = None
        self.running = True
        self.budget_remaining = self.starting_budget
        self.total_budget_spent = 0
        
        # Game phase system
        self.phase = GamePhase.SETUP
        self.show_tutorial = True
        
        # Visual modes
        self.show_elevation = False
        self.show_pheromones = False
        self.show_water = True
        self.show_grid = True
        self.show_icons = True
        
        # Game state
        self.survival_time = 0
        self.water_history = []
        self.total_pipe_cost = 0
        
        # UI state
        self.dragging_budget = False
        self.dragging_rain = False
        self.dragging_ants = False
        self.dragging_alpha = False
        self.dragging_beta = False
        self.dragging_evap = False
        
        # Animation
        self.blink_timer = 0
        self.pulse_animation = 0
        self.hover_cell = None
        self.aco_iteration_delay = 0  # Delay counter for visible ACO iterations
        self.iterations_per_frame = 1  # How many ACO iterations per frame
        self.animation_speed = 1 # Default animation speed
        self.dragging_speed = False
        
    def recalculate_layout(self, width, height):
        """Recalculate grid size and position based on window size"""
        # Available space for grid (left side)
        available_width = width - INFO_PANEL_WIDTH
        available_height = height - 50 # Top margin
        
        # Calculate max possible cell size
        size_x = available_width // GRID_SIZE
        size_y = available_height // GRID_SIZE
        self.cell_size = min(size_x, size_y)
        
        # Ensure minimum size
        self.cell_size = max(20, self.cell_size)
        
        # Center the grid
        grid_width = self.cell_size * GRID_SIZE
        grid_height = self.cell_size * GRID_SIZE
        
        self.grid_offset_x = (available_width - grid_width) // 2
        self.grid_offset_y = (available_height - grid_height) // 2 + 25 # Add top margin offset
    
    def draw_slider(self, x, y, width, value, min_val, max_val, label, color):
        """Draw a horizontal slider with label and value"""
        # Label
        label_text = self.small_font.render(label, True, BLACK)
        self.screen.blit(label_text, (x, y))
        
        # Value
        if isinstance(value, int):
            value_text = self.small_font.render(f"{value}", True, color)
        else:
            value_text = self.small_font.render(f"{value:.2f}", True, color)
        value_rect = value_text.get_rect(right=x + width)
        self.screen.blit(value_text, (value_rect.x, y))
        
        slider_y = y + 18
        slider_height = 16
        
        # Track
        pygame.draw.rect(self.screen, DARK_GRAY, (x, slider_y, width, slider_height), border_radius=8)
        pygame.draw.rect(self.screen, WHITE, (x + 2, slider_y + 2, width - 4, slider_height - 4), border_radius=6)
        
        # Fill
        percent = (value - min_val) / (max_val - min_val)
        fill_width = int(percent * (width - 4))
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (x + 2, slider_y + 2, fill_width, slider_height - 4), border_radius=6)
        
        # Handle
        handle_x = x + int(percent * width)
        pygame.draw.circle(self.screen, color, (handle_x, slider_y + slider_height // 2), 10)
        pygame.draw.circle(self.screen, WHITE, (handle_x, slider_y + slider_height // 2), 6)
        
        return pygame.Rect(x, slider_y, width, slider_height)
    
    def draw_cell(self, x, y):
        """Draw a single cell"""
        screen_x = self.grid_offset_x + x * self.cell_size
        screen_y = self.grid_offset_y + y * self.cell_size
        
        cell_type = self.city.grid[x][y]
        
        # Base color
        if cell_type == CellType.ROAD:
            color = DARK_GRAY
        elif cell_type == CellType.HOUSE:
            color = RED
        elif cell_type == CellType.TREE:
            color = GREEN
        elif cell_type == CellType.DRAIN:
            color = BLUE
        elif cell_type == CellType.OBSTACLE:
            color = BLACK
        else:
            if self.show_elevation:
                elev = self.city.elevation[x][y]
                norm_elev = max(0, min(1, (elev - 0) / 200))
                if norm_elev < 0.5:
                    intensity = int(norm_elev * 2 * 100)
                    color = (60 + intensity, 40 + intensity, 20 + intensity // 2)
                else:
                    intensity = int((norm_elev - 0.5) * 2 * 155)
                    color = (160 + intensity, 140 + intensity, 100 + intensity // 2)
            elif self.show_pheromones and self.aco:
                pheromone = self.aco.pheromones[x][y]
                norm_pheromone = min(1.0, max(0.0, (pheromone - 0.1) / 10))
                # Purple/Magenta gradient to distinguish from blue water
                if norm_pheromone < 0.25:
                    # Dark purple to purple
                    ratio = norm_pheromone / 0.25
                    color = (int(100 + 55 * ratio), 0, int(100 + 55 * ratio))
                elif norm_pheromone < 0.5:
                    # Purple to magenta
                    ratio = (norm_pheromone - 0.25) / 0.25
                    color = (int(155 + 100 * ratio), 0, int(155 - 55 * ratio))
                elif norm_pheromone < 0.75:
                    # Magenta to red
                    ratio = (norm_pheromone - 0.5) / 0.25
                    color = (255, 0, int(100 * (1 - ratio)))
                else:
                    # Red to orange
                    ratio = (norm_pheromone - 0.75) / 0.25
                    color = (255, int(100 * ratio), 0)
            else:
                color = LIGHT_GRAY
        
        pygame.draw.rect(self.screen, color, (screen_x, screen_y, self.cell_size, self.cell_size))
        
        # Water overlay
        # Water overlay
        if self.show_water and self.city.water_level[x][y] > 0.1:
            level = self.city.water_level[x][y]
            
            # Calculate color based on depth (Light Blue -> Dark Blue)
            # Assume 10.0 is "deep" water
            depth_ratio = min(1.0, level / 10.0)
            
            # Light Blue (173, 216, 230) to Dark Blue (0, 0, 139)
            r = int(173 + (0 - 173) * depth_ratio)
            g = int(216 + (0 - 216) * depth_ratio)
            b = int(230 + (139 - 230) * depth_ratio)
            
            # Alpha also increases with depth
            base_alpha = int(100 + 155 * depth_ratio)
            wave_offset = int(20 * math.sin(self.pulse_animation / 10 + x + y))
            alpha_value = max(0, min(255, base_alpha + wave_offset))
            
            water_color = (r, g, b, alpha_value)
            s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            s.fill(water_color)
            self.screen.blit(s, (screen_x, screen_y))
        
        # Grid
        if self.show_grid:
            pygame.draw.rect(self.screen, GRAY, (screen_x, screen_y, self.cell_size, self.cell_size), 1)
        
        # Hover highlight
        if self.hover_cell == (x, y) and self.phase == GamePhase.SETUP:
            glow_alpha = int(100 + 50 * math.sin(self.pulse_animation / 10))
            glow_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
            glow_surface.fill((255, 215, 0, glow_alpha))
            self.screen.blit(glow_surface, (screen_x, screen_y))
            pygame.draw.rect(self.screen, YELLOW, (screen_x, screen_y, self.cell_size, self.cell_size), 3)
        
        # Icons
        if self.show_icons:
            center_x = screen_x + self.cell_size // 2
            center_y = screen_y + self.cell_size // 2
            
            if cell_type == CellType.HOUSE:
                pygame.draw.rect(self.screen, (180, 0, 40), (screen_x + 8, screen_y + 12, self.cell_size - 16, self.cell_size - 18))
                points = [(center_x, screen_y + 5), (screen_x + self.cell_size - 6, screen_y + 14), (screen_x + 6, screen_y + 14)]
                pygame.draw.polygon(self.screen, (120, 0, 20), points)
                pygame.draw.rect(self.screen, YELLOW, (center_x - 4, center_y, 8, 8))
            elif cell_type == CellType.TREE:
                pygame.draw.circle(self.screen, (0, 100, 0), (center_x, center_y - 4), 8)
                pygame.draw.circle(self.screen, (0, 80, 0), (center_x - 5, center_y - 2), 6)
                pygame.draw.circle(self.screen, (0, 80, 0), (center_x + 5, center_y - 2), 6)
                pygame.draw.rect(self.screen, BROWN, (center_x - 3, center_y + 4, 6, 8))
            elif cell_type == CellType.DRAIN:
                drain_size = 10 + int(3 * math.sin(self.pulse_animation / 10))
                pygame.draw.circle(self.screen, DARK_BLUE, (center_x, center_y), drain_size)
                pygame.draw.circle(self.screen, CYAN, (center_x, center_y), drain_size - 4)
                pygame.draw.circle(self.screen, DARK_BLUE, (center_x, center_y), 4)
    
    def draw_city(self):
        """Draw the entire city grid"""
        for i in range(self.city.size):
            for j in range(self.city.size):
                self.draw_cell(i, j)
    
    def draw_paths(self):
        """Draw ant paths"""
        if self.aco and len(self.aco.best_paths) > 0:
            # Create surface for paths matching the grid size
            grid_width = GRID_SIZE * self.cell_size
            grid_height = GRID_SIZE * self.cell_size
            path_surface = pygame.Surface((grid_width, grid_height), pygame.SRCALPHA)
            
            num_paths = min(30, len(self.aco.best_paths))
            paths_to_draw = self.aco.best_paths[-num_paths:]
            
            for path_idx, path in enumerate(paths_to_draw):
                alpha = int(100 + (path_idx / num_paths) * 155)
                hue = (path_idx * 30) % 360
                if hue < 120:
                    color = (255, 255, 0, alpha)
                elif hue < 240:
                    color = (255, 200, 0, alpha)
                else:
                    color = (200, 255, 0, alpha)
                
                for i in range(len(path) - 1):
                    x1, y1 = path[i]
                    x2, y2 = path[i + 1]
                    start_pos = (x1 * self.cell_size + self.cell_size // 2, y1 * self.cell_size + self.cell_size // 2)
                    end_pos = (x2 * self.cell_size + self.cell_size // 2, y2 * self.cell_size + self.cell_size // 2)
                    pygame.draw.line(path_surface, color, start_pos, end_pos, max(1, int(self.cell_size / 10)))
            
            self.screen.blit(path_surface, (self.grid_offset_x, self.grid_offset_y))
    

    
    def draw_info_panel(self):
        """Draw comprehensive info panel"""
        # Panel is always on the right side
        window_width = self.screen.get_width()
        panel_x = window_width - INFO_PANEL_WIDTH + 10
        panel_y = 10
        panel_width = INFO_PANEL_WIDTH - 20
        
        # Header
        header_height = 40
        pygame.draw.rect(self.screen, BLUE, (panel_x, panel_y, panel_width, header_height), border_radius=8)
        title = self.font.render("Ant Colony Optimization [Flood Control]", True, WHITE)
        self.screen.blit(title, (panel_x + 10, panel_y + 5))
        subtitle = self.tiny_font.render("Group 2", True, LIGHT_GRAY)
        self.screen.blit(subtitle, (panel_x + 10, panel_y + 24))
        
        panel_y += header_height + 8
        
        # Phase indicator
        phase_color, phase_text = get_phase_color(self.phase)
        pygame.draw.rect(self.screen, phase_color, (panel_x, panel_y, panel_width, 35), border_radius=6)
        phase_surface = self.font.render(phase_text, True, WHITE)
        self.screen.blit(phase_surface, (panel_x + 10, panel_y + 8))
        
        panel_y += 40
        
        # Phase-specific info
        if self.phase == GamePhase.SETUP:
            self.draw_setup_info(panel_x, panel_y, panel_width)
        elif self.phase == GamePhase.OPTIMIZING:
            self.draw_optimizing_info(panel_x, panel_y, panel_width)
        elif self.phase == GamePhase.DEFENDING:
            self.draw_defending_info(panel_x, panel_y, panel_width)
        elif self.phase in [GamePhase.VICTORY, GamePhase.GAME_OVER]:
            self.draw_endgame_info(panel_x, panel_y, panel_width)
    
    def draw_setup_info(self, x, y, width):
        """Draw setup phase info with budget and rain controls"""
        # Budget info
        drain_count = len(self.city.drains)
        budget_color = GREEN if self.budget_remaining >= DRAIN_COST else RED
        
        items = [
            ("Budget:", format_currency(self.budget_remaining), budget_color),
            ("Spent:", format_currency(self.total_budget_spent), ORANGE),
            ("Drains:", f"{drain_count}", BLUE),
        ]
        
        for label, value, color in items:
            label_text = self.small_font.render(label, True, BLACK)
            self.screen.blit(label_text, (x, y))
            value_text = self.small_font.render(value, True, color)
            value_rect = value_text.get_rect(right=x + width)
            value_rect.y = y
            self.screen.blit(value_text, value_rect)
            y += 20
        
        y += 10
        
        # Configuration section
        header = self.small_font.render("CONFIGURATION:", True, PURPLE)
        self.screen.blit(header, (x, y))
        y += 25
        
        # Budget slider
        self.budget_slider_rect = self.draw_slider(x, y, width, self.starting_budget, BUDGET_MIN, BUDGET_MAX, "Budget:", BLUE)
        y += 40
        
        # Rain slider
        self.rain_slider_rect = self.draw_slider(x, y, width, self.rain_intensity, RAIN_INTENSITY_MIN, RAIN_INTENSITY_MAX, "Rain:", CYAN)
        y += 45
        
        # ACO Parameters section
        header = self.small_font.render("ACO PARAMETERS:", True, PURPLE)
        self.screen.blit(header, (x, y))
        y += 25
        
        # Sliders
        self.ants_slider_rect = self.draw_slider(x, y, width, self.num_ants, NUM_ANTS_MIN, NUM_ANTS_MAX, "Ants:", BLUE)
        y += 40
        
        self.alpha_slider_rect = self.draw_slider(x, y, width, self.alpha, ALPHA_MIN, ALPHA_MAX, "Alpha (pheromone):", ORANGE)
        y += 40
        
        self.beta_slider_rect = self.draw_slider(x, y, width, self.beta, BETA_MIN, BETA_MAX, "Beta (distance):", GREEN)
        y += 40
        
        self.evap_slider_rect = self.draw_slider(x, y, width, self.evaporation_rate, EVAPORATION_RATE_MIN, EVAPORATION_RATE_MAX, "Evaporation:", RED)
        y += 45
        
        # Legend and controls occupy freed space
        legend_y = self.draw_legend(x, y, width)
        y = legend_y + 5
        self.draw_controls(x, y, width)
        
        # Instructions at bottom
        y_bottom = self.screen.get_height() - 30
        if self.blink_timer % 60 < 30:
            inst = self.small_font.render("Press ENTER to optimize", True, PURPLE)
            inst_rect = inst.get_rect(center=(x + width // 2, y_bottom))
            self.screen.blit(inst, inst_rect)
    
    def draw_optimizing_info(self, x, y, width):
        """Draw optimization info"""
        if not self.aco:
            return
        
        success_rate = int((self.aco.paths_this_iteration / max(1, self.aco.num_ants)) * 100)
        pipe_used = self.aco.total_pipe_length
        current_cost = self.aco.get_current_pipe_cost()
        pipe_budget = self.starting_budget - self.total_budget_spent
        budget_percent = int((current_cost / max(1, pipe_budget)) * 100)
        
        items = [
            ("Iteration:", f"{self.aco.iteration}", ORANGE),
            ("Paths Found:", f"{len(self.aco.best_paths)}", BLUE),
            ("Efficiency:", f"{self.aco.iteration_efficiency:.2f}", CYAN),
            ("Last Improved:", f"Iter {self.aco.last_improvement_iteration}", GREEN),
            ("Stagnation:", f"{self.aco.stagnation_counter}/{CONVERGENCE_THRESHOLD}", RED if self.aco.stagnation_counter > 10 else BLACK),
            ("", "", BLACK),
            ("Pipe Cells:", f"{pipe_used}/{MAX_TOTAL_PIPE_LENGTH}", BLUE),
            ("Pipe Cost:", format_currency(current_cost), PURPLE),
            ("Budget Used:", f"{budget_percent}%", GREEN if budget_percent < 80 else RED),
            ("", "", BLACK),
            ("ACO Parameters:", "", BLACK),
            (f"  Ants: {self.aco.num_ants}", "", DARK_GRAY),
            (f"  Alpha: {self.aco.alpha:.2f}", "", DARK_GRAY),
            (f"  Beta: {self.aco.beta:.2f}", "", DARK_GRAY),
            (f"  Evap: {self.aco.evaporation_rate:.2f}", "", DARK_GRAY),
        ]
        
        for label, value, color in items:
            if label == "":
                y += 8
                continue
            if value == "":
                text = self.tiny_font.render(label, True, color)
                self.screen.blit(text, (x, y))
                y += 14
            else:
                label_text = self.small_font.render(label, True, BLACK)
                self.screen.blit(label_text, (x, y))
                value_text = self.small_font.render(value, True, color)
                value_rect = value_text.get_rect(right=x + width)
                value_rect.y = y
                self.screen.blit(value_text, value_rect)
                y += 20
        
        y += 10
        # Speed slider
        self.speed_slider_rect = self.draw_slider(x, y, width, self.animation_speed, 1, 10, "Animation Speed:", BLACK)
        y += 35
        
        y += 15
        
        # Add legend and controls in the middle space
        legend_y = self.draw_legend(x, y, width)
        y = legend_y + 5
        self.draw_controls(x, y, width)
        
        # Get the y position after controls for button placement
        y += 120  # Approximate height of controls section
        
        # Manual advance buttons at bottom if converged
        if self.aco.converged:
            button_x = x + (width - 160) // 2
            button_width = 160
            button_height = 35
            
            mouse_pos = pygame.mouse.get_pos()
            self.start_defending_rect = pygame.Rect(button_x, y, button_width, button_height)
            hover = self.start_defending_rect.collidepoint(mouse_pos)
            
            pygame.draw.rect(self.screen, GREEN if not hover else (50, 220, 120), 
                           (button_x, y, button_width, button_height), border_radius=8)
            pygame.draw.rect(self.screen, WHITE, (button_x, y, button_width, button_height), 2, border_radius=8)
            
            btn_text = self.small_font.render("Start Defending", True, WHITE)
            btn_rect = btn_text.get_rect(center=(button_x + button_width // 2, y + button_height // 2))
            self.screen.blit(btn_text, btn_rect)
            
            y += button_height + 10
            
            # Try again button
            self.retry_aco_rect = pygame.Rect(button_x, y, button_width, 30)
            hover2 = self.retry_aco_rect.collidepoint(mouse_pos)
            
            pygame.draw.rect(self.screen, ORANGE if not hover2 else (255, 150, 50), 
                           (button_x, y, button_width, 30), border_radius=6)
            
            btn_text2 = self.tiny_font.render("Try Different Parameters", True, WHITE)
            btn_rect2 = btn_text2.get_rect(center=(button_x + button_width // 2, y + 15))
            self.screen.blit(btn_text2, btn_rect2)
    
    def draw_defending_info(self, x, y, width):
        """Draw defending phase info"""
        total_water = sum(sum(row) for row in self.city.water_level)
        water_percent = min(100, int((total_water / MAX_WATER_THRESHOLD) * 100))
        survival_seconds = self.survival_time // TARGET_FPS
        
        items = [
            ("Time Survived:", f"{survival_seconds}s / {VICTORY_TIME_SECONDS}s", BLUE),
            ("Water Level:", f"{water_percent}%", RED if water_percent > 70 else GREEN),
            ("", "", BLACK),
            ("Rain Intensity:", f"{self.rain_intensity:.2f}", CYAN),
            ("Drains Active:", f"{len(self.city.drains)}", GREEN),
        ]
        
        for label, value, color in items:
            if label == "":
                y += 10
                continue
            label_text = self.small_font.render(label, True, BLACK)
            self.screen.blit(label_text, (x, y))
            value_text = self.small_font.render(value, True, color)
            value_rect = value_text.get_rect(right=x + width)
            value_rect.y = y
            self.screen.blit(value_text, value_rect)
            y += 20
        
        y += 20
        
        # Add legend and controls
        legend_y = self.draw_legend(x, y, width)
        y = legend_y + 5
        self.draw_controls(x, y, width)
        
        # Progress bar for victory
        y_bottom = self.screen.get_height() - 80
        bar_width = width - 20
        bar_height = 20
        progress = min(1.0, survival_seconds / VICTORY_TIME_SECONDS)
        
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x + 10, y_bottom, bar_width, bar_height), border_radius=10)
        if progress > 0:
            filled_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, GREEN, (x + 10, y_bottom, filled_width, bar_height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (x + 10, y_bottom, bar_width, bar_height), 2, border_radius=10)
        
        progress_text = self.tiny_font.render(f"Victory Progress: {int(progress * 100)}%", True, BLACK)
        text_rect = progress_text.get_rect(center=(x + width // 2, y_bottom + bar_height + 12))
        self.screen.blit(progress_text, text_rect)
            
    
    def draw_endgame_info(self, x, y, width):
        """Draw end game info"""
        is_victory = self.phase == GamePhase.VICTORY
        title_color = GREEN if is_victory else RED
        title_text = "VICTORY!" if is_victory else "GAME OVER"
        subtitle_text = "Perfect Drainage!" if is_victory else "Water Overflow!"
        
        msg1 = self.title_font.render(title_text, True, title_color)
        msg1_rect = msg1.get_rect(center=(x + width // 2, y + 15))
        self.screen.blit(msg1, msg1_rect)
        
        msg2 = self.small_font.render(subtitle_text, True, title_color)
        msg2_rect = msg2.get_rect(center=(x + width // 2, y + 45))
        self.screen.blit(msg2, msg2_rect)
        
        y += 70
        
        total_cost = self.total_budget_spent + self.total_pipe_cost
        remaining_budget = self.starting_budget - total_cost
        
        costs = [
            ("Drains:", format_currency(self.total_budget_spent), BLUE),
            ("Pipes:", format_currency(self.total_pipe_cost), ORANGE),
            ("Total Spent:", format_currency(total_cost), title_color),
            ("Remaining:", format_currency(remaining_budget), GREEN if remaining_budget >= 0 else RED),
        ]
        
        for label, value, color in costs:
            label_text = self.small_font.render(label, True, BLACK)
            self.screen.blit(label_text, (x + 10, y))
            value_text = self.small_font.render(value, True, color)
            value_rect = value_text.get_rect(right=x + width - 10)
            value_rect.y = y
            self.screen.blit(value_text, value_rect)
            y += 20
        
        y += 10
        msg3 = self.tiny_font.render("Y: Retry | R: New City", True, DARK_GRAY)
        msg3_rect = msg3.get_rect(center=(x + width // 2, y))
        self.screen.blit(msg3, msg3_rect)
    
    def draw_legend(self, x, y, width):
        """Draw legend"""
        legend_title = self.small_font.render("LEGEND", True, BLACK)
        self.screen.blit(legend_title, (x, y))
        y += 18
        
        items = [
            (RED, "House"),
            (DARK_GRAY, "Road"),
            (GREEN, "Tree"),
            (BLUE, "Drain"),
            (YELLOW, "Pipe Route"),
            (ORANGE, "High Pheromone"),
            (PURPLE, "Low Pheromone"),
        ]
        
        for color, label in items:
            pygame.draw.circle(self.screen, color, (x + 6, y + 6), 5)
            pygame.draw.circle(self.screen, BLACK, (x + 6, y + 6), 5, 1)
            text = self.tiny_font.render(label, True, BLACK)
            self.screen.blit(text, (x + 18, y + 2))
            y += 14
        
        return y
    
    def draw_controls(self, x, y, width):
        """Draw controls"""
        y += 10
        controls_title = self.small_font.render("VIEW CONTROLS", True, BLACK)
        self.screen.blit(controls_title, (x, y))
        y += 18
        
        view_options = [
            ("E", "Elevation", self.show_elevation),
            ("P", "Pheromones", self.show_pheromones),
            ("W", "Water", self.show_water),
            ("G", "Grid", self.show_grid),
            ("I", "Icons", self.show_icons),
        ]
        
        for key, name, enabled in view_options:
            button_color = GREEN if enabled else LIGHT_GRAY
            pygame.draw.rect(self.screen, button_color, (x, y, 20, 16), border_radius=3)
            pygame.draw.rect(self.screen, BLACK, (x, y, 20, 16), 1, border_radius=3)
            
            key_text = self.tiny_font.render(key, True, BLACK)
            key_rect = key_text.get_rect(center=(x + 10, y + 8))
            self.screen.blit(key_text, key_rect)
            
            label_text = self.tiny_font.render(name, True, BLACK if enabled else DARK_GRAY)
            self.screen.blit(label_text, (x + 25, y + 2))
            y += 17
        
        y += 10
        other_keys = [
            ("T", "Tutorial"),
            ("Y", "Retry"),
            ("R", "New City"),
        ]
        
        for key, action in other_keys:
            text = self.tiny_font.render(f"{key}: {action}", True, DARK_GRAY)
            self.screen.blit(text, (x, y))
            y += 14
    
    def draw_ants(self):
        """Draw ants during optimization phase"""
        if not self.aco or not hasattr(self.aco, 'ants'):
            return
            
        for ant in self.aco.ants:
            # Draw ant as a small circle
            # Screen coordinates
            x = self.grid_offset_x + ant.pos[0] * self.cell_size + self.cell_size // 2
            y = self.grid_offset_y + ant.pos[1] * self.cell_size + self.cell_size // 2
            
            # Draw ant body
            pygame.draw.circle(self.screen, (50, 50, 50), (x, y), 3)
            
    def draw_tutorial(self):
        """Draw tutorial overlay"""
        if not self.show_tutorial:
            return
        
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        box_width = 700
        box_height = 500
        box_x = (self.screen.get_width() - box_width) // 2
        box_y = (self.screen.get_height() - box_height) // 2
        
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_width, box_height), border_radius=12)
        pygame.draw.rect(self.screen, BLUE, (box_x, box_y, box_width, box_height), 4, border_radius=12)
        
        y = box_y + 20
        
        title = self.title_font.render("FLOOD CONTROL GAME", True, BLUE)
        title_rect = title.get_rect(center=(box_x + box_width // 2, y))
        self.screen.blit(title, title_rect)
        
        y += 40
        subtitle = self.small_font.render("Ant Colony Optimization", True, DARK_GRAY)
        subtitle_rect = subtitle.get_rect(center=(box_x + box_width // 2, y))
        self.screen.blit(subtitle, subtitle_rect)
        
        y += 40
        
        sections = [
            ("OBJECTIVE:", [
                "Design a drainage system to prevent flooding",
                "Use budget wisely: Drains + Pipes must stay in budget",
            ]),
            ("PHASE 1 - SETUP:", [
                "Click to place drains (200M each)",
                "Configure ACO parameters (ants, alpha, beta, evaporation)",
                "Press ENTER to start optimization",
            ]),
            ("PHASE 2 - OPTIMIZE:", [
                "Watch ants find paths to drains using pheromones",
                "Adjust parameters and retry if needed",
                "Click 'Start Defending' when satisfied",
            ]),
            ("PHASE 3 - DEFEND:", [
                "Rain starts automatically",
                "Keep water level below 100% for 20 seconds",
                "Win if drainage system works!",
            ]),
        ]
        
        for section_title, lines in sections:
            title_text = self.small_font.render(section_title, True, PURPLE)
            self.screen.blit(title_text, (box_x + 40, y))
            y += 20
            
            for line in lines:
                line_text = self.tiny_font.render(f"  - {line}", True, BLACK)
                self.screen.blit(line_text, (box_x + 40, y))
                y += 16
            y += 8
        
        y += 10
        close_text = self.small_font.render("Press T to close", True, DARK_GRAY)
        close_rect = close_text.get_rect(center=(box_x + box_width // 2, y))
        self.screen.blit(close_text, close_rect)
    
    def handle_click(self, pos, button):
        """Handle mouse clicks"""
        if self.phase == GamePhase.SETUP:
            # Check sliders
            if hasattr(self, 'budget_slider_rect') and self.budget_slider_rect.collidepoint(pos):
                self.dragging_budget = True
                return
            if hasattr(self, 'rain_slider_rect') and self.rain_slider_rect.collidepoint(pos):
                self.dragging_rain = True
                return
            if hasattr(self, 'ants_slider_rect') and self.ants_slider_rect.collidepoint(pos):
                self.dragging_ants = True
                return
            if hasattr(self, 'alpha_slider_rect') and self.alpha_slider_rect.collidepoint(pos):
                self.dragging_alpha = True
                return
            if hasattr(self, 'beta_slider_rect') and self.beta_slider_rect.collidepoint(pos):
                self.dragging_beta = True
                return
            if hasattr(self, 'evap_slider_rect') and self.evap_slider_rect.collidepoint(pos):
                self.dragging_evap = True
                return
            
            # Place/remove drains
            x, y = pos
            # Adjust for grid offset
            adj_x = x - self.grid_offset_x
            adj_y = y - self.grid_offset_y
            
            if adj_x >= 0 and adj_y >= 0:
                grid_x = adj_x // self.cell_size
                grid_y = adj_y // self.cell_size
            else:
                grid_x, grid_y = -1, -1
            
            if 0 <= grid_x < self.city.size and 0 <= grid_y < self.city.size:
                if button == 1:
                    if self.city.grid[grid_x][grid_y] in [CellType.EMPTY, CellType.ROAD]:
                        if self.budget_remaining >= DRAIN_COST:
                            self.city.grid[grid_x][grid_y] = CellType.DRAIN
                            self.city.drains.append((grid_x, grid_y))
                            self.budget_remaining -= DRAIN_COST
                            self.total_budget_spent += DRAIN_COST
                elif button == 3:
                    if self.city.grid[grid_x][grid_y] == CellType.DRAIN:
                        self.city.grid[grid_x][grid_y] = CellType.EMPTY
                        if (grid_x, grid_y) in self.city.drains:
                            self.city.drains.remove((grid_x, grid_y))
                        self.budget_remaining += DRAIN_COST
                        self.total_budget_spent -= DRAIN_COST
        
        elif self.phase == GamePhase.OPTIMIZING:
            if hasattr(self, 'speed_slider_rect') and self.speed_slider_rect.collidepoint(pos):
                self.dragging_speed = True
                return

            if hasattr(self, 'start_defending_rect') and self.start_defending_rect.collidepoint(pos):
                # Manually advance to defending
                self.phase = GamePhase.DEFENDING
                self.show_water = True
                self.show_pheromones = False
                self.total_pipe_cost = self.aco.get_current_pipe_cost()
            elif hasattr(self, 'retry_aco_rect') and self.retry_aco_rect.collidepoint(pos):
                # Retry optimization with new parameters
                self.phase = GamePhase.SETUP
                self.show_pheromones = False
                self.aco = None
    
    def update_slider(self, pos, rect, min_val, max_val):
        """Update slider value based on mouse position"""
        slider_x = rect.x
        slider_width = rect.width
        mouse_x = pos[0]
        percent = max(0, min(1, (mouse_x - slider_x) / slider_width))
        return min_val + percent * (max_val - min_val)
    
    def run(self):
        """Main game loop"""
        while self.running:
            self.blink_timer += 1
            self.pulse_animation += 1
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Calculate grid hover
            adj_x = mouse_pos[0] - self.grid_offset_x
            adj_y = mouse_pos[1] - self.grid_offset_y
            
            if adj_x >= 0 and adj_y >= 0:
                grid_x = adj_x // self.cell_size
                grid_y = adj_y // self.cell_size
                if 0 <= grid_x < self.city.size and 0 <= grid_y < self.city.size:
                    self.hover_cell = (grid_x, grid_y)
                else:
                    self.hover_cell = None
            else:
                self.hover_cell = None
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.recalculate_layout(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        # Toggle fullscreen
                        if self.screen.get_flags() & pygame.FULLSCREEN:
                            pygame.display.set_mode((DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT), pygame.RESIZABLE)
                            self.recalculate_layout(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
                        else:
                            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            info = pygame.display.Info()
                            self.recalculate_layout(info.current_w, info.current_h)
                    elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                        if self.phase == GamePhase.SETUP:
                            pipe_budget = self.starting_budget - self.total_budget_spent
                            self.aco = ACO(self.city, self.num_ants, self.evaporation_rate, 
                                         DEFAULT_PHEROMONE_STRENGTH, self.alpha, self.beta, pipe_budget)
                            self.phase = GamePhase.OPTIMIZING
                            self.show_water = False
                            self.show_pheromones = True
                    elif event.key == pygame.K_t:
                        self.show_tutorial = not self.show_tutorial
                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    elif event.key == pygame.K_i:
                        self.show_icons = not self.show_icons
                    elif event.key == pygame.K_w:
                        self.show_water = not self.show_water
                    elif event.key == pygame.K_r:
                        self.city = City(GRID_SIZE, self.starting_budget)
                        self.aco = None
                        self.phase = GamePhase.SETUP
                        self.survival_time = 0
                        self.budget_remaining = self.starting_budget
                        self.total_budget_spent = 0
                        self.total_pipe_cost = 0
                        self.water_history = []
                        self.show_tutorial = False
                        self.show_water = True
                        self.show_pheromones = False
                        self.show_elevation = False
                    elif event.key == pygame.K_y:
                        for i in range(self.city.size):
                            for j in range(self.city.size):
                                self.city.water_level[i][j] = 0.0
                                if self.city.grid[i][j] == CellType.DRAIN:
                                    self.city.grid[i][j] = CellType.EMPTY
                        self.city.drains = []
                        self.aco = None
                        self.phase = GamePhase.SETUP
                        self.survival_time = 0
                        self.budget_remaining = self.starting_budget
                        self.total_budget_spent = 0
                        self.total_pipe_cost = 0
                        self.water_history = []
                        self.show_tutorial = False
                        self.show_water = True
                        self.show_pheromones = False
                        self.show_elevation = False
                    elif event.key == pygame.K_e:
                        self.show_elevation = not self.show_elevation
                        if self.show_elevation:
                            self.show_pheromones = False
                            self.show_water = False
                    elif event.key == pygame.K_p:
                        self.show_pheromones = not self.show_pheromones
                        if self.show_pheromones:
                            self.show_elevation = False
                            self.show_water = False
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.dragging_budget = False
                    self.dragging_rain = False
                    self.dragging_ants = False
                    self.dragging_alpha = False
                    self.dragging_beta = False
                    self.dragging_evap = False
                    self.dragging_speed = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging_budget and hasattr(self, 'budget_slider_rect'):
                        new_budget = int(self.update_slider(event.pos, self.budget_slider_rect, BUDGET_MIN, BUDGET_MAX))
                        budget_diff = new_budget - self.starting_budget
                        self.starting_budget = new_budget
                        self.budget_remaining += budget_diff
                        # Reset city with new budget
                        self.city.budget = new_budget
                    elif self.dragging_rain and hasattr(self, 'rain_slider_rect'):
                        self.rain_intensity = self.update_slider(event.pos, self.rain_slider_rect, RAIN_INTENSITY_MIN, RAIN_INTENSITY_MAX)
                    elif self.dragging_ants and hasattr(self, 'ants_slider_rect'):
                        self.num_ants = int(self.update_slider(event.pos, self.ants_slider_rect, NUM_ANTS_MIN, NUM_ANTS_MAX))
                    elif self.dragging_alpha and hasattr(self, 'alpha_slider_rect'):
                        self.alpha = self.update_slider(event.pos, self.alpha_slider_rect, ALPHA_MIN, ALPHA_MAX)
                    elif self.dragging_beta and hasattr(self, 'beta_slider_rect'):
                        self.beta = self.update_slider(event.pos, self.beta_slider_rect, BETA_MIN, BETA_MAX)
                    elif self.dragging_evap and hasattr(self, 'evap_slider_rect'):
                        self.evaporation_rate = self.update_slider(event.pos, self.evap_slider_rect, EVAPORATION_RATE_MIN, EVAPORATION_RATE_MAX)
                    elif self.dragging_speed and hasattr(self, 'speed_slider_rect'):
                        self.animation_speed = int(self.update_slider(event.pos, self.speed_slider_rect, 1, 10))
            
            # Game logic
            if self.phase == GamePhase.OPTIMIZING:
                if self.aco and not self.aco.converged:
                    # Step-by-step animation
                    steps_per_frame = self.animation_speed
                    for _ in range(steps_per_frame):
                        if not hasattr(self.aco, 'active_ants') or not self.aco.active_ants:
                            # Start new iteration
                            self.aco.start_iteration()
                        else:
                            # Move ants one step
                            finished = self.aco.step()
                            if finished:
                                self.aco.finish_iteration()
                                if self.aco.converged:
                                    break
                # DON'T auto-advance - wait for user button click
            
            elif self.phase == GamePhase.DEFENDING:
                self.city.simulate_rain(self.rain_intensity)
                self.city.drain_water(pipe_cells=self.aco.pipe_cells if self.aco else None)
                self.survival_time += 1
                
                total_water = sum(sum(row) for row in self.city.water_level)
                self.water_history.append(total_water)
                if len(self.water_history) > STABILIZATION_THRESHOLD:
                    self.water_history.pop(0)
                
                water_stabilized = False
                if len(self.water_history) >= STABILIZATION_THRESHOLD:
                    avg_water = sum(self.water_history) / len(self.water_history)
                    variance = sum((w - avg_water) ** 2 for w in self.water_history) / len(self.water_history)
                    water_stabilized = variance < 1000
                
                if total_water > MAX_WATER_THRESHOLD:
                    self.phase = GamePhase.GAME_OVER
                elif self.survival_time > VICTORY_TIME_FRAMES and water_stabilized:
                    self.phase = GamePhase.VICTORY
            
            # Draw
            self.screen.fill(WHITE)
            self.draw_city()
            
            if self.phase in [GamePhase.OPTIMIZING, GamePhase.DEFENDING, GamePhase.VICTORY, GamePhase.GAME_OVER]:
                self.draw_paths()
                
            if self.phase == GamePhase.OPTIMIZING and self.aco:
                self.draw_ants()
            
            self.draw_info_panel()
            
            if self.show_tutorial:
                self.draw_tutorial()
            
            pygame.display.flip()
            self.clock.tick(TARGET_FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
