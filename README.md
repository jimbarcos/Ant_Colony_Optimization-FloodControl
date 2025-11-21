# Flood Control System - Ant Colony Optimization

An interactive simulation that uses Ant Colony Optimization (ACO) to find optimal drainage paths in a randomly generated city for flood control. Features real-time flood simulation with rain and water flow dynamics.

## Features

-   **Randomly Generated City**: Each city is unique with houses, roads, trees, and varied elevation
-   **Ant Colony Optimization**: Simulates ant behavior to find optimal drainage routes
-   **Flood Simulation**: Real-time water accumulation and drainage with adjustable rain
-   **Interactive Controls**: Adjust parameters in real-time and modify the city layout
-   **Visual Feedback**: See pheromone trails, elevation maps, water levels, and drainage paths
-   **Comprehensive Legend**: Clear indicators for all city elements and flood status
-   **Responsive Design**: Resizable window and fullscreen support (F11)
-   **Budget System**: Manage your budget for drains and pipes with detailed cost breakdown

## Installation

### Windows PowerShell

1.  Install Python dependencies:
    ```powershell
    pip install -r requirements.txt
    ```

## Running the Application

```powershell
python main.py
```

## How It Works

### Ant Colony Optimization
-   **Ants** start at random positions and navigate toward drains
-   **Pheromones** are deposited along successful paths to drains (like scent trails)
-   **Elevation** influences ant movement (prefer downhill paths)
-   Over iterations, optimal drainage paths emerge
-   **Stagnation Convergence**: The algorithm stops when the best path found hasn't improved for 20 iterations.

### Flood Control Simulation
-   **Rain**: Trigger rainfall to add water to the city
-   **Water Flow**: Water flows downhill following elevation
-   **Drainage**: Drains remove water from the system
-   **Visual Overlay**: See flood levels in real-time with depth-based color gradient
-   Watch how well your drainage system handles flooding!

### City Generation
-   **Elevation Map**: Randomized terrain with hills and valleys
-   **Roads**: Grid pattern connecting city blocks
-   **Houses**: Clustered residential areas
-   **Trees**: Scattered vegetation
-   **Drains**: Initially placed at low elevation points (natural water collection)

## Controls

| Key | Action |
| :--- | :--- |
| **ENTER** | Start Optimization / Defending Phase |
| **F11** | Toggle Fullscreen |
| **T** | Toggle Tutorial |
| **G** | Toggle Grid |
| **I** | Toggle Icons |
| **W** | Toggle Water Overlay |
| **R** | Reset / New City |
| **E** | Toggle Elevation View |
| **P** | Toggle Pheromone View |
| **Left Click** | Add drain (Setup) |
| **Right Click** | Remove drain (Setup) |

## Legend

-   🔴 **Red**: Houses (with roof icon)
-   ⚫ **Dark Gray**: Roads
-   🟢 **Green**: Trees (with tree icon)
-   🔵 **Blue**: Drains (water collection points with icon)
-   ⚫ **Black**: Obstacles (blocking drainage)
-   🟡 **Yellow**: Discovered drainage paths
-   💧 **Water Gradient**: Light Blue (Shallow) to Dark Blue (Deep)
-   🟣 **Purple**: Low Pheromone Trail
-   🟠 **Orange**: High Pheromone Trail

## Tips

1.  **Start Setup**: Place drains strategically in low-lying areas (use Elevation view 'E').
2.  **Optimize**: Press ENTER to let the ants find the best pipe routes.
3.  **Adjust Speed**: Use the animation speed slider to speed up the optimization.
4.  **Defend**: Press ENTER again to start the rain simulation.
5.  **Monitor Budget**: Watch your spending on drains and pipes. The endgame screen shows a detailed breakdown.
6.  **Adjust Parameters**:
    -   More ants = faster exploration but more chaotic
    -   Higher pheromone strength = faster convergence to solutions
    -   Lower evaporation = paths persist longer

## Parameters Explained

-   **Ants**: Number of ants per iteration (5-50)
-   **Evaporation Rate**: How quickly pheromones fade (0.01-0.5)
-   **Pheromone Strength**: How much "scent" ants leave on successful paths
-   **Rain Intensity**: Amount of water added per rain cycle
-   **Alpha**: Importance of pheromone trail (History)
-   **Beta**: Importance of distance/heuristic (Greedy)

## Visualization Modes

-   **Normal**: Shows city layout with drainage paths
-   **Elevation Mode (E)**: Displays terrain elevation (lighter = higher ground)
-   **Pheromone Mode (P)**: Shows pheromone concentration (Purple -> Orange)
-   **Water Overlay (W)**: Displays flood water levels (Light Blue -> Dark Blue)

## Performance Improvements

This version includes several optimizations:
-   **Smaller Grid**: 15x15 ensures faster convergence and better performance
-   **Efficient Rendering**: Dynamic cell sizing for any screen resolution
-   **Smart Convergence**: Stops when optimal paths are found to save time
