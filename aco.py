"""
Ant Colony Optimization module for Flood Control Simulation
Contains City, Ant, and ACO classes with budget constraints
"""

import random
import math
import time
from config import *


class City:
    """Represents the city grid with terrain, water, and drainage"""
    
    def __init__(self, size, starting_budget=DEFAULT_BUDGET):
        self.size = size
        self.grid = [[CellType.EMPTY for _ in range(size)] for _ in range(size)]
        self.elevation = [[0 for _ in range(size)] for _ in range(size)]
        self.water_level = [[0.0 for _ in range(size)] for _ in range(size)]
        self.drains = []
        self.budget = starting_budget
        self.drain_count = 0
        self.generate_city()
    
    def generate_city(self):
        """Generate city terrain with elevation, roads, houses, and trees"""
        # Generate elevation map (higher values = higher elevation)
        for i in range(self.size):
            for j in range(self.size):
                # Create varied terrain with some randomness
                self.elevation[i][j] = random.randint(0, 100) + \
                    30 * math.sin(i / 10) + 30 * math.cos(j / 10)
        
        # Generate main roads (grid pattern)
        for i in range(0, self.size, 6):
            for j in range(self.size):
                if random.random() < 0.8:
                    self.grid[i][j] = CellType.ROAD
        
        for j in range(0, self.size, 6):
            for i in range(self.size):
                if random.random() < 0.8:
                    self.grid[i][j] = CellType.ROAD
        
        # Generate houses in clusters
        num_houses = random.randint(30, 50)
        for _ in range(num_houses):
            x = random.randint(1, self.size - 2)
            y = random.randint(1, self.size - 2)
            if self.grid[x][y] == CellType.EMPTY:
                self.grid[x][y] = CellType.HOUSE
        
        # Generate trees in clusters
        num_trees = random.randint(20, 40)
        for _ in range(num_trees):
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if self.grid[x][y] == CellType.EMPTY:
                self.grid[x][y] = CellType.TREE
    
    def simulate_rain(self, intensity=0.5):
        """Add water to the city (simulating rainfall)"""
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] != CellType.OBSTACLE:
                    self.water_level[i][j] += intensity * random.uniform(0.8, 1.2)
    
    def drain_water(self, pipe_cells=None):
        """Simulate water flowing to drains (only through pipe paths)"""
        new_water = [[0.0 for _ in range(self.size)] for _ in range(self.size)]
        
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == CellType.DRAIN:
                    # Drains remove water efficiently
                    new_water[i][j] = max(0, self.water_level[i][j] - 2.0)
                elif self.grid[i][j] == CellType.OBSTACLE:
                    # Obstacles don't hold water
                    new_water[i][j] = 0
                else:
                    # Water only flows if there's a pipe path or to a drain
                    current_water = self.water_level[i][j]
                    if current_water > 0.1:
                        # Check if this cell has a pipe or is adjacent to pipe/drain
                        has_drainage = False
                        if pipe_cells and (i, j) in pipe_cells:
                            has_drainage = True
                        elif self.grid[i][j] == CellType.DRAIN:
                            has_drainage = True
                        else:
                            # Check if adjacent to pipe or drain
                            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                ni, nj = i + di, j + dj
                                if 0 <= ni < self.size and 0 <= nj < self.size:
                                    if self.grid[ni][nj] == CellType.DRAIN:
                                        has_drainage = True
                                        break
                                    if pipe_cells and (ni, nj) in pipe_cells:
                                        has_drainage = True
                                        break
                        
                        if has_drainage:
                            # Water can flow to drainage system
                            neighbors = []
                            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                ni, nj = i + di, j + dj
                                if 0 <= ni < self.size and 0 <= nj < self.size:
                                    # Can flow to drains, pipes, or lower elevation with pipes
                                    if self.grid[ni][nj] == CellType.DRAIN:
                                        neighbors.append((ni, nj))
                                    elif pipe_cells and (ni, nj) in pipe_cells and \
                                            self.elevation[ni][nj] <= self.elevation[i][j]:
                                        neighbors.append((ni, nj))
                            
                            if neighbors:
                                # Distribute water to drainage neighbors
                                flow = current_water * 0.4  # Faster drainage with pipes
                                flow_per_neighbor = flow / len(neighbors)
                                new_water[i][j] = current_water - flow
                                for ni, nj in neighbors:
                                    new_water[ni][nj] += flow_per_neighbor
                            else:
                                new_water[i][j] = current_water * 0.98  # Very slow evaporation
                        else:
                            # No drainage path - water accumulates!
                            new_water[i][j] = current_water * 0.99
                    else:
                        new_water[i][j] = current_water * 0.95  # Slow evaporation
        
        self.water_level = new_water


