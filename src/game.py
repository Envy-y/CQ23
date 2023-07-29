import random
import math
import comms
from object_types import ObjectTypes
import json
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
            return dodge_direction
        else:
            return None


    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """
        # Write your code here... For demonstration, this bot just shoots randomly every turn.
        #check if we have actually moved
        TO_SHOOT = True
        TO_MOVE = [self.width/2, self.height/2]
        my_pos = self.objects[self.tank_id]["position"]
        if my_pos == self.start_pos:
            #move to the center
           TO_MOVE = [self.width/2, self.height/2]
        self.start_pos = my_pos

        enemy_pos = self.objects[self.enemy_id]["position"]
        
        #use trig to determine angle to shoot at
        angle = math.degrees(math.atan2(enemy_pos[1] - my_pos[1], enemy_pos[0] - my_pos[0]))
        
        #check if there is a wall in the way
        #first, construct y=mx+b equation for our position and the path the bullet will take
   
        m = (enemy_pos[1] - my_pos[1])/(enemy_pos[0] - my_pos[0])
        b = my_pos[1] - m*my_pos[0]
        # the maximum value for x is enemy_pos[0] and the minimum is my_pos[0]
        # now check if any of the walls are in the way
        for obj in self.objects.values():
            if obj["type"] == 3:
                #check if its within our domain
                if abs(obj["position"][0]) < abs(enemy_pos[0]) and abs(obj["position"][0]) > abs(my_pos[0]):
                    #use equation to see if it is in the way
                    y_pos = m*obj["position"][0] + b
                    if abs(y_pos - obj["position"][1]) < 20:
                        #TO_SHOOT = False
                        pass
 
               
                        
        '''  
        # check if any bullets are coming towards us
        to_move = [(50,50), (50,-50), (-50,50), (-50,-50)]
        for obj in self.objects.values():
            if obj["type"] == 2:
                #move away if any of the x-y values are within 40 units of our position
                if abs(obj["position"][0] - my_pos[0]) < 40 or abs(obj["position"][1] - my_pos[1]) < 40:
                    #move away from the bullet 
                    move = random.choice(to_move)     
                    TO_MOVE = [self.width/2 + move[0], self.height/2 + move[1]]

        '''   
        projectiles = []
        # check if any bullets are coming towards us
        for obj in self.objects.values():
            if obj["type"] == 2:
                #move away if any of the x-y values are within 450 units of our position
                if abs(obj["position"][0] - my_pos[0]) < 500 or abs(obj["position"][1] - my_pos[1]) < 500:
                    # calculate if the bullet will hit me, and add to queue
               
                    if self.check_bullet(my_pos[0],
                                        my_pos[1],
                                        obj["position"][0],
                                        obj["position"][1], 
                                        obj["velocity"][0],
                                        obj["velocity"][1]
                                        ):
                            
                        projectiles.append(obj)
        dodge_direction = self.get_dodge_direction(projectiles,my_pos)

        if dodge_direction is not None:

            #new_position_x = my_pos[0] + 120 * math.cos(math.radians(dodge_direction))
            #new_position_y = my_pos[1] + 120 * math.sin(math.radians(dodge_direction))
            comms.post_message(
                {
                "move": dodge_direction + random.randint(45,90), "shoot": angle
                }
            )
            return
        else:
            comms.post_message(
                {
                "path": TO_MOVE
                }
            )

                        
                        
        if TO_SHOOT:
            comms.post_message(
            {
            "shoot": angle, "path": TO_MOVE
            }
            )
        else:
            comms.post_message(
            {
            "path": TO_MOVE
            }
            )
     #  {"closing_boundary-1":{"type":6,"position":[[2.5,997.5],[2.5,2.5],[1797.5,2.5],[1797.5,997.5]],"velocity":[[10.0,0.0],[0.0,10.0],[-10.0,0.0],[0.0,-10.0]]}}
     # bound_pos = self.objects["closing_boundary-1"]["position"]