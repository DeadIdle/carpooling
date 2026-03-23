from .models import Node, Edge
from .bfs import find_shortest_path

def get_roadmap():
    """Returns adjacency map {node_id: [neighbour_node_ids]}"""
    road_map = {node.id: [] for node in Node.objects.all()}
    for edge in Edge.objects.select_related('source', 'destination'):
        road_map[edge.source.id].append(edge.destination.id)
    return road_map

def get_nodes_within_distance(road_map, node_id, max_hops):
    """Returns set of node_ids reachable within max_hops from node_id (BFS)."""
    visited = set()
    frontier = [node_id]

    for _ in range(max_hops):
        next_frontier = []
        for current in frontier:
            for neighbour in road_map.get(current, []):
                if neighbour not in visited:
                    visited.add(neighbour)
                    next_frontier.append(neighbour)
        frontier = next_frontier

    return visited

def calculate_detour(road_map, remaining_route, pickup_id, dropoff_id):
    """
    Finds the best place to insert pickup and dropoff into remaining_route.
    Returns (new_route, detour_hops) or (None, None) if impossible.
    """
    best_detour = None
    best_route = None

    original_len = len(remaining_route) - 1  # hops

    for i in range(len(remaining_route)):
        
        path_to_pickup, _ = find_shortest_path(road_map, remaining_route[i], pickup_id)
        if not path_to_pickup:
            continue

        path_pickup_to_dropoff, _ = find_shortest_path(road_map, pickup_id, dropoff_id)
        if not path_pickup_to_dropoff:
            continue

        # After dropoff, rejoin remaining route
        for j in range(i, len(remaining_route)):
            path_dropoff_to_route, _ = find_shortest_path(road_map, dropoff_id, remaining_route[j])
            if not path_dropoff_to_route:
                continue

            new_route = (
                remaining_route[:i + 1]
                + path_to_pickup[1:]
                + path_pickup_to_dropoff[1:]
                + path_dropoff_to_route[1:]
                + remaining_route[j + 1:]
            )

            detour = len(new_route) - 1 - original_len
            if best_detour is None or detour < best_detour:
                best_detour = detour
                best_route = new_route

    return best_route, best_detour

def calculate_fare(road_map, new_route, pickup_id, dropoff_id, existing_passengers=None, unit_price=70.0, base_fee=20.0):
    """
    fare = p * sum(1/n_i for each hop from pickup to dropoff) + base_fee
    existing_passengers: list of (pickup_id, dropoff_id) for already confirmed passengers
    """
    if existing_passengers is None:
        existing_passengers = []

    pickup_idx = new_route.index(pickup_id)
    dropoff_idx = new_route.index(dropoff_id)
    passenger_hops = new_route[pickup_idx:dropoff_idx + 1]

    fare = base_fee
    for k in range(len(passenger_hops) - 1):
        node = passenger_hops[k]
        n_i = 1
        for p_pickup, p_dropoff in existing_passengers:
            if p_pickup in new_route and p_dropoff in new_route:
                p_on = new_route.index(p_pickup)
                p_off = new_route.index(p_dropoff)
                if p_on <= new_route.index(node) < p_off:
                    n_i += 1
        fare += unit_price * (1 / n_i)

    return round(fare, 2)