from collections import defaultdict
import torch

class CacheManager:
    def __init__(self):
        # Cache to store loaded map segments
        self.shared_cache = {}
        # Dictionary to store the reference count for each segment
        self.reference_counts = defaultdict(int)
        # Dictionary to track loaded segments for each session
        self.session_segments = defaultdict(set)

    def load_segments(self, server, session_id, segment_ids):
        """
        Load the segments into the cache if they are not already loaded.
        For each segment, increment its reference count.
        Segments from the same building and floor are merged into one combined map data.
        Ensure each segment_id is only loaded once per session_id.
        """
        if not isinstance(segment_ids, list):
            segment_ids = [segment_ids]

        combined_segments = {}

        for segment_id in segment_ids:
            # Parse segment_id to get building and floor
            parts = segment_id.split('_')
            building = parts[0]  # Extract building name
            floor = parts[1] + '_' + parts[2]  # Extract floor name (e.g., '6_floor')
            building_floor = f"{building}_{floor}"  # Combine to get the unique identifier for building and floor

            # If this building_floor is not yet in combined_segments, initialize its structure
            if building_floor not in combined_segments:
                combined_segments[building_floor] = {
                    'T': None,
                    'rot_base': None,
                    'perspective_frames': {},  # Use the same structure as in load_data
                }

            # Ensure we only load the segment if it's not already loaded for this session
            if segment_id not in self.session_segments[session_id]:
                # If the segment is not in cache, load it from the server
                if segment_id not in self.shared_cache:
                    loaded_map = server.load_map(segment_id)
                    if loaded_map is None:
                        continue  # Skip if there's an issue loading the map

                    # Store the loaded map in cache
                    self.shared_cache[segment_id] = loaded_map

                # Increment the reference count for the segment
                self.reference_counts[segment_id] += 1

                # Add the segment_id to the session's loaded segments
                self.session_segments[session_id].add(segment_id)

            # Access the map data for the current segment from cache
            cached_map = self.shared_cache[segment_id]

            # Merge the frames in 'perspective_frames' for this building and floor
            for frame_name, frame_data in cached_map['perspective_frames'].items():
                combined_segments[building_floor]['perspective_frames'][frame_name] = frame_data

            # Set 'T' and 'rot_base' only once, as they are the same for all segments in this building and floor
            if combined_segments[building_floor]['T'] is None:
                combined_segments[building_floor]['T'] = cached_map['T']
                combined_segments[building_floor]['rot_base'] = cached_map['rot_base']

        return combined_segments[list(combined_segments.keys())[0]]

    def release_segments(self, session_id, segment_ids):
        """
        Release the segments from the cache by decrementing their reference counts.
        If a segment's reference count reaches 0, remove it from the cache.
        Also ensure that we remove the segment from the session's loaded segment set.
        """
        if not isinstance(segment_ids, list):
            segment_ids = [segment_ids]
        
        for segment_id in segment_ids:
            if segment_id in self.session_segments[session_id]:
                if segment_id in self.reference_counts:
                    self.reference_counts[segment_id] -= 1
                    
                    # If no user is using the segment, remove it from the cache
                    if self.reference_counts[segment_id] == 0:
                        del self.shared_cache[segment_id]
                        del self.reference_counts[segment_id]

                # Remove the segment from the session's loaded segments
                self.session_segments[session_id].remove(segment_id)
