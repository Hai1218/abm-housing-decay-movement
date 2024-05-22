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
             "mean_quality": "mean_quality",
             "mean_complaints": "mean_complaints",
             "mean_displacement": "mean_displacement",
             "mean_housing_quality": "mean_housing_quality",
             "mean_rent_price": "mean_rent_price",
             "hh_low_quality":"hh_low_quality",
             "hh_rent_regulation": "hh_rent_regulation",
             "movement": "movement",
             "attempt": "attempt",
             "movement_li": "movement_li",
             "attempt_li": "attempt_li",
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
    def mean_quality(self):
        quality = 0
        quality_li = 0
        household_count = 0
        household_count_li = 0
        
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                region_quality = self.space.get_region_by_id(agent.region_id).housing_quality
                if agent.income_level <= 0.5:
                    household_count_li += 1
                    quality_li += region_quality
                else:
                    household_count += 1
                    quality += region_quality
        
        # Calculate mean qualities, checking for division by zero
        mean_quality = quality / household_count if household_count > 0 else 0
        mean_quality_li = quality_li / household_count_li if household_count_li > 0 else 0
        
        return (mean_quality, mean_quality_li)

    @property
    def mean_complaints(self):
        complaints = 0
        complaints_li = 0
        household_count = 0
        household_count_li = 0
        
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                if agent.income_level <= 0.5:
                    household_count_li += 1
                    complaints_li += agent.complaints
                else:
                    household_count += 1
                    complaints += agent.complaints

        mean_complaint = complaints / household_count if household_count > 0 else 0
        mean_complaint_li = complaints_li / household_count_li if household_count_li > 0 else 0

        return (mean_complaint, mean_complaint_li)
        
    @property
    def mean_displacement(self):
        displacements = 0
        displacements_li = 0
        household_count = 0
        household_count_li = 0
        
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                if agent.income_level <= 0.5:
                    household_count_li += 1
                    if agent.is_displaced:
                        displacements_li += 1
                else:
                    household_count += 1
                    if agent.is_displaced:
                        displacements += 1

        mean_displacements = displacements / household_count if household_count > 0 else 0
        mean_displacements_li = displacements_li / household_count_li if household_count_li > 0 else 0
        
        return (mean_displacements, mean_displacements_li)
    
    @property
    def mean_housing_quality(self):
        regulated_quality_sum = 0
        non_regulated_quality_sum = 0
        regulated_count = 0
        non_regulated_count = 0

        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                if agent.rent_regulated:
                    regulated_quality_sum += agent.housing_quality
                    regulated_count += 1
                else:
                    non_regulated_quality_sum += agent.housing_quality
                    non_regulated_count += 1

        mean_quality = regulated_quality_sum / regulated_count if regulated_count > 0 else 0
        mean_quality_NR = non_regulated_quality_sum / non_regulated_count if non_regulated_count > 0 else 0

        return (mean_quality, mean_quality_NR)
    
    @property
    def mean_rent_price(self):
        regulated_rent_sum = 0
        non_regulated_rent_sum = 0
        regulated_count = 0
        non_regulated_count = 0

        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                if agent.rent_regulated:
                    regulated_rent_sum += agent.rent_price
                    regulated_count += 1
                else:
                    non_regulated_rent_sum += agent.rent_price
                    non_regulated_count += 1

        mean_rent = regulated_rent_sum / regulated_count if regulated_count > 0 else 0
        mean_rent_NR = non_regulated_rent_sum / non_regulated_count if non_regulated_count > 0 else 0

        return (mean_rent, mean_rent_NR)

    @property
    def hh_low_quality(self):
        '''
        households in low quality housing 
        '''
        household_count = 0
        household_count_li = 0 
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent) and agent.housing_quality < 50:
                households = agent.model.space.get_agents_within_region(agent)
                for household in households:
                    if household.income_level <= 0.5:
                        household_count_li += 1
                    else:
                        household_count += 1
        return (household_count, household_count_li)
    
    @property
    def hh_rent_regulation(self):
        '''
        households in rent regulated housing
        '''
        household_count = 0
        household_count_NR = 0
        for agent in self.space.agents:
            if isinstance(agent, RegionAgent):
                if agent.rent_regulated:
                    household_count += agent.num_people
                else:
                    household_count_NR += agent.num_people
        return (household_count, household_count_NR)
        
    # @property
    # def mean_regulated_housing_quality(self):
    #     housing_quality = 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, RegionAgent) and agent.rent_regulated:
    #             housing_quality += agent.housing_quality
    #     return housing_quality
    
    # @property
    # def mean_non_regulated_housing_quality(self):
    #     housing_quality = 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, RegionAgent) and not agent.rent_regulated:
    #             housing_quality += agent.housing_quality
    #     return housing_quality
    
    @property
    def movement(self):
        num_movement = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                num_movement += agent.move_count
        return num_movement
    

    @property
    def attempt(self):
        attempt_rent = 0 
        attempt_quality = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent):
                attempt_rent += agent.attempt_rent
                attempt_quality += agent.attempt_quality
        return (attempt_rent, attempt_quality)
    
    
    @property
    def movement_li(self):
        num_movement = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent) and agent.income_level <= 0.5:
                num_movement += agent.move_count
        return num_movement
    

    @property
    def attempt_li(self):
        attempt_rent = 0 
        attempt_quality = 0
        for agent in self.space.agents:
            if isinstance(agent, PersonAgent) and agent.income_level <= 0.5:
                attempt_rent += agent.attempt_rent
                attempt_quality += agent.attempt_quality
        return (attempt_rent, attempt_quality)
    
    

    # @property
    # def renovations(self):
    #     num_renovations = 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, RegionAgent):
    #             num_renovations += agent.renovations
    #     return num_renovations

    # @property
    # def displacement(self):
    #     num_displacement= 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, PersonAgent):
    #             num_displacement += agent.displacement_count
    #     return num_displacement
    
    # @property
    # def displaced(self):
    #     num_displaced= 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, PersonAgent):
    #             if agent.is_displaced:
    #                 num_displaced += 1
    #     return num_displaced
    
    # @property
    # def low_income_displaced(self):
    #     num_displaced= 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, PersonAgent) and agent.income_level <= 0.3:
    #             if agent.is_displaced:
    #                 num_displaced += 1
    #     return num_displaced

    # @property
    # def complaints(self):
    #     num_complaints= 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, RegionAgent):
    #             num_complaints += agent.num_complaints
    #     return num_complaints
    
    # @property
    # def low_income_complaints(self):
    #     num_complaints= 0
    #     for agent in self.space.agents:
    #         if isinstance(agent, RegionAgent):
    #             num_complaints += agent.low_income_num_complaints
    #     return int(num_complaints)
    
       

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

