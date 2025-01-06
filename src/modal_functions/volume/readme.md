## upload from local to modal 
- refer this file ``` src/modal_functions/local_to_modal.py```
- edit the file path on line number (varibale name local_root_path) to mount the local storage for file transfer 
    - please avoid mounting large space like users/user1, or users/user1/Desktop
    - use as small space as possible like users/user1/Desktop/Projectxyz/folderwithdata
- update the path_list in main function. 
    - each entry as (source , destination)
    - conisder you mounted a space like below
      
      ![image](https://github.com/user-attachments/assets/008aac46-95cb-4bff-81cf-32a425866273)
    - for above structure the source and path are like below
      ![image](https://github.com/user-attachments/assets/2e8dfaee-907e-437f-8111-b55ded11fc78)

