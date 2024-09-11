import numpy as np
from scipy.sparse.csgraph import shortest_path
from UNav_core.src.loader import data_loader
from collections import defaultdict, deque
import math

class Trajectory():
    def __init__(self, all_buildings_data, all_interwaypoint_connections):
        self.all_buildings_data = all_buildings_data
        self.all_interwaypoint_connections = all_interwaypoint_connections
        self.precalculated_inter_paths = self._precalculated_inter_paths()
        self.precalculated_global_paths = self._precalculate_global_paths()

    def _find_all_paths(self, current_building, current_floor, dest_building, dest_floor):
        paths = []

        # Helper function to get valid next waypoints
        def get_next_waypoints(current_waypoint, visited):
            next_waypoints = []
            for inter_id, waypoints in self.all_interwaypoint_connections.items():
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
        for inter_id, waypoints in self.all_interwaypoint_connections.items():
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

    # Function to precalculate all possible paths between every building and floor combination
    def _precalculate_global_paths(self):
        # Store the precalculated paths
        precalculated_paths = defaultdict(dict)

        # Use keys from self.all_buildings_data to get all building and floor combinations
        for current_building, floors in self.all_buildings_data.items():
            for current_floor, _ in floors.items():
                for dest_building, dest_floors in self.all_buildings_data.items():
                    for dest_floor, _ in dest_floors.items():
                        # Skip if the start and destination are the same
                        if current_building == dest_building and current_floor == dest_floor:
                            continue

                        # Calculate all paths between the start and destination
                        paths = self._find_all_paths(current_building, current_floor, dest_building, dest_floor)

                        # Store the result
                        precalculated_paths[(current_building, current_floor)][(dest_building, dest_floor)] = paths

        return precalculated_paths
    
    def update_destination_graph(self, navigation_states):
        self.destination_place = navigation_states['Place']
        self.destination_building = navigation_states['Building']
        self.destination_floor = navigation_states['Floor']
        
        floor_data = self.all_buildings_data.get(self.destination_building,{}).get(self.destination_floor,{})

        self.destination_bounderies = floor_data.get('boundaries')
        self.destination_waypoints = floor_data.get('waypoints')
        self.destination_M = floor_data.get('access_graph')
        self.destination_interwaypoints = floor_data.get('interwaypoints')

        destination_anchor_location = self._form_anchor_points(floor_data.get('destinations'), floor_data.get('waypoints'))

        selected_destination_ID = navigation_states['Selected_destination_ID']
        destination_info = floor_data.get('destinations').get(selected_destination_ID)
        
        self.destination_index = None
        if destination_info:
            # Find the index of the selected destination ID by iterating over the keys
            for idx, dest_id in enumerate(floor_data.get('destinations').keys()):
                if dest_id == selected_destination_ID:
                    self.destination_index = idx
                    break
                
        _, Pr = shortest_path(self.destination_M, directed=True, method='FW', return_predecessors=True)
        
        self.dest_from_inter = defaultdict(dict)
        for interwaypoint in self.destination_interwaypoints:
            self.dest_from_inter[interwaypoint['index']] = self._trace_back_path(Pr, destination_anchor_location, interwaypoint['index'], self.destination_index)
            
    def _precalculated_inter_paths(self):
        path_between_interwaypoints = defaultdict(dict)
        
        for building, building_data  in self.all_buildings_data.items():
            for floor, floor_data  in building_data.items():
                
                current_M = floor_data.get('access_graph')
                _, Pr = shortest_path(current_M, directed=True, method='FW', return_predecessors=True)
                
                interwaypoints = floor_data.get('interwaypoints')
                
                interwaypoints_index_in_floor = [interwaypoint.get('index') for interwaypoint in interwaypoints]
                
                anchor_location =  self._form_anchor_points(floor_data.get('destinations'), floor_data.get('waypoints'))
                
                for current_index in interwaypoints_index_in_floor:
                    for target_index in interwaypoints_index_in_floor:
                        if current_index < target_index:
                            path_between_interwaypoints[(building, floor)][(current_index, target_index)] = self._trace_back_path(Pr, anchor_location, current_index, target_index)
                            path_between_interwaypoints[(building, floor)][(target_index, current_index)] = path_between_interwaypoints[(building, floor)][(current_index, target_index)]
                            
        return path_between_interwaypoints
    
    def _form_anchor_points(self, destinations, waypoints):
        """
        Forms a list of anchor points by extracting the location data from destinations and waypoints.
        
        Args:
            destinations (dict): Dictionary containing destination data.
            waypoints (dict): Dictionary containing waypoint data.
            
        Returns:
            list: A list of anchor points (locations) extracted from destinations and waypoints.
        """
        anchor_points = []

        # Iterate through destinations and extract the location
        for dest_id, dest_info in destinations.items():
            location = dest_info.get('location')
            if location:
                anchor_points.append(location)

        # Iterate through waypoints and extract the location
        for waypoint_id, waypoint_info in waypoints.items():
            location = waypoint_info.get('location')
            if location:
                anchor_points.append(location)

        return anchor_points

    def _ccw(self, A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def _distance(self, c, d):
        for boundary in self.current_bounderies:
            a, b = [boundary[0], boundary[1]], [boundary[2], boundary[3]]
            if self._ccw(a, c, d) != self._ccw(b, c, d) and self._ccw(a, b, c) != self._ccw(a, b, d):
                return 0
        return np.linalg.norm(np.array(c) - np.array(d))

    def _calculate_trajectory_length(self, points):
        total_length = 0.0
        
        # Iterate over the list of points, calculating distance between consecutive pairs
        for i in range(1, len(points)):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]
            
            # Calculate the Euclidean distance between consecutive points
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            
            # Add to the total length
            total_length += distance
        
        return total_length
    
    def calculate_path(self, localization_states):
        current_building = localization_states['building']
        current_floor = localization_states['floor']
        current_pose = localization_states['pose']
        
        floor_data = self.all_buildings_data.get(current_building, {}).get(current_floor, {})
        self.current_bounderies = floor_data.get('boundaries')
        self.current_waypoints = floor_data.get('waypoints')
        self.current_M = floor_data.get('access_graph')
        self.current_interwaypoints = floor_data.get('interwaypoints')
        
        current_anchor_location = self._form_anchor_points(floor_data.get('destinations'), floor_data.get('waypoints'))
        
        # Update the access graph matrix for the current pose
        for i, loc in enumerate(current_anchor_location):
            self.current_M[i, -1] = self._distance(current_pose[:2], loc)
        
        # Find shortest path within current floor using Floyd-Warshall
        _, Pr = shortest_path(self.current_M, directed=True, method='FW', return_predecessors=True)
        
        trajectory = defaultdict(dict)
        
        # If current building and floor match the destination, calculate shortest path directly
        if (current_building, current_floor) == (self.destination_building, self.destination_floor) and self.destination_index:
            trajectory['destination'] = [[current_pose[0], current_pose[1]]] + self._trace_back_path(Pr, current_anchor_location, -1, self.destination_index)
        else:
            possible_paths = self.precalculated_global_paths.get((current_building, current_floor), {}).get((self.destination_building, self.destination_floor), {})
            
            min_diatance = float('inf')
            
            for path_candidate in possible_paths:
                enter_id = set()
                local_trajectory = defaultdict(dict)
                distance = 0
                for step, step_info in enumerate(path_candidate):
                    inter_name = step_info.get('name')
                    floor = step_info.get('floor')
                    building = step_info.get('building')
                    if step == 0:
                        current_to_interwaypoints = [[current_pose[0], current_pose[1]]] + self._trace_back_path(Pr, current_anchor_location, -1, step_info.get('index'))
                        distance += self._calculate_trajectory_length(current_to_interwaypoints)
                        local_trajectory[(building, floor, inter_name)] = current_to_interwaypoints
                    elif step == len(path_candidate) - 1:
                        interwaypoints_to_dest = self.dest_from_inter.get(step_info.get('index'))
                        distance += self._calculate_trajectory_length(interwaypoints_to_dest)
                        local_trajectory[(building, floor, 'destination')] = interwaypoints_to_dest
                    else:
                        inter_id = step_info.get('id')
                        inter_index = step_info.get('index')
                        if inter_id not in enter_id:
                            enter_id.add(inter_index)
                            building = step_info.get('building')
                            floor = step_info.get('floor')
                            target_index = step_info.get('index')
                            inter_paths = self.precalculated_inter_paths.get((building, floor)).get((current_index, target_index))
                            distance += self._calculate_trajectory_length(inter_paths)
                            local_trajectory[(building, floor, inter_name)] = inter_paths
                        else:
                            current_index = step_info.get('index')
                if distance < min_diatance:
                    min_diatance = distance
                    trajectory = local_trajectory
        return trajectory
            
    def _get_waypoint_index(self, waypoint_id, anchor_points):
        """
        Get the index of a waypoint in the anchor points list.
        """
        for idx, waypoint in enumerate(anchor_points):
            if waypoint_id == waypoint:
                return idx
        return None

    def _trace_back_path(self, predecessors, locations, current_index, destination_index):
        """
        Trace back the path from the destination index using the predecessor matrix.
        """
        path_list=[]
        
        index = destination_index
        predecessors=predecessors[index]
        
        index=predecessors[current_index]
        while index!=-9999:
            path_list.append(locations[index])
            index=predecessors[index]

        return path_list

    def _calculate_path_from_interwaypoint_to_dest(self, interwaypoint, interwaypoints_destination):
        """
        Calculate the path from an interwaypoint on the current floor to the destination.
        """
        # Get the connections between the interwaypoints on the current floor and the destination floor
        possible_paths = []
        for destination_interwaypoint in interwaypoints_destination:
            connection_path = self._find_interwaypoint_connection(interwaypoint, destination_interwaypoint)
            if connection_path:
                possible_paths.append(connection_path)

        # Return the shortest connection between floors
        if possible_paths:
            return min(possible_paths, key=len)
        return []

    def _find_interwaypoint_connection(self, interwaypoint_current, interwaypoint_destination):
        """
        Find the connection between two interwaypoints across different floors or buildings.
        """
        connections = self.all_interwaypoint_connections.get(interwaypoint_current['index'], [])
        for connection in connections:
            if connection['floor'] == interwaypoint_destination['floor'] and connection['building'] == interwaypoint_destination['building']:
                return [interwaypoint_current['location'], interwaypoint_destination['location']]
        return []

        
