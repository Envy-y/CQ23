import random
import math
import comms
from object_types import ObjectTypes
import json
import heapq
class Game:
    """
    Stores all information about the game and manages the communication cycle.
    Available attributes after initialization will be:
    - tank_id: your tank id
    - objects: a dict of all objects on the map like {object-id: object-dict}.
    - width: the width of the map as a floating point number.
    - height: the height of the map as a floating point number.
    - current_turn_message: a copy of the message received this turn. It will be updated everytime `read_next_turn_data`
        is called and will be available to be used in `respond_to_turn` if needed.
    """
    def __init__(self):
        tank_id_message: dict = comms.read_message()
        self.tank_id = tank_id_message["message"]["your-tank-id"]
        self.enemy_id = tank_id_message["message"]["enemy-tank-id"]
        self.start_pos = [0,0]

        self.current_turn_message = None

        # We will store all game objects here
        self.objects = {}

        next_init_message = comms.read_message()
        while next_init_message != comms.END_INIT_SIGNAL:
            # At this stage, there won't be any "events" in the message. So we only care about the object_info.
            object_info: dict = next_init_message["message"]["updated_objects"]

            # Store them in the objects dict
            self.objects.update(object_info)

            # Read the next message
            next_init_message = comms.read_message()

        # We are outside the loop, which means we must've received the END_INIT signal

        # Let's figure out the map size based on the given boundaries

        # Read all the objects and find the boundary objects
        boundaries = []
        for game_object in self.objects.values():
            if game_object["type"] == ObjectTypes.BOUNDARY.value:
                boundaries.append(game_object)

        # The biggest X and the biggest Y among all Xs and Ys of boundaries must be the top right corner of the map.

        # Let's find them. This might seem complicated, but you will learn about its details in the tech workshop.
        biggest_x, biggest_y = [
            max([max(map(lambda single_position: single_position[i], boundary["position"])) for boundary in boundaries])
            for i in range(2)
        ]

        self.width = biggest_x
        self.height = biggest_y
        

    def read_next_turn_data(self):
        """
        It's our turn! Read what the game has sent us and update the game info.
        :returns True if the game continues, False if the end game signal is received and the bot should be terminated
        """
        # Read and save the message
        self.current_turn_message = comms.read_message()

        if self.current_turn_message == comms.END_SIGNAL:
            return False

        # Delete the objects that have been deleted
        # NOTE: You might want to do some additional logic here. For example check if a powerup you were moving towards
        # is already deleted, etc.
        for deleted_object_id in self.current_turn_message["message"]["deleted_objects"]:
            try:
                del self.objects[deleted_object_id]
            except KeyError:
                pass

        # Update your records of the new and updated objects in the game
        # NOTE: you might want to do some additional logic here. For example check if a new bullet has been shot or a
        # new powerup is now spawned, etc.
        self.objects.update(self.current_turn_message["message"]["updated_objects"])

        return True
    
    def check_bullet(self,player_x, player_y, bullet_x, bullet_y, bullet_velocity_x, bullet_velocity_y):        
        #distance formula to get distance between player and bullet
        distance = math.sqrt((player_x - bullet_x)**2 + (player_y - bullet_y)**2)
        #get new distance with orig bullet + orig velocity
        new_distance = math.sqrt((player_x - (bullet_x + bullet_velocity_x))**2 + (player_y - (bullet_y + bullet_velocity_y))**2)
        #if the new distance is greater than the old distance, the bullet is moving away from us
        if new_distance > distance:
            return False
        else:
            return True

        

    def get_distance(self, position1, position2):
        x1, y1 = position1
        x2, y2 = position2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def get_dodge_direction(self, bullets,my_pos):
        total_threat_direction = 0
        total_threat_weight = 0

        for bullet in bullets:
            bullet_position = bullet['position']
            bullet_velocity_x, bullet_velocity_y = bullet['velocity']

            distance = self.get_distance(my_pos, bullet_position)
            threat_weight = 1 / distance

            bullet_direction = math.degrees(math.atan2(bullet_velocity_y, bullet_velocity_x)) % 360

            total_threat_direction += bullet_direction * threat_weight
            total_threat_weight += threat_weight

        if total_threat_weight > 0:
            average_threat_direction = total_threat_direction / total_threat_weight
            dodge_direction = (average_threat_direction + 90) % 360
            dodge_direction = random.choice([dodge_direction, dodge_direction + 90])
            return dodge_direction
        else:
            return None


    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """
        # TODO: 
        # 1. BORDER CHECKING (THIS SHOULD HAVE THE HIGHEST PRIORITY)
        # 2. UNSTUCKING (IF YOU ARE STUCK, YOU SHOULD GET UNSTUCKED)
        # 3. POWERUP CHECKING (IF THERE IS A POWERUP IN YOUR RANGE, YOU SHOULD GO AND GET IT)
        # 4. WALLS LOGIC (DO NOT SHOOT INTO A REBOUNDABLE WALL)

        post_message_queue = []
        my_pos = self.objects[self.tank_id]["position"]
        enemy_pos = self.objects[self.enemy_id]["position"]
        #DEFAULT ACTION - MOVE TOWARDS CENTER
        heapq.heappush(post_message_queue,(4,{"path":[self.width/2,self.height/2]}))
        
        #use trig to determine angle to shoot at
        angle = math.degrees(math.atan2(enemy_pos[1] - my_pos[1], enemy_pos[0] - my_pos[0]))
    ##################################################################################################
    # UNSTUCKING SECTION
    ##################################################################################################
        #if stuck, move to the center
        if math.sqrt((my_pos[0] - self.start_pos[0])**2 + (my_pos[1] - self.start_pos[1])**2) < 10:
            heapq.heappush(post_message_queue,(2,{"path":[self.width/2,self.height/2]}))
        self.start_pos = my_pos
            
        
    ##################################################################################################   
    # DODGE BULLET SECTION     
    ##################################################################################################
        pos = None
        temp = 5000
        projectiles = []
        # check if any bullets are coming towards us
        for obj in self.objects.values():
            if obj["type"] == 2:
                #move away if any of the x-y values are within 150 units of our position
                if abs(obj["position"][0] - my_pos[0]) < 150 and abs(obj["position"][1] - my_pos[1]) < 150:
                    # calculate if the bullet will hit me, and add to queue
                    if self.check_bullet(my_pos[0],
                                        my_pos[1],
                                        obj["position"][0],
                                        obj["position"][1], 
                                        obj["velocity"][0],
                                        obj["velocity"][1]
                                        ):
                            
                        projectiles.append(obj)
            if obj["type"] == 7:
                powerup_pos = obj["position"]
                distance = self.get_distance(my_pos, powerup_pos)
                if distance < temp:
                    temp = distance
                    pos = powerup_pos
            if obj["type"] == 6:
                border_pos = obj["position"]
                if abs(my_pos[0] - obj["position"][0][0]) < 80 or abs(my_pos[1] - obj["position"][0][1]) < 80 \
                or abs(my_pos[0] - obj["position"][2][0]) < 80 or abs(my_pos[1] - obj["position"][2][1]) < 80:
                   heapq.heappush(post_message_queue,(0,{"path":[self.width/2,self.height/2]}))
                   break






        dodge_direction = self.get_dodge_direction(projectiles,my_pos)

        if pos:
            #compute if this position is outside border_pos
            # border_pos = [TOP LEFT,BOTTOM LEFT,BOTTOM RIGHT,TOP RIGHT]
            if pos[0] < border_pos[0][0] or pos[0] > border_pos[3][0] or pos[1] < border_pos[1][1] or pos[1] > border_pos[3][1]:
                pass
            else:
                heapq.heappush(post_message_queue,(2,{"path":[pos[0],pos[1]]}))
        if dodge_direction:      
            heapq.heappush(post_message_queue,(1,{"move": dodge_direction + random.randint(-45,45)}))
        else:
            pass
        
    ##################################################################################################
    # NO HOMO SECTION
    ##################################################################################################
        dist = self.get_distance(my_pos,enemy_pos)
        if dist < 200:
            heapq.heappush(post_message_queue,(3,{"move": angle + 180}))

        
        priority, action = heapq.heappop(post_message_queue)
        action.update({"shoot": angle})
        try:       
            comms.post_message(action)
        except Exception as e:
            pass
    
    