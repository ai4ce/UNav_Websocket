from UNav_core.src.feature.local_extractor import Local_extractor
from UNav_core.src.third_party.local_feature.LightGlue.lightglue.utils import load_image, match_pair
import torch
import numpy as np

class Local_matcher():
    device='cuda' if torch.cuda.is_available() else "cpu"
    def __init__(self, frame_name, map_data, threshold = 10, **feature_configs):
        local_feature = Local_extractor(feature_configs['local'])
        self.local_feature_matcher = local_feature.matcher().to(self.device)

        self.frame_name = frame_name
        
        self.map_data = map_data
        
        self.threshold = threshold
        
    def match_filter(self, matches, feats0, feats1, valid_landmarks):
        pts0 = []
        pts1 = []
        lms = []
        
        # Iterate over matches and filter using valid_landmarks
        for n, m in enumerate(matches):
            if m != -1 and m in valid_landmarks:
                pts0.append(feats0['keypoints'][n])
                pts1.append(feats1['keypoints'][m])
                lms.append(valid_landmarks[m])
        
        return np.array(pts0), np.array(pts1), np.array(lms)


    def lightglue_batch(self, parent, topk, feats0):
        batch_size = len(topk)
        mini_batch_size = 15
        batch_list = [min(mini_batch_size, batch_size - i) for i in range(0, batch_size, mini_batch_size)]

        pts0_list, pts1_list, lms_list= [], [], []

        index = 0

        max_matched_num = 0
        
        # Precompute the static components of feats0 once
        feats0_descriptors = torch.tensor(feats0['descriptors']).unsqueeze(0).to(self.device)
        feats0_image_size = torch.tensor(feats0['image_size']).unsqueeze(0).to(self.device)
        feats0_keypoints = torch.tensor(feats0['keypoints']).unsqueeze(0).to(self.device)
        feats0_scores = torch.tensor(feats0['scores']).unsqueeze(0).to(self.device)
        
        valid_db_frame_name = []
        
        for batch in batch_list:
            valid_keypoints_index, landmarks_list = [],[]
            batch_topk = topk[index:index+batch]
                
            
            # Pre-allocate the data structure for feats1
            desc_dim = feats0_descriptors.shape[1]
            max_len = max(len(self.map_data[self.frame_name[i]]['local_features']['keypoints']) for i in batch_topk)
            
            descriptors = torch.zeros((batch, desc_dim, max_len), device=self.device)
            keypoints = torch.zeros((batch, max_len, 2), device=self.device)
            scores = torch.zeros((batch, max_len), device=self.device)
            image_size = torch.zeros((batch, 2), device=self.device)

            for idx, i in enumerate(batch_topk):
                frame_data = self.map_data[self.frame_name[i]]
                
                landmarks_list.append(frame_data['landmarks'])
                
                local_features = frame_data['local_features']
                
                valid_keypoints_index.append(local_features['valid_keypoints_index'])
                
                current_len = len(local_features['keypoints'])
                
                keypoints[idx, :current_len, :] = torch.tensor(local_features['keypoints'], device=self.device)
                descriptors[idx, :, :current_len] = torch.tensor(local_features['descriptors'], device=self.device)
                scores[idx, :current_len] = torch.tensor(local_features['scores'], device=self.device)
                image_size[idx, :] = torch.tensor(local_features['image_size'], device=self.device)

            # Prepare pred for matching
            pred = {
                'descriptors0': feats0_descriptors.repeat(batch, 1, 1),
                'image_size0': feats0_image_size.repeat(batch, 1),
                'keypoints0': feats0_keypoints.repeat(batch, 1, 1),
                'keypoint_scores0': feats0_scores.repeat(batch, 1),
                'descriptors1': descriptors,
                'image_size1': image_size,
                'keypoints1': keypoints,
                'keypoint_scores1': scores,
            }

            # Perform inference
            with torch.inference_mode():
                pred1 = self.local_feature_matcher(pred)
            matches = pred1['matches0'].detach().cpu().short().numpy()

            
            # Process matches
            for ind, match in enumerate(matches):

                feat0 = pred['keypoints0'][ind].detach().cpu().numpy()
                feat1 = pred['keypoints1'][ind].detach().cpu().numpy()
                
                valid_landmarks = {valid_id:landmark for valid_id,landmark in zip(valid_keypoints_index[ind], landmarks_list[ind])}

                pts0, pts1, lms = [], [], []
                for n, m in enumerate(match):
                    if m != -1 and m in valid_landmarks:
                        pts0.append(feat0[n])
                        pts1.append(feat1[m])
                        lms.append(valid_landmarks[m])
                
                inlier_num = len(pts0)
                if inlier_num > self.threshold:
                    valid_db_frame_name.append(parent.db_name[ind + index])
                    if max_matched_num < inlier_num:
                        max_matched_num = inlier_num
                    pts0_list.append(np.array(pts0))
                    pts1_list.append(np.array(pts1))
                    lms_list.append(np.array(lms))

            index += batch

        return valid_db_frame_name, pts0_list, pts1_list, lms_list, max_matched_num


    def lightglue(self, i, feats0):
        # Fetch local features and landmarks for the selected frame
        local_features = self.map_data[self.frame_name[i]]['local_features']
        landmarks = self.map_data[self.frame_name[i]]['landmarks']
        valid_keypoints_index = local_features['valid_keypoints_index']

        feats1 = {
            'descriptors': local_features['descriptors'],
            'image_size': local_features['image_size'],
            'scores': local_features['scores'],
            'keypoints': local_features['keypoints'],
        }

        # Create a mapping for valid landmarks using valid_keypoints_index
        valid_landmarks = {valid_id: landmarks[valid_id] for valid_id in valid_keypoints_index}

        # Batch data transfer to GPU
        pred = {
            **{k + '0': torch.tensor(np.array(v)).unsqueeze(0).to(self.device) for k, v in feats0.items()},
            **{k + '1': torch.tensor(np.array(v)).unsqueeze(0).to(self.device) for k, v in feats1.items()},
        }

        # Perform inference using local feature matcher
        with torch.inference_mode():
            pred = self.local_feature_matcher(pred)

        # Extract matches
        matches = pred['matches0'][0].detach().cpu().short().numpy()

        # Use match_filter to filter valid matches based on valid_landmarks
        pts0, pts1, lms = self.match_filter(matches, feats0, feats1, valid_landmarks)
        
        return [pts0, pts1, lms]

        
    def superglue(self, i, feats0):
        # Fetch local features and landmarks for the selected frame
        local_features = self.map_data[self.frame_name[i]]['local_features']
        landmarks = self.map_data[self.frame_name[i]]['landmarks']
        valid_keypoints_index = local_features['valid_keypoints_index']

        feats1 = {
            'descriptors': local_features['descriptors'],
            'image_size': local_features['image_size'],
            'scores': local_features['scores'],
            'keypoints': local_features['keypoints'],
        }

        # Create a mapping for valid landmarks using valid_keypoints_index
        valid_landmarks = {valid_id: landmarks[valid_id] for valid_id in valid_keypoints_index}

        # Batch data transfer to GPU
        pred = {
            **{k + '0': torch.tensor(np.array(v)).unsqueeze(0).to(self.device) for k, v in feats0.items()},
            **{k + '1': torch.tensor(np.array(v)).unsqueeze(0).to(self.device) for k, v in feats1.items()},
        }

        # Perform inference using local feature matcher
        with torch.inference_mode():
            pred = self.local_feature_matcher(pred)

        # Extract matches
        matches = pred['matches0'][0].detach().cpu().short().numpy()

        # Use match_filter to filter valid matches based on valid_landmarks
        pts0, pts1, lms = self.match_filter(matches, feats0, feats1, valid_landmarks)
        
        return [pts0, pts1, lms]

