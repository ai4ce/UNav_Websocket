from collections import defaultdict, deque

# Sample interwaypoints data
interwaypoints = defaultdict(list, {
    '0': [
        {'waypoint': 'w_004', 'location': [1678.223038078417, 946.2607169046108], 'id': '0', 'index': 7, 'building': 'LightHouse', 'floor': '1_floor'},
        {'waypoint': 'w_012', 'location': [744.9179515576044, 299.2566535500814], 'id': '0', 'index': 28, 'building': 'LightHouse', 'floor': '3_floor'},
        {'waypoint': 'w_021', 'location': [1695.7738000000002, 907.1560200000002], 'id': '0', 'index': 41, 'building': 'LightHouse', 'floor': '6_floor'}
    ],

    '1': [
        {'waypoint': 'w_004', 'location': [1678.223038078417, 946.2607169046108], 'id': '1', 'index': 7, 'building': 'LightHouse', 'floor': '1_floor'},
        {'waypoint': 'w_012', 'location': [744.9179515576044, 299.2566535500814], 'id': '1', 'index': 28, 'building': 'LightHouse', 'floor': '3_floor'},
        {'waypoint': 'w_021', 'location': [1695.7738000000002, 907.1560200000002], 'id': '1', 'index': 41, 'building': 'LightHouse', 'floor': '6_floor'}
    ],
    
    '2': [
        {'waypoint': 'w_014', 'location': [167.223038078417, 96.2607169046108], 'id': '2', 'index': 6, 'building': 'Hospital', 'floor': '1_floor'},
        {'waypoint': 'w_022', 'location': [74.9179515576044, 29.2566535500814], 'id': '2', 'index': 23, 'building': 'Hospital', 'floor': '5_floor'},
        {'waypoint': 'w_043', 'location': [169.7738000000002, 97.1560200000002], 'id': '2', 'index': 35, 'building': 'Hospital', 'floor': '8_floor'}
    ],
    
    '3': [
        {'waypoint': 'w_024', 'location': [167.38078417, 96.7169046108], 'id': '3', 'index': 51, 'building': 'square', 'floor': '1_floor'},
        {'waypoint': 'w_052', 'location': [74.915576044, 29.2566500814], 'id': '3', 'index': 23, 'building': 'LightHouse', 'floor': '1_floor'}
    ],

    '4': [
        {'waypoint': 'w_052', 'location': [74.915576044, 29.2566500814], 'id': '4', 'index': 23, 'building': 'square', 'floor': '1_floor'},
        {'waypoint': 'w_046', 'location': [169.7738000002, 97.100000002], 'id': '4', 'index': 65, 'building': 'Metrotech', 'floor': '1_floor'}
    ],
    
    '5': [
        {'waypoint': 'w_024', 'location': [167.38078417, 96.7169046108], 'id': '5', 'index': 51, 'building': 'Metrotech', 'floor': '1_floor'},
        {'waypoint': 'w_052', 'location': [74.915576044, 29.2566500814], 'id': '5', 'index': 23, 'building': 'Metrotech', 'floor': '4_floor'},
        {'waypoint': 'w_046', 'location': [169.7738000002, 97.100000002], 'id': '5', 'index': 65, 'building': 'Metrotech', 'floor': '8_floor'}
    ],

    '6': [
        {'waypoint': 'w_024', 'location': [16.5453, 92.5454], 'id': '6', 'index': 52, 'building': 'Metrotech', 'floor': '1_floor'},
        {'waypoint': 'w_052', 'location': [714.53, 31.343535], 'id': '6', 'index': 35, 'building': 'Metrotech', 'floor': '4_floor'},
        {'waypoint': 'w_046', 'location': [163.1351, 92.1231231], 'id': '6', 'index': 15, 'building': 'Metrotech', 'floor': '8_floor'}
    ]
})

def find_all_paths(interwaypoints, current_building, current_floor, dest_building, dest_floor):
    paths = []

    # Helper function to get valid next waypoints
    def get_next_waypoints(current_waypoint, visited):
        next_waypoints = []
        for inter_id, waypoints in interwaypoints.items():
            for waypoint in waypoints:
                # Check if it's a valid transition (same building/floor or connected via interwaypoints)
                if waypoint['building'] == current_waypoint['building'] and waypoint['floor'] == current_waypoint['floor']:
                    if waypoint['waypoint'] != current_waypoint['waypoint'] and waypoint not in visited:
                        next_waypoints.append(waypoint)
                elif waypoint['id'] == current_waypoint['id'] and waypoint not in visited:
                    next_waypoints.append(waypoint)
        return next_waypoints
    
    # BFS search for paths
    queue = deque()

    # Enqueue all interwaypoints in the current building and floor
    for inter_id, waypoints in interwaypoints.items():
        for waypoint in waypoints:
            if waypoint['building'] == current_building and waypoint['floor'] == current_floor:
                queue.append((waypoint, [waypoint], defaultdict(int)))  # (current_waypoint, path_so_far, id_count)

    while queue:
        current_waypoint, path_so_far, id_count = queue.popleft()

        # Update the count of the current waypoint's id
        id_count[current_waypoint['id']] += 1
        
        # If any id is visited more than twice, skip this path
        if id_count[current_waypoint['id']] > 2:
            continue

        # If we've reached the destination building and floor, check if the path is valid
        if current_waypoint['building'] == dest_building and current_waypoint['floor'] == dest_floor:
            # Ensure each id has been visited exactly twice
            if all(count == 2 for count in id_count.values()):
                paths.append(path_so_far)
            continue
        
        # Get next valid waypoints
        next_waypoints = get_next_waypoints(current_waypoint, path_so_far)
        for next_waypoint in next_waypoints:
            # Pass along the current id_count dictionary
            new_id_count = id_count.copy()
            queue.append((next_waypoint, path_so_far + [next_waypoint], new_id_count))
    
    return paths

# Example usage
current_building = 'LightHouse'
current_floor = '6_floor'
dest_building = 'LightHouse'
dest_floor = '6_floor'

paths = find_all_paths(interwaypoints, current_building, current_floor, dest_building, dest_floor)

# Output all paths
for idx, path in enumerate(paths):
    print(f"Path {idx + 1}:")
    for step in path:
        print(step)
