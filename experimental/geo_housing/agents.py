import random
import numpy as np
import mesa_geo as mg
from shapely.geometry import Point
import logging
logging.basicConfig(level=logging.DEBUG)


class PersonAgent(mg.GeoAgent):
    """
    Represents an individual housing in the simulation with spatial attributes. This agent evaluates its living conditions
    based on income and housing quality, deciding whether to move to a different region if current conditions are not satisfactory.

    Attributes:
        unique_id (int): A unique identifier for the agent.
        model (mesa.Model): The model instance to which this agent belongs.
        geometry (object): The geometric representation of the agent's location.
        crs (object): Coordinate reference system information for the geometry.
        income_level (float): The income level of the agent, affecting its housing quality treshold and maximum afforable rent
        region_id (int): The identifier of the region where the agent is initially located.
    """
    
    def __init__(self, unique_id, model, geometry, crs, income_level, max_complaint, region_id):
        super().__init__(unique_id, model, geometry, crs)
        self.income_level = income_level
        self.region_id = region_id
        self.move_count = 0 #tracking household movements 
        # self.happiness = True #if false, finds a suitable region or be displaced
        self.is_displaced = False
        self.displacement_count = 0 #housholds tries to move every step, counts the total number of displacement
        self.unhappiness_due_to_quality_count = 0 #tracks housholds unhappy steps with acceptable rent but unacceptable housing quality
        self.max_complaint = max_complaint
        self.complaints = 0 #housing quality complaints made by housholds at a region, reset when moved
        self.total_complaints = 0 #accumulative complaints made by a household

    @property
    def housing_quality_threshold(self):
        """
        Calculates a modified housing quality threshold based on the agent's income level,
        with a cap and a floor to ensure the threshold remains within realistic bounds.

        Returns:
            int: The housing quality threshold, adjusted to not exceed 90 if too high,
            and not drop below 50 if too low.
        """
        quality = 100 * self.income_level
        if quality > 100:
            return 90
        elif quality < 50:
            return 50
        else:
            return quality

    @property
    def maximum_affordable_rent(self):
        #50% of income per month for rent is considered highly rent burdened
        return 0.5 * self.income_level
    

    def step(self):
        """
        Executes one simulation step for the agent, evaluating housing conditions.
        The agent first checks if the rent exceeds their affordability threshold, deciding to move immediately if so.
        If the rent is affordable, the agent then checks the housing quality and decides to move if it's below the threshold for a specified number of consecutive steps.
        """
        current_region = self.model.space.get_region_by_id(self.region_id)
        
        if self.is_displaced:
            self.move_to_suitable_region()

        # Immediate move if rent is too high
        if current_region.rent_price > self.maximum_affordable_rent:
            self.move_to_suitable_region()
            #self.unhappiness_due_to_quality_count = 0  # Reset the unhappiness count related to quality
        else:
            # Check housing quality if rent is affordable
            if current_region.housing_quality < self.housing_quality_threshold:
                self.unhappiness_due_to_quality_count += 1  # Increment unhappiness count
                self.make_complaints()  # Make a complaint when housing quality is too low
            else:
                # Reset the unhappiness and complaint count if conditions are satisfactory
                self.unhappiness_due_to_quality_count = 0
                # self.complaints = 0

            # Decide to move if housing quality has been consistently poor
            if self.unhappiness_due_to_quality_count >= self.max_complaint:
                self.move_to_suitable_region()
                self.unhappiness_due_to_quality_count = 0  # Reset the counter after moving


    # def step(self):
    #     """
    #     Executes one simulation step for the agent, evaluating housing conditions and deciding on happiness.
    #     If the rent is too high, the agent immediately becomes unhappy. If the housing quality is below the threshold,
    #     the agent becomes unhappy and considers moving only after staying unhappy for 5 steps.
    #     """
    #     current_region = self.model.space.get_region_by_id(self.region_id)
    #     # Check for high rent
    #     if current_region.rent_price > self.maximum_affordable_rent:
    #         self.happiness = False
    #         # Agent moves immediately if rent is too high
    #         if not self.happiness:
    #             self.move_to_suitable_region()
    #     # Check for low housing quality
    #     else:
    #         if current_region.housing_quality < self.housing_quality_threshold:
    #             if self.happiness:
    #                 # Start the count if the agent was previously happy but now faces low quality
    #                 self.unhappiness_due_to_quality_count = 1
    #                 self.make_complaints() #make a complaint when housing quality too low per step
    #             else:
    #                 # Increment unhappiness count if already unhappy due to quality
    #                 self.unhappiness_due_to_quality_count += 1
    #                 self.make_complaints()  #make a complaint when housing quality too low per step
    #             # Check if the count has reached 5 steps
    #             if self.unhappiness_due_to_quality_count >= self.max_complaint:
    #                 self.happiness = False
    #                 self.move_to_suitable_region()
    #         else:
    #             # Reset happiness and the counter if conditions are met
    #             self.happiness = True
    #             self.unhappiness_due_to_quality_count = 0



    def move_to_suitable_region(self):

        # suitable_regions = [agent for agent in self.model.space.agents if isinstance(agent, RegionAgent) and
        #                     agent.housing_quality >= self.housing_quality_threshold and
        #                     agent.rent_price <= self.maximum_affordable_rent and agent.people_count <= 2]
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
            #self.update_happiness()
            self.complaints = 0 #reset compaints at this region since moved
        else:
            self.is_displaced = True
            self.displacement_count += 1
            logging.debug(f"Agent {self.unique_id} is displaced,  quality threshold:{self.housing_quality_threshold}, income level: {self.income_level}.")
            self.complaints = 0 #reset compaints at this region since displaced


    # def update_happiness(self):
    #     self.happiness = True

    def make_complaints(self):
        self.complaints += 1
        self.total_complaints += 1



