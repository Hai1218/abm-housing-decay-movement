import random
import numpy as np
import mesa_geo as mg
from shapely.geometry import Point
import logging
logging.basicConfig(level=logging.DEBUG)


class PersonAgent(mg.GeoAgent):
    def __init__(self, unique_id, model, geometry, crs, income_level, region_id):
        super().__init__(unique_id, model, geometry, crs)
        self.income_level = income_level
        self.region_id = region_id
        self.move_count = 0
        self.happiness = True
        self.is_displaced = False
        self.displacement_count = 0

    @property
    def housing_quality_threshold(self):
        return 100 * self.income_level

    @property
    def maximum_affordable_rent(self):
        return 0.5 * self.income_level

    def step(self):
        current_region = self.model.space.get_region_by_id(self.region_id)
        if current_region.housing_quality < self.housing_quality_threshold or \
           current_region.rent_price > self.maximum_affordable_rent:
            self.happiness = False
        else:
            self.happiness = True

        if not self.happiness:
            self.move_to_suitable_region()

    def move_to_suitable_region(self):
        logging.debug(f"Agent {self.unique_id} is trying to move, quality threshold:{self.housing_quality_threshold}, income level: {self.maximum_affordable_rent}.")
        max_attempts = 1  # Limit the number of move attempts
        if self.move_count >= max_attempts:
            self.is_displaced = True
            logging.debug(f"Agent {self.unique_id} is displaced, quality threshold:{self.housing_quality_threshold}, income level: {self.maximum_affordable_rent}.")
            return  # Stop trying to move after reaching the max attempts
        
        suitable_regions = [agent for agent in self.model.space.agents if isinstance(agent, RegionAgent) and
                            agent.housing_quality >= self.housing_quality_threshold and
                            agent.rent_price <= self.maximum_affordable_rent]

        if suitable_regions:
            new_region = random.choice(suitable_regions)
            new_region_id = new_region.unique_id
            self.model.space.remove_person_from_region(self)
            self.model.space.add_person_to_region(self, region_id=new_region_id)
            logging.debug(f"Agent {self.unique_id} has moved to {self.region_id}, quality threshold:{self.housing_quality_threshold}, new housing profile: {new_region.housing_quality, new_region.rent_price},income level: {self.maximum_affordable_rent}.")
            self.move_count += 1
            self.update_happiness()
        else:
            self.is_displaced = True
            self.displacement_count += 1
            logging.debug(f"Agent {self.unique_id} is displaced,  quality threshold:{self.housing_quality_threshold}, income level: {self.income_level}.")

    def update_happiness(self):
        self.happiness = True



class RegionAgent(mg.GeoAgent):
    init_num_people: int
    num_people : int
    def __init__(self, 
                 unique_id, 
                 model, 
                 geometry, 
                 crs, 
                 init_num_people=2,
                 rent_discount=0.5, 
                 base_decay_constant=0.15, 
                 decay_differential=0.05):
        

        super().__init__(unique_id, 
                         model, 
                         geometry, 
                         crs 
                         )
        self.init_num_people = init_num_people
        self.num_people = self.init_num_people
        self.rent_regulated = random.choice([True, False])
        logging.debug(f"region {self.unique_id} rent regulation is {self.rent_regulated}.")
        self.initial_quality = random.uniform(20, 100)
        logging.debug(f"region {self.unique_id} initial quality is {self.initial_quality}.")
        self.housing_quality = self.initial_quality
        self.rent_discount = rent_discount
        self.renovations = 0
        # Set decay constants based on whether the region is rent-regulated
        if self.rent_regulated:
            self.decay_constant = base_decay_constant
        else:
            self.decay_constant = base_decay_constant + decay_differential
        self.steps = 0  # Initialize a step counter


    @property
    def average_ami(self):
        neighbors = self.model.space.get_neighbors(self)
        self_neighbors = [self] + list(neighbors)

        # Calculate the average AMI including neighboring regions
        #self_and_neighbors = [self] + list(self.model.space.get_neighbors(self))
        all_residents = []
        #for region in self_and_neighbors:

        for region in self_neighbors:
            all_residents.extend(region.model.space.get_agents_within_region(region))
        
        if all_residents:
            return np.mean([resident.income_level for resident in all_residents])
        return 0
    
    @property
    def own_ami(self):
        all_residents = []
        all_residents.extend(self.model.space.get_agents_within_region(self))
        
        if all_residents:
            return np.mean([resident.income_level for resident in all_residents])
        return 0
    
    @property
    def rent_price(self):
            # Calculate rent price, applying a discount if the region is rent regulated
            base_rent = 0.5 * self.average_ami
            return base_rent * (1 - self.rent_discount) if self.rent_regulated else base_rent   

    def random_point(self):
        min_x, min_y, max_x, max_y = self.geometry.bounds
        while not self.geometry.contains(
            random_point := Point(
                random.uniform(min_x, max_x), random.uniform(min_y, max_y)
            )
        ):
            continue
        return random_point
       
    
    def step(self):
        # Increment step counter
        self.steps += 1
        logging.debug(f"Region's rent regulation is {self.rent_regulated}, quality is {self.housing_quality},rent is {self.rent_price} and overall AMI is {self.average_ami}, own AMI is {self.own_ami}")
        self.decays()
        if self.housing_quality <= 50 and not self.rent_regulated:  # Assuming a threshold for renovation
            self.renovate()
    
    def decays(self):
        # Calculate exponential decay
        self.housing_quality = self.initial_quality * np.exp(-self.decay_constant * self.steps)
        logging.debug(f"Region {self.unique_id} is decayed from {self.initial_quality} to {self.housing_quality}.")


    def renovate(self):
        # Resets housing quality and increments renovations counter
        self.housing_quality = 80
        self.renovations += 1
        logging.debug(f"Region {self.unique_id} is renovated.")
        self.steps = 0  # Reset step counter after renovation

    def get_neighbors(self, distance):
        # Find neighboring regions within a certain distance
        return self.model.space.get_neighbors(self, distance, include_agents=False)
    
    def add_person(self, person):
        self.num_people += 1

    def remove_person(self, person):
        self.num_people -= 1