class Ant:
    """Individual ant that searches for paths to drains"""
    
    def __init__(self, start_pos, city):
        self.pos = start_pos
        self.path = [start_pos]
        self.city = city
        self.visited = set()
        self.visited.add(start_pos)
    
    def move(self, pheromones, alpha=ACO_ALPHA, beta=ACO_BETA):
        """
        Move to next cell based on pheromones and elevation heuristic
        
        Args:
            pheromones: 2D array of pheromone levels
            alpha: Pheromone importance factor
            beta: Heuristic importance factor
            
        Returns:
            True if reached drain, False if stuck, None if continuing
        """
        x, y = self.pos
        candidates = []
        
        # Check all 8 neighbors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if 0 <= nx < self.city.size and 0 <= ny < self.city.size:
                    # Skip if already visited or is an obstacle
                    if (nx, ny) not in self.visited and \
                            self.city.grid[nx][ny] != CellType.OBSTACLE:
                        candidates.append((nx, ny))
        
        if not candidates:
            return False  # Stuck
        
        # Calculate probabilities based on pheromones and heuristic
        probabilities = []
        for nx, ny in candidates:
            # Pheromone level
            pheromone = pheromones[nx][ny] ** alpha
            
            # Heuristic: prefer downward slope (lower elevation)
            elevation_diff = self.city.elevation[x][y] - self.city.elevation[nx][ny]
            heuristic = (max(0, elevation_diff) + 1) ** beta
            
            # Bonus for drains
            if self.city.grid[nx][ny] == CellType.DRAIN:
                heuristic *= 5
            
            # Bonus for houses (protecting them is priority)
            elif self.city.grid[nx][ny] == CellType.HOUSE:
                heuristic *= 4  # High priority for actual house cells
            
            # Bonus for cells adjacent to houses (catch water before it hits house)
            else:
                is_near_house = False
                for hx in [-1, 0, 1]:
                    for hy in [-1, 0, 1]:
                        hnx, hny = nx + hx, ny + hy
                        if 0 <= hnx < self.city.size and 0 <= hny < self.city.size:
                            if self.city.grid[hnx][hny] == CellType.HOUSE:
                                is_near_house = True
                                break
                    if is_near_house:
                        break
                
                if is_near_house:
                    heuristic *= 2  # Moderate priority for area around houses
            
            probabilities.append(pheromone * heuristic)
        
        # Normalize probabilities
        total = sum(probabilities)
        if total == 0:
            # Random choice if all probabilities are 0
            next_pos = random.choice(candidates)
        else:
            probabilities = [p / total for p in probabilities]
            next_pos = random.choices(candidates, weights=probabilities)[0]
        
        self.pos = next_pos
        self.path.append(next_pos)
        self.visited.add(next_pos)
        
        # Check if reached drain
        if self.city.grid[next_pos[0]][next_pos[1]] == CellType.DRAIN:
            return True  # Success
        
        return None  # Continue