# class Trajectory():
#     def __init__(self, connection_graph, boundaries, waypoints):
        
#         #load data and whole building's dict
#         self.M_dict = {}
#         self.M_dict[map_data['floor']] = map_data['graph']
#         self.lines_dict = {}
#         self.lines_dict[map_data['floor']] = map_data['lines']
#         self.anchor_name_dict = {}
#         self.anchor_name_dict[map_data['floor']] = [tuple([name] + [map_data['floor']]) for name in map_data['anchor_name']]
#         self.anchor_location_dict = {}
#         self.anchor_location_dict[map_data['floor']] = [loc + [map_data['floor']] for loc in map_data['anchor_location']]

#         self.interwaypoints = map_data['interwaypoints']  # 新增: 包含 interwaypoints 的信息

#         #check if graph data has the same length as anchor_name data plus 1 (for start point)
#         leng_M = len(self.M_dict[map_data['floor']])
#         leng_anchor = len(self.anchor_name_dict[map_data['floor']])
#         if not len(self.M_dict[map_data['floor']]) == len(self.anchor_name_dict[map_data['floor']]) + 1 :
#             print(f'Warning: current floor graph M dimension is not current waypoints and destionation locations\' dimension plus 1')
#             print(f'length of current floor graph M: {leng_M}')
#             print(f'length of current waypoint and destination location plus 1 {leng_anchor}')

