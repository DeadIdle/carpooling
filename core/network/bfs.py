def find_shortest_path(road_map, start_id, end_id):
    """
    BFS on adjacency map {node_id: [neighbour_ids]}.
    Returns (path as list of node_ids, hop_count) or (None, 0).
    """
    if start_id == end_id:
        return [start_id], 0

    queue = [([start_id], 0)]
    visited = set()

    while queue:
        path, hops = queue.pop(0)
        current = path[-1]

        if current in visited:
            continue
        visited.add(current)

        for neighbour in road_map.get(current, []):
            new_path = path + [neighbour]
            if neighbour == end_id:
                return new_path, hops + 1
            queue.append((new_path, hops + 1))

    return None, 0