class ACO:
    """
    Ant Colony Optimization algorithm for finding optimal drainage paths
    NOW WITH PROPER BUDGET CONSTRAINTS!
    """
    
    def __init__(self, city, num_ants=DEFAULT_NUM_ANTS, 
                 evaporation_rate=DEFAULT_EVAPORATION_RATE,
                 pheromone_strength=DEFAULT_PHEROMONE_STRENGTH,
                 alpha=ACO_ALPHA,
                 beta=ACO_BETA,
                 available_budget=0):
        self.city = city
        self.num_ants = num_ants
        self.evaporation_rate = evaporation_rate
        self.pheromone_strength = pheromone_strength
        self.alpha = alpha  # Pheromone importance
        self.beta = beta    # Heuristic (distance) importance
        self.pheromones = [[1.0 for _ in range(city.size)] for _ in range(city.size)]
        self.best_paths = []
        self.iteration = 0
        self.converged = False
        self.convergence_threshold = CONVERGENCE_THRESHOLD
        self.stable_iterations = 0
        self.paths_this_iteration = 0
        self.total_pipe_length = 0
        self.available_budget = available_budget
        self.budget_exceeded = False
        self.exceeded_reason = None  # "BUDGET" or "LENGTH"
        self.pipe_cells = set()
        self.total_aco_cost = 0.0
        
        # Stagnation detection
        # Stagnation detection
        self.global_best_efficiency = float('inf')
        self.stagnation_counter = 0
        self.iteration_efficiency = float('inf')
        self.last_improvement_iteration = 0
    
    def get_current_pipe_cost(self):
        """Calculate current total pipe cost"""
        return self.total_pipe_length * PIPE_COST_PER_CELL
    
    def start_iteration(self):
        """Initialize a new iteration"""
        self.iteration += 1
        self.ants = []
        self.paths_this_iteration = 0
        self.active_ants = True
        self.steps_taken = 0
        self.iteration_efficiency = float('inf')
        
        # Create ants at random positions
        for _ in range(self.num_ants):
            x = random.randint(0, self.city.size - 1)
            y = random.randint(0, self.city.size - 1)
            # Don't start on obstacles or drains
            while self.city.grid[x][y] == CellType.OBSTACLE or \
                    self.city.grid[x][y] == CellType.DRAIN:
                x = random.randint(0, self.city.size - 1)
                y = random.randint(0, self.city.size - 1)
            self.ants.append(Ant((x, y), self.city))
            
    def step(self):
        """
        Move all ants one step
        Returns: True if iteration finished (all ants done or max steps), False otherwise
        """
        if not self.active_ants:
            return True
            
        self.steps_taken += 1
        any_active = False
        
        for ant in self.ants:
            if len(ant.path) > 0:  # Ant is still active
                # If ant has already reached a drain or is stuck, skip it
                # We need a way to know if ant is finished. 
                # Let's check if the last move was a terminal state
                if hasattr(ant, 'finished') and ant.finished:
                    continue
                    
                result = ant.move(self.pheromones, self.alpha, self.beta)
                
                if result is not None:  # Ant finished (success or stuck)
                    ant.finished = True
                    if result:  # Success - reached drain
                        # Calculate total cost if we add this path
                        temp_paths = self.best_paths + [ant.path[:]]
                        unique_cells = set()
                        for path in temp_paths:
                            for cell in path:
                                unique_cells.add(cell)
                        
                        total_pipe_length = len(unique_cells)
                        total_pipe_cost = total_pipe_length * PIPE_COST_PER_CELL
                        
                        # Check BOTH length AND budget constraints
                        length_ok = total_pipe_length <= MAX_TOTAL_PIPE_LENGTH
                        budget_ok = total_pipe_cost <= self.available_budget
                        
                        if length_ok and budget_ok:
                            # Both constraints satisfied - add the path
                            self.best_paths.append(ant.path[:])
                            self.paths_this_iteration += 1
                            
                            # Track best length for this iteration - REMOVED (using efficiency now)
                            # if total_pipe_length < self.iteration_best_length:
                            #     self.iteration_best_length = total_pipe_length
                        else:
                            # Constraint violated - set exceeded flag
                            self.budget_exceeded = True
                            if not budget_ok:
                                self.exceeded_reason = "BUDGET"
                            else:
                                self.exceeded_reason = "LENGTH"
                else:
                    any_active = True
        
        if not any_active or self.steps_taken >= ACO_MAX_STEPS:
            self.active_ants = False
            return True
            
        return False

    def finish_iteration(self):
        """Complete the iteration: evaporation, pheromone deposit, convergence"""
        # Calculate total unique pipe cells used
        unique_pipe_cells = set()
        for path in self.best_paths:
            for cell in path:
                unique_pipe_cells.add(cell)
        self.total_pipe_length = len(unique_pipe_cells)
        self.pipe_cells = unique_pipe_cells
        
        # Evaporate pheromones
        for i in range(self.city.size):
            for j in range(self.city.size):
                self.pheromones[i][j] *= (1 - self.evaporation_rate)
                self.pheromones[i][j] = max(0.1, self.pheromones[i][j])
        
        # Deposit pheromones
        for ant in self.ants:
            if len(ant.path) > 1:
                # Check if ant reached a drain
                last_pos = ant.path[-1]
                if self.city.grid[last_pos[0]][last_pos[1]] == CellType.DRAIN:
                    # Reward inversely proportional to path length
                    deposit = self.pheromone_strength * (50 / len(ant.path))
                    for x, y in ant.path:
                        self.pheromones[x][y] += deposit
        
        # Check for convergence (Stagnation)
        if self.budget_exceeded:
             self.converged = True
        else:
            # Calculate efficiency (Average pipe length per path)
            # We need to calculate pipe length ONLY for paths found THIS iteration
            current_iter_paths = self.best_paths[-self.paths_this_iteration:] if self.paths_this_iteration > 0 else []
            
            current_iter_pipe_cells = set()
            for path in current_iter_paths:
                for cell in path:
                    current_iter_pipe_cells.add(cell)
            
            current_iter_length = len(current_iter_pipe_cells)

            if self.paths_this_iteration > 0:
                self.iteration_efficiency = current_iter_length / self.paths_this_iteration
            else:
                self.iteration_efficiency = float('inf')
            
            if self.iteration_efficiency < self.global_best_efficiency:
                # Found a better solution (more efficient)!
                self.global_best_efficiency = self.iteration_efficiency
                self.stagnation_counter = 0
                self.last_improvement_iteration = self.iteration
            else:
                # No improvement
                if self.paths_this_iteration > 0: # Only count stagnation if we actually found paths
                    self.stagnation_counter += 1
                
                if self.stagnation_counter >= self.convergence_threshold:
                    self.converged = True
    
    def run_iteration(self):
        """Legacy method for backward compatibility or instant run"""
        self.start_iteration()
        while not self.step():
            pass
        self.finish_iteration()
        
        # Track computational cost
        iteration_time = time.time() - start_time
        self.total_aco_cost += iteration_time