#         #cross floor map loading
#         self.place = map_data['place']
#         self.building = map_data['building']
#         self.floor = map_data['floor']

#         self.destination_place = None 
#         self.destination_building = None
#         self.destination_floor = None

#         self.is_crossfloor = False
#         self.cross_floor_cost = 5  # 跨楼层固定成本
    

    # def ccw(self, A, B, C):
    #     return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    # def distance(self, c, d, floor):
    #     # print(f'c: {tuple(c)}')
    #     # print(f'd: {tuple(d)}')
    #     if c[2] == d[2]:  # 如果在同一楼层
    #         for boundary in self.lines_dict[floor]:
    #             a, b = [boundary[0], boundary[1]], [boundary[2], boundary[3]]
    #             if self.ccw(a, c[:2], d[:2]) != self.ccw(b, c[:2], d[:2]) and self.ccw(a, b, c[:2]) != self.ccw(a, b, d[:2]):
    #                 return 0
    #         return np.linalg.norm(np.array(c[:2]) - np.array(d[:2]))
    #     else:
    #         return float('inf')
    

#     def calculate_path_within_floor(self, pose, destination_id, floor, start_index = -1):
#         for i, loc in enumerate(self.anchor_location_dict[floor]):
#             self.M_dict[floor][i, start_index] = self.distance(pose+[floor], loc, floor)

#         # print("Updated distances from pose to all locations in M:")
#         # print(self.M_dict[floor][:, -1])  # 打印最后一列，即起点到所有点的距离
#         distance, Pr = shortest_path(self.M_dict[floor], directed=True, method='FW', return_predecessors=True)
#         start_index = len(self.M_dict[floor]) - 1
#         index=self.anchor_name_dict[floor].index((destination_id,floor))
#         # print(f'anchor_name: {self.anchor_name_dict[floor]}')
#         # print(f'index0: {index}')
#         # print(f'Pr1: {Pr}')
#         destination_index = index
#         Pr=Pr[index]
#         # print(f'Pr2: {Pr}')
#         # print(f'index1: {index}')
#         path_list=[]
#         index=Pr[-1]
#         # print(f'index2: {index}')
#         while index!=-9999:
#             path_list.append(self.anchor_location_dict[floor][index])
#             index=Pr[index]
#         return path_list, self.M_dict[floor][destination_index, -1]

