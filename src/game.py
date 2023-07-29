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

    def respond_to_turn(self):
        """
        This is where you should write your bot code to process the data and respond to the game.
        """
        # Write your code here... For demonstration, this bot just shoots randomly every turn.
        #check if we have actually moved
        my_pos = self.objects[self.tank_id]["position"]
        if my_pos == self.start_pos:
            #move to the center
            comms.post_message(
                {
                "path": [self.width/2, self.height/2]
                }
                )
            return
        self.start_pos = my_pos




        enemy_pos = self.objects[self.enemy_id]["position"]
        #use trig to determine angle to shoot at
  
        angle = math.degrees(math.atan2(enemy_pos[1] - my_pos[1], enemy_pos[0] - my_pos[0]))
        

        #calculate position of bullet to see if there is a reboundable wall too close
        bullet_pos = [my_pos[0] + 50*math.cos(math.radians(angle)), my_pos[1] + 50*math.sin(math.radians(angle))]
        for obj in self.objects.values():
            if obj["type"] == 3:
                pass
                


        # check if any bullets are coming towards us
        to_move = [(50,50), (50,-50), (-50,50), (-50,-50)]
        for obj in self.objects.values():
            if obj["type"] == 2:
                #move away if any of the x-y values are within 40 units of our position
                if abs(obj["position"][0] - my_pos[0]) < 40 or abs(obj["position"][1] - my_pos[1]) < 40:
                    #move away from the bullet 
                    move = random.choice(to_move)
                    comms.post_message(
                        {
                        "path": [my_pos[0]+move[0],my_pos[1]+move[1]], "shoot": angle
                        }
                        )
        
        comms.post_message(
            {
            "shoot": angle, "path": enemy_pos
            }
            )
        

        # move away from closing boundary
        for obj in self.objects.values():
            if obj["type"] == 6:
                # check x coord
                if abs(obj["position"][0][0] - my_pos[0]) < 40 or abs(obj["position"][0][1] - my_pos[1]) < 40 \
                    or abs(obj["position"][2][0] - my_pos[0]) < 40 or abs(obj["position"][2][1] - my_pos[1]) < 40:
                    #move to the center
                     comms.post_message(
                         {
                             "path": [self.width/2, self.height/2]
                         }
                     )

        
        # for obj in self.objects.values():
        #     if obj["type"] == 7:

     #  {"closing_boundary-1":{"type":6,"position":[[2.5,997.5],[2.5,2.5],[1797.5,2.5],[1797.5,997.5]],"velocity":[[10.0,0.0],[0.0,10.0],[-10.0,0.0],[0.0,-10.0]]}}
     # bound_pos = self.objects["closing_boundary-1"]["position"]