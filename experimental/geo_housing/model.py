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
                 seed=None, 
                 has_regulation = True,
                 rent_discount = 0.5,
                 decay_differential = 0.05,
                 base_decay_constant= 0.15, 
                 num_month_rent_renovation = 4,
                 rent_increase_differential = 0.1,
                 init_num_people = 2,
                 max_complaint = 5
                 ):
        
        super().__init__()
        self.has_regulation = has_regulation
        self.rent_discount = rent_discount
        self.init_num_people = init_num_people
        self.decay_differential = decay_differential
        self.base_dacay_constant = base_decay_constant
        self.max_complaint = max_complaint


        self.random = np.random.default_rng(seed)
        self.schedule = mesa.time.RandomActivation(self)
        self.space = CensusTract()
        self.datacollector = mesa.DataCollector(
            {
             "movement": "movement",
             "li_movement": "low_income_movement",
             "displaced": "displaced",
             "li_displaced": "low_income_displaced",
             "complaints": "complaints",
             "li_complaints":"low_income_complaints",
             "regulated_quality": "regulated_housing_quality",
             "quality": "non_regulated_housing_quality",
             "renovations": "renovations"
             }
        )


        # Set up the grid with patches for every census tract
        ac = mg.AgentCreator(RegionAgent, 
                             model=self, 
                             agent_kwargs = {"has_regulation":has_regulation,
                                             "rent_discount":rent_discount,
                                             "init_num_people":init_num_people,
                                             "base_decay_constant":base_decay_constant,
                                             "decay_differential":decay_differential,
                                             "num_month_rent_renovation": num_month_rent_renovation,
                                             "rent_increase_differential":rent_increase_differential
                             },
                             )
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
                    income_level=self.random.beta(2.5, 3.5) * 2,
                    housing_quality_threshold=self.random.normal(65, 10),
                    region_id=region.unique_id,
                    max_complaint = self.max_complaint
                )
                self.space.add_person_to_region(person, region_id=region.unique_id)
                logging.debug(f"person {person.unique_id} income is {person.income_level}.")
                
                self.schedule.add(person)
            self.schedule.add(region)

        self.datacollector.collect(self)

    @property
    def regulated_housing_quality(self):
        housing_quality = 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent) and agent.rent_regulated:
                housing_quality += agent.housing_quality
        return housing_quality
    
    @property
    def non_regulated_housing_quality(self):
        housing_quality = 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent) and not agent.rent_regulated:
                housing_quality += agent.housing_quality
        return housing_quality
    
    @property
    def movement(self):
        num_movement = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                num_movement += agent.move_count
        return num_movement
    
    @property
    def low_income_movement(self):
        num_movement = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent) and agent.income_level <= 0.3:
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
    
    @property
    def low_income_displaced(self):
        num_displaced= 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent) and agent.income_level <= 0.3:
                if agent.is_displaced:
                    num_displaced += 1
        return num_displaced

    @property
    def complaints(self):
        num_complaints= 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                num_complaints += agent.num_complaints
        return num_complaints
    
    @property
    def low_income_complaints(self):
        num_complaints= 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                num_complaints += agent.low_income_num_complaints
        return int(num_complaints)
    
       

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

