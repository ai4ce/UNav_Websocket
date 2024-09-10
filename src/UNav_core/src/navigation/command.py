import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

def actions(current_pose,path_list,scale):
    xc, yc, an = current_pose
    action_list = []
    for p in path_list:
        xn,yn =p
        distance = np.linalg.norm([xn - xc, yn - yc])
        rot = np.arctan2(xn - xc, yn - yc)/ np.pi * 180+180
        rot_ang = (an - rot) % 360
        rot_clock = (round(rot_ang.squeeze().tolist() / 30)) % 12
        if rot_clock < 1:
            rot_clock += 12
        action_list.append([rot_clock, distance*scale])
        xc, yc ,an= xn, yn,rot

    return action_list

def get_direction(rot_clock):
    if rot_clock>=10.5 or rot_clock<1.5:
        direction = "go straight"
    elif 1.5<=rot_clock<4.5:
        direction = "turn right"
    elif 4.5<=rot_clock<7.5:
        direction = "turn around"
    else:
        direction = "turn left"
    return direction

def clean(rot_clock):
    if rot_clock % 3 <= 1 or rot_clock % 3 >= 2:
        return True
    else:
        return False

def command_debug(action_list):
    message = ''
    for i, ac in enumerate(action_list):
        rot_clock, distance, is_interwaypoint = ac
        if is_interwaypoint:
            message += f"please take the elevator or stairs to your destination floor "
            # break
        direction = get_direction(rot_clock)   #go straight, right, left
        # distance = round(distance*3.28,1)
        distance = int(distance*3.28)
        message += f"please {direction} and walk {distance} feet along {int(rot_clock)} o'clock direction. "
        # message += 'Please walk %.1f meters along %d clock' % (
        #     distance, int(rot_clock))
        
        if i < len(action_list) - 1:
            message += '. Then '
        else:
            message += '. And you will arrive the destination.\n'
    return message

def command_alert(action_list):
    message = ''
    rot_clock,next_distance, is_interwaypoint =action_list[0]  #define actionlist
        # return message
    direction = get_direction(rot_clock)    #get direction
    next_station='your destination' if len(action_list)==1 else '' #arrive at destination
    if next_station=='your destination' and next_distance<2:        
        message='You have arrived your destination'
    else:                                               
        # next_distance = round(next_distance*3.28,1)                 #not arrived at destination yet    
        next_distance = int(next_distance*3.28)                                              
        message += f"{direction} to {int(rot_clock)} o'clock, and walk {next_distance} feet. "
        # message += 'Alert!!!!!!! %s to %d clock, and walk %d steps ' % (
        #     direction, int(rot_clock), int(next_distance/0.55))
        if next_station=='':
            rot_clock,next_distance,is_interwaypoint=action_list[1]
            direction = get_direction(rot_clock)
            next_station='your destination' if len(action_list)==2 else ''
            # message += f" Then {direction} to {int(rot_clock)} o'clock, and walk {int(next_distance*3.28)} feet. "
            message += f" Then {direction}. "
            # message += 'And then %s to %d clock, and walk %d steps ' % (
            #     direction, int(rot_clock), int(next_distance/0.55))
            # if next_distance<5:
            #     if next_station=='your destination':
            #         message +=' to arrive at '+next_station
            #     else:
            #         rot_clock,next_distance=action_list[2]
            #         direction = get_direction(rot_clock)
                
            #     # message += f"head to your {direction} at {int(rot_clock)} o'clock direction"
            #         # message += ', and then %s to %d clock' % (
            #         #     direction, int(rot_clock))
            # else:
            #     if next_station=='your destination':
            #         message +=' to arrive at '+next_station
            #     else:
            #         message +=next_station
        else:
            message +=' to approach '+next_station
    # if is_interwaypoint:
    #     message += f"please get out the elevator and relocalize yourself "
    #     return message
    if len(action_list) > 1 :
        rot_clock_1,next_distance_1,is_interwaypoint_1=action_list[1]
        if is_interwaypoint_1:
            message += f"please take the elevator or stairs to your destination floor "
    return message

def command_normal(action_list):
    message = ''
    
    rot_clock,next_distance,is_interwaypoint=action_list[0]
    
    # return message
    direction = get_direction(rot_clock)
    next_station='your destination' if len(action_list)==1 else ''
    message += f"{direction} at {int(rot_clock)} o'clock direction, and walk {int(next_distance*3.28)} feet"
    # message += '%s to %d clock, and walk %d steps' % (
    #     direction, int(rot_clock), int(next_distance/0.55))
    if next_station=='':
        message += next_station
    else:
        message +=' to approach '+ next_station

    # if is_interwaypoint:
    #     message += f"please get out the elevator and relocalize yourself "
    #     return message
    if len(action_list) > 1 :
        rot_clock_1,next_distance_1,is_interwaypoint_1=action_list[1]
        if is_interwaypoint_1:
            message += f"please take the elevator or stairs to your destination floor "
    return message


def command_count(parent,action_list,length):
    result_message = ''
    rot_clock,next_distance, is_interwaypoint=action_list[0]
    direction = get_direction(rot_clock)
    
    if not parent.halfway: #for counting halfway only once: the first time reaching this area
        percentage = int(length/parent.base_len*100)
        if percentage>=40 and percentage<=60:
            parent.halfway = True
            lenFeetLeft = int((parent.base_len-length)*3.28)
            # result_message = 'you have walked {lenFeet} feet, halfway there for next intruction \n'
            result_message = f'{lenFeetLeft} feet left for next intruction \n'
        elif percentage>=75 and percentage<=85:
            parent.eighty_way = True
            # remain = round((parent.base_len-length)*3.28,1)
            remain = int((parent.base_len-length)*3.28)
            result_message = f'you are almost there, {remain} feet remain \n'
    else:
        if length<2:
            if len(action_list)>1:
                result_message=f"{direction} at {int(action_list[1][0])} o'clock direction "
            else:
                result_message="You have arrived at your destination"
    
    # if is_interwaypoint:
    #     result_message += f"please get out the elevator and relocalize yourself "
    #     return result_message
    if len(action_list) > 1 :
        rot_clock_1,next_distance_1,is_interwaypoint_1=action_list[1]
        if is_interwaypoint_1:
            result_message += f"please take the elevator or stairs to your destination floor "
    
    return result_message
    