#     def calculate_path(self, pose, destination_id,current_floor):
#         if current_floor not in self.anchor_name_dict.keys():
#             print(f'Error: current floor is not loaded in navigation system')
#             exit(0)
#         #if not crossfloor navigation 
#         if not self.is_crossfloor:
#             path_list, total_cost = self.calculate_path_within_floor(pose,destination_id,current_floor)
#             return path_list
#         else:
#         #if crossfloor navigation
#             #first identify the elevator indexs num in this building
#             cross_num = len(self.interwaypoints.keys()) 

#             # using different rountes to find the best path 
#             min_cost = float('inf') 
#             path_list = []
#             for k,v in self.interwaypoints.items():
#                 for interwaypoint in v:
#                     interwaypoint = list(interwaypoint)
#                     if interwaypoint[2] == current_floor:
#                         elevator1_index = self.anchor_location_dict[current_floor].index(interwaypoint)
#                         elevator1_id, _ = self.anchor_name_dict[current_floor][elevator1_index]
#                         # print(f'elevator1_id :  {elevator1_id}')
#                         path_1, cost_c_to_point_c = self.calculate_path_within_floor(pose,elevator1_id,current_floor)
#                     if interwaypoint[2] == self.destination_floor: 
#                         elevator2_index = self.anchor_location_dict[self.destination_floor].index(interwaypoint)
#                         elevator2_id, _ = self.anchor_name_dict[self.destination_floor][elevator2_index]  
#                         # print(f'elevator2_id: {elevator2_id}')
#                         elevator2_pose = interwaypoint[:2]
#                         path_2, cost_point_d_to_d = self.calculate_path_within_floor(elevator2_pose,destination_id,self.destination_floor,start_index=elevator2_index)
                    
#                 total_cost =  cost_c_to_point_c + self.cross_floor_cost + cost_point_d_to_d   
#                 if total_cost < min_cost:
#                     min_cost = total_cost
#                     path_list = path_1 + path_2

#                 # print(f'cost_c_to_point_c : {cost_c_to_point_c}')
#                 # print(f'cost_point_d_to_d : {cost_point_d_to_d}')
#             return path_list
    
#     def update_destination_map(self,Place, Building, Floor):
        
#         #check if crossfloor 
#         #check if destination map loaded
#         if self.place == Place and self.building == Building and self.floor == Floor:
#             self.is_crossfloor = False
#         else:
#             self.is_crossfloor = True

#             #change the destination_place
#             self.destination_place = Place
#             self.destination_building = Building
#             self.destination_floor = Floor
#             self.load_another_map()
#         return
    
#     def load_another_map(self):       
#         #update map data from loader
#         additional_data = data_loader.load_another_map_boundaries(self.destination_place,self.destination_building,self.destination_floor)
        
#         # loading map data
#         # boundary
#         self.lines_dict[self.destination_floor]= additional_data['lines']
#         self.M_dict[self.destination_floor] = additional_data['graph'][:-1, :-1]

        
#         self.anchor_name_dict[self.destination_floor] = [tuple([name] + [self.destination_floor]) for name in additional_data['anchor_name']]
#         self.anchor_location_dict[self.destination_floor] = [loc + [self.destination_floor] for loc in additional_data['anchor_location']]

#         #check if graph data has the same length as anchor_name data 
#         leng_M = len(self.M_dict[self.destination_floor])
#         leng_anchor = len(self.anchor_name_dict[self.destination_floor])
#         if not len(self.M_dict[self.destination_floor]) == len(self.anchor_name_dict[self.destination_floor]) + 1 :
#             print(f'Warning: destination floor graph M dimension is not destiation waypoints and destionation locations\' dimensions ')
#             print(f'length of destination floor graph M: {leng_M}')
#             print(f'length of destination waypoint and destination location plus 1 {leng_anchor}')

#         #interwaypoints:
#         additional_interwaypoints = additional_data['interwaypoints']
#         for k,v in additional_interwaypoints.items():
#             if k in self.interwaypoints.keys():
#                 self.interwaypoints[k].extend(v)
#             else:
#                 print(f'Error {k} is not in original floor interwaypoints')
#                 exit(0)
#         print(self.interwaypoints)

#         return

# 示例 map_data 结构需要包括 interwaypoints 的信息
# interwaypoints 例子: [{'index': 1, 'locations': [(x1, y1, floor1), (x2, y2, floor2)]}, ...]