class RegionAgent(mg.GeoAgent):
    init_num_people: int
    # num_people : int
    def __init__(self, 
                 unique_id, 
                 model, 
                 geometry, 
                 crs, 
                 rent_discount,
                 init_num_people, 
                 base_decay_constant, 
                 decay_differential):
        

        super().__init__(unique_id, 
                         model, 
                         geometry, 
                         crs 
                         )
        self.init_num_people = init_num_people
        self.num_people = init_num_people
        # self.num_people = self.init_num_people
        self.rent_regulated = random.choice([True, False])
        logging.debug(f"region {self.unique_id} rent regulation is {self.rent_regulated}.")
        self.initial_quality = random.uniform(50, 100)
        logging.debug(f"region {self.unique_id} initial quality is {self.initial_quality}.")
        self.housing_quality = self.initial_quality
        self.rent_discount = rent_discount
        self.renovations = 0
        # Set decay constants based on whether the region is rent-regulated
        if self.rent_regulated:
            self.decay_constant = base_decay_constant + decay_differential
        else:
            self.decay_constant = base_decay_constant 
        self.steps = 0  # Initialize a step counter


    @property
    def area_ami(self):
        neighbors = self.model.space.get_neighbors(self) #get all regional neigbors 
        self_neighbors = [self] + list(neighbors) #including self

        # Calculate the average AMI including neighboring regions
        all_residents = []

        for region in self_neighbors:
            all_residents.extend(region.model.space.get_agents_within_region(region)) #get all housholds in all the regions
        
        if all_residents:
            return np.mean([resident.income_level for resident in all_residents]) #get an area ami for rent price calculation
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
            base_rent = 0.5 * self.area_ami
            return base_rent * self.rent_discount if self.rent_regulated else base_rent   
    
    @property
    def num_complaints(self):
        all_residents = []
        all_residents.extend(self.model.space.get_agents_within_region(self)) #get all housholds residing in its region
        if all_residents:
            return np.sum([resident.complaints for resident in all_residents]) #get total number of complaints within the regions
        return 0

    @property
    def low_income_num_complaints(self):
        all_residents = []
        all_residents.extend(self.model.space.get_agents_within_region(self)) #get all housholds residing in its region
        if all_residents:
            return np.sum([resident.complaints for resident in all_residents if resident.income_level < 0.3]) #get total number of complaints within the regions
        return 0
    
    @property
    def people_count(self):
        """
        Counts the number of residents within the region.
        
        Returns:
            int: The number of residents in this region.
        """
        all_residents = []
        all_residents.extend(self.model.space.get_agents_within_region(self)) #get all housholds residing in its region
        return len(all_residents)  # Return the number of residents in the list


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
        logging.debug(f"Region's rent regulation is {self.rent_regulated}, quality is {self.housing_quality},rent is {self.rent_price} and overall AMI is {self.area_ami}, own AMI is {self.own_ami}")
        self.decays()
        if self.rent_regulated:
            if self.housing_quality < 40 or self.num_complaints > 40:
                self.renovate()
        else:
            if self.housing_quality < 50 or self.num_complaints > 30:
                self.renovate()
    
    def decays(self):
        # Calculate exponential decay
        self.housing_quality = self.initial_quality * np.exp(-self.decay_constant * self.steps)
        logging.debug(f"Region {self.unique_id} is decayed from {self.initial_quality} to {self.housing_quality}.")

    def renovate(self):
        # Resets housing quality and increments renovations counter
        if self.rent_regulated:
            self.housing_quality = 90
        else: 
            self.housing_quality = 60
        self.renovations += 1
        logging.debug(f"Region {self.unique_id} is renovated and has {self.people_count} Households.")
        self.steps = 0  # Reset step counter after renovation
        

    def get_neighbors(self, distance):
        # Find neighboring regions within a certain distance
        return self.model.space.get_neighbors(self, distance, include_agents=False)
    
    def add_person(self, person):
        self.num_people += 1

    def remove_person(self, person):
        self.num_people -= 1
