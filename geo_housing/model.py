import random
import uuid
import mesa
import mesa_geo as mg
import numpy as np

from .agents import PersonAgent, RegionAgent
from .space import CensusTract
import logging
logging.basicConfig(level=logging.DEBUG)

class GeoHousing(mesa.Model):
    def __init__(self, 
                 rent_discount=0.5, 
                 ):
        super().__init__()

        self.schedule = mesa.time.RandomActivation(self)
        self.space = CensusTract()
        self.datacollector = mesa.DataCollector(
            {"happy": "happy", "movement": "movement"}
        )


        # Set up the grid with patches for every census tract
        ac = mg.AgentCreator(RegionAgent, model=self)
        regions = ac.from_file(
            "data/chicago.geojson", unique_id="community"
        )
        
        self.space.add_regions(regions)
           
        for region in regions:
            for _ in range(region.init_num_people):
                person = PersonAgent(
                    unique_id=uuid.uuid4().int,
                    model=self,
                    crs=self.space.crs,
                    geometry=region.random_point(),
                    income_level=np.random.beta(2.5, 3.5),
                    region_id=region.unique_id,
                )
                self.space.add_person_to_region(person, region_id=region.unique_id)
                logging.debug(f"person {person.unique_id} income is {person.income_level}.")
                
                self.schedule.add(person)
            self.schedule.add(region)

        self.datacollector.collect(self)

    @property
    def unhappy(self):
        num_unhappy = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent) and agent.happiness == False:
                num_unhappy += 1
        return num_unhappy

    @property
    def happy(self):
        return self.space.num_people - self.unhappy
    

    @property
    def movement(self):
        num_movement = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                num_movement += agent.move_count
        return num_movement
    
    @property
    def renovations(self):
        num_renovations = 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                num_renovations += agent.renovations
        return num_renovations

    @property
    def displacement(self):
        num_displacement= 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                num_displacement += agent.displacement_count
        return num_displacement
    
    @property
    def displaced(self):
        num_displaced= 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                if agent.is_displaced:
                    num_displaced += 1
        return num_displaced

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

        if not self.unhappy:
            self.running = False
