import time
import networkx as nx
from typing import Tuple, Dict, Any, Optional

def valid_color(G: nx.Graph, node: Any, color: int, assigned: Dict[Any, int]) -> bool:
    """Check if color is valid for node given current assignments"""
    for nbr in G.neighbors(node):
        if nbr in assigned and assigned[nbr] == color:
            return False
    return True

def order_by_degree(G: nx.Graph, nodes: list) -> list:
    """Order nodes by degree (highest first)"""
    return sorted(nodes, key=lambda n: G.degree(n), reverse=True)

def mrv_order(G: nx.Graph, domains: Dict[Any, set], assigned: Dict[Any, int]) -> Any:
    """Minimum Remaining Values heuristic"""
    unassigned = [n for n in G.nodes() if n not in assigned]
    if not unassigned:
        return None
    return min(unassigned, key=lambda n: len(domains[n]))

def forward_checking_update(domains: Dict[Any, set], node: Any, color: int, 
                          G: nx.Graph, assigned: Dict[Any, int]) -> list:
    """Update domains after assignment"""
    removed = []
    for nbr in G.neighbors(node):
        if nbr in assigned:
            continue
        if color in domains[nbr]:
            domains[nbr].remove(color)
            removed.append((nbr, color))
    return removed

def restore_domains(domains: Dict[Any, set], removed: list):
    """Restore domains after backtracking"""
    for n, c in removed:
        domains[n].add(c)

def backtrack_search(G: nx.Graph, max_colors: int, use_mrv: bool = True, 
                    time_limit: Optional[float] = None) -> Tuple[bool, Dict[Any, int], float]:
    """Backtracking search with MRV and forward checking"""
    nodes = list(G.nodes())
    domains = {n: set(range(max_colors)) for n in nodes}
    assigned = {}
    start = time.perf_counter()

    degree_ordered = order_by_degree(G, nodes)

    def backtrack():
        if time_limit is not None and (time.perf_counter() - start) > time_limit:
            return False

        if len(assigned) == len(nodes):
            return True

        if use_mrv:
            var = mrv_order(G, domains, assigned)
            if var is None:
                return False
        else:
            var = next((n for n in degree_ordered if n not in assigned), None)
            if var is None:
                return False

        for color in sorted(list(domains[var])):
            if valid_color(G, var, color, assigned):
                assigned[var] = color

                removed = []
                if use_mrv:
                    removed = forward_checking_update(domains, var, color, G, assigned)

                wipeout = any(len(domains[n]) == 0 for n in G.nodes() if n not in assigned)
                if not wipeout:
                    if backtrack():
                        return True

                if use_mrv:
                    restore_domains(domains, removed)
                del assigned[var]
        return False

    ok = backtrack()
    elapsed = time.perf_counter() - start
    return ok, assigned, elapsed

def try_min_colors(G: nx.Graph, max_try: int = 10, **kwargs) -> Tuple[Optional[int], Dict[Any, int], float]:
    """Try increasing numbers of colors until valid coloring found"""
    total_time = 0.0
    
    for k in range(1, max_try + 1):
        ok, colors, t = backtrack_search(G, k, **kwargs)
        total_time += t
        
        if ok:
            return k, colors, total_time
            
        # إذا تجاوز الوقت المحدد، توقف
        time_limit = kwargs.get('time_limit')
        if time_limit and total_time > time_limit:
            break
    
    return None, {}, total_time