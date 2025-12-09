# cultural.py
import random
import time
from typing import List, Dict, Tuple, Any, Optional
import networkx as nx

def fitness(coloring: List[int], G: nx.Graph) -> int:
    """Calculate fitness: negative of conflicts"""
    conflicts = 0
    for u, v in G.edges():
        if coloring[u] == coloring[v]:
            conflicts += 1
    return -conflicts

def create_individual(num_vertices: int, k: int) -> List[int]:
    """Create random coloring"""
    return [random.randint(0, k-1) for _ in range(num_vertices)]

def smart_mutate(individual: List[int], k: int, G: nx.Graph) -> List[int]:
    """Smart mutation - try different colors for each vertex"""
    coloring = individual[:]
    for _ in range(50):  # Try up to 50 smart mutations
        v = random.randint(0, len(coloring) - 1)
        old_color = coloring[v]
        
        # Try all possible colors in random order
        for new_color in random.sample(range(k), k):
            if new_color == old_color:
                continue
            coloring[v] = new_color
            if fitness(coloring, G) > fitness(individual, G):
                return coloring  # Return if improvement found
        coloring[v] = old_color  # Revert if no improvement
    return coloring

def cultural_algorithm_for_k(G: nx.Graph, k: int, pop_size: int = 50, 
                           max_gen: int = 10, mutation_rate: float = 0.1,  # Changed default from 100 to 10
                           progress_callback: callable = None) -> Tuple[bool, List[int], int, int, List[Dict]]:
    """Cultural Algorithm for specific k - similar to old version"""
    
    num_vertices = G.number_of_nodes()
    
    # Initialize population
    population = [create_individual(num_vertices, k) for _ in range(pop_size)]
    
    # Initialize belief space
    belief_space = {
        "best_ever": max(population, key=lambda ind: fitness(ind, G)).copy(),
        "generational_best": None
    }
    
    best_solution = None
    best_fitness = float('-inf')
    history = []
    last_generation = 0  # تخزين الجيل الأخير
    
    start_time = time.time()
    
    print(f"Trying to color with {k} colors...")
    
    for generation in range(1, max_gen + 1):
        last_generation = generation  # تحديث الجيل الأخير
        
        # Create new population with cultural influence
        new_population = [belief_space["best_ever"].copy()]  # Always keep best
        
        while len(new_population) < pop_size:
            if random.random() < 0.15:  # 15% chance for random individual
                child = create_individual(num_vertices, k)
            else:  # 85% chance for smart mutation of best solution
                child = smart_mutate(belief_space["best_ever"], k, G)
            new_population.append(child)
        
        population = new_population
        
        # Find current best
        current_best = max(population, key=lambda ind: fitness(ind, G))
        current_best_fitness = fitness(current_best, G)
        
        # Update belief space if improved
        if current_best_fitness > fitness(belief_space["best_ever"], G):
            belief_space["best_ever"] = current_best.copy()
        
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = current_best.copy()
        
        # Calculate metrics
        conflicts = -current_best_fitness
        colors_used = len(set(current_best))
        
        # Record history
        history.append({
            'generation': generation,
            'conflicts': conflicts,
            'colors_used': colors_used,
            'best_fitness': current_best_fitness
        })
        
        # Progress callback - عرض كل جيل بدلاً من كل 10 أجيال فقط
        if progress_callback:
            progress_callback(generation, conflicts, colors_used)
        
        # Print progress (like old version)
        if generation % 10 == 0 or conflicts == 0 or generation == max_gen:  # Added generation == max_gen
            print(f"Gen {generation:3d} | Conflicts: {conflicts:3d} | Colors used: {colors_used}")
        
        # Check for solution
        if conflicts == 0:
            elapsed = time.time() - start_time
            print(f"Valid coloring found with {k} colors in {generation} generations!")
            return True, current_best, colors_used, 0, history
    
    # If no solution found within max generations
    elapsed = time.time() - start_time
    conflicts = -best_fitness
    colors_used = len(set(best_solution)) if best_solution else k
    
    # عرض الجيل الأخير دائماً
    print(f"Final Generation {last_generation:3d} | Conflicts: {conflicts:3d} | Colors used: {colors_used}")
    print(f"Failed with {k} colors (best conflicts: {conflicts})")
    
    return False, best_solution, colors_used, conflicts, history

# باقي الدوال تبقى كما هي بدون تغيير...
def find_chromatic_number(G: nx.Graph, pop_size: int = 50, max_gen: int = 10,  # Changed default from 100 to 10
                         mutation_rate: float = 0.1, max_k: int = 20,
                         progress_callback: callable = None) -> Tuple[Optional[int], Dict, float]:
    """Find chromatic number by trying increasing k values - like old version"""
    
    print("Searching for the smallest number of colors...")
    total_start = time.time()
    
    for k in range(1, max_k + 1):
        success, coloring, colors_used, conflicts, history = cultural_algorithm_for_k(
            G, k, pop_size, max_gen, mutation_rate, progress_callback
        )
        
        if success:
            total_time = time.time() - total_start
            coloring_dict = {i: coloring[i] for i in range(len(coloring))}
            
            print("=" * 50)
            print(f"SUCCESS! Graph is {k}-colorable")
            print(f"Chromatic number = {k}")
            print(f"Colors used: {colors_used}")
            print(f"Total time: {total_time:.2f} seconds")
            print("=" * 50)
            
            return k, coloring_dict, total_time
    
    print("No solution found with reasonable k.")
    return None, {}, time.time() - total_start

# Keep the original cultural_algorithm function for backward compatibility
def cultural_algorithm(G: nx.Graph, pop_size: int = 50, max_gen: int = 10,  # Changed default from 100 to 10
                      mutation_rate: float = 0.1, k: int = None,
                      progress_callback: callable = None) -> Tuple[bool, List[int], int, int, List[Dict]]:
    """Main cultural algorithm function that tries to find solution with given or optimal k"""
    
    if k is not None:
        # Use specified k
        return cultural_algorithm_for_k(G, k, pop_size, max_gen, mutation_rate, progress_callback)
    else:
        # Find optimal k
        result = find_chromatic_number(G, pop_size, max_gen, mutation_rate, 
                                     max_k=20, progress_callback=progress_callback)
        k_found, coloring_dict, total_time = result
        
        if k_found is not None:
            coloring_list = [coloring_dict[i] for i in range(len(coloring_dict))] if k_found else []
            return True, coloring_list, k_found, 0, [] if k_found else []
        else:
            return False, [], 0, 0, []