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
    
    def __init__(self, 
                 unique_id, 
                 model, 
                 geometry, 
                 crs,
                 income_level, 
                 housing_quality_threshold,
                 max_complaint,
                 region_id):
        
        super().__init__(unique_id, 
                         model, 
                         geometry, 
                         crs)
        self.income_level = income_level
        self.housing_quality_threshold = housing_quality_threshold
        self.region_id = region_id
        self.move_count = 0 #tracking household movements 
        self.attempt_rent = 0 
        self.attempt_quality = 0 
        self.attempt_displaced = 0 
        self.is_displaced = False
        self.displacement_count = 0 #housholds tries to move every step, counts the total number of displacement
        self.max_complaint = max_complaint
        self.complaints = 0 #housing quality complaints made by housholds at a region, reset when moved
        self.total_complaints = 0 #accumulative complaints made by a household

    # @property
    # def housing_quality_threshold(self):
    #     """
    #     Calculates a modified housing quality threshold based on the agent's income level,
    #     with a cap and a floor to ensure the threshold remains within realistic bounds.

    #     Returns:
    #         int: The housing quality threshold, adjusted to not exceed 90 if too high,
    #         and not drop below 50 if too low.
    #     """
    #     #deal with threshold distribution at some point !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #     quality = 100 * self.income_level
    #     if quality > 100:
    #         return 90
    #     elif quality < 40:
    #         return 40
    #     else:
    #         return quality

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
        current_region = self.model.space.get_region_by_id(self.region_id) #locates houshold's region(census tract)
        
        if self.is_displaced:
            #if the household is displaced, it tries to find a suitable region
            self.move_to_suitable_region()
            logging.debug(f"Displaced Household{self.unique_id} Trying to Move")
            self.attempt_displaced += 1
            pass

        # Immediate move if rent is too high
        if current_region.rent_price > self.maximum_affordable_rent:
            self.move_to_suitable_region()
            self.attempt_rent += 1
            self.complaints = 0  # Reset the complaint count, if any, once moved; 
            logging.debug(f"Houshold {self.unique_id} Trying to Move - Affordability")
            pass
        else:
            # rent is afforable, checks housing quality 
            if current_region.housing_quality < self.housing_quality_threshold:
                self.complaints += 1  # Increment complaint counts
                self.total_complaints += 1 # Increment total complaints made by houshold
                logging.debug(f"Houshold {self.unique_id} Made A Complaint")
                if self.complaints >= self.max_complaint:# check if there has been more than the max complaints to trigger move
                    self.move_to_suitable_region()
                    self.attempt_quality += 1
                    self.complaints = 0  # Reset the counter after moving
                    logging.debug(f"Houshold {self.unique_id} Trying to Move - Quality")
                    pass
                else:
                    pass
            else:
                #housing quality could be improved before the houshold collects enough complaints to trigger move, complaint counts reset when improved; 
                self.complaints = 0
                logging.debug(f"Houshold {self.unique_id} Found Quality Acceptable - Reset Complaints")
                pass



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
        """
        Generate a list of suitable regions, move to a random region within that list

        """

        suitable_regions = [agent for agent in self.model.space.agents if isinstance(agent, RegionAgent) and
                            agent.housing_quality >= self.housing_quality_threshold and
                            agent.rent_price <= self.maximum_affordable_rent and agent.people_count <= 2]
        # ?? Should I make people_count in a region a parameter? 

        if suitable_regions:
            new_region = random.choice(suitable_regions)
            new_region_id = new_region.unique_id
            self.model.space.remove_person_from_region(self)
            self.model.space.add_person_to_region(self, region_id=new_region_id)
            logging.debug(f"Household {self.unique_id} Moved to {self.region_id}")
            self.move_count += 1 #increased a movement count
            #self.update_happiness()
            #  self.complaints = 0 #reset compaints at this region since moved
        else:
            self.is_displaced = True
            self.displacement_count += 1
            logging.debug(f"Household {self.unique_id} Displaced")
            # self.complaints = 0 #reset compaints at this region since displaced


    # def update_happiness(self):
    #     self.happiness = True

    # def make_complaints(self):
    #     self.complaints += 1
    #     self.total_complaints += 1



class RegionAgent(mg.GeoAgent):
    init_num_people: int
    # num_people : int
    def __init__(self, 
                 unique_id, 
                 model, 
                 geometry, 
                 crs, 
                 has_regulation,
                 rent_discount,
                 init_num_people, 
                 base_decay_constant, 
                 decay_differential,
                 num_month_rent_renovation, 
                 rent_increase_differential):
        

        super().__init__(unique_id, 
                         model, 
                         geometry, 
                         crs 
                         )
        self.init_num_people = init_num_people
        self.num_people = init_num_people
        self.num_month_rent_renovation = num_month_rent_renovation
        self.has_regulation = has_regulation # allow rent regulation to be on or off
        if self.has_regulation:
            self.rent_regulated = random.choice([True, False])
            logging.debug(f"Rent Regulation Activated: Region {self.unique_id} Rent Regulated is {self.rent_regulated}.")
        else:
            self.rent_regulated = random.choice([False, False])
            logging.debug(f"Rent Regulation Not Active: Region {self.unique_id} Rent Regulated is {self.rent_regulated}.")
        self.initial_quality = random.uniform(50, 100)
        logging.debug(f"Region {self.unique_id} Initial Quality is {self.initial_quality}.")
        self.housing_quality = self.initial_quality
        self.rent_discount = rent_discount
        self.renovations = 0
        # Set decay constants based on whether the region is rent-regulated
        if self.rent_regulated:
            self.decay_constant = base_decay_constant + decay_differential #rent regulated housing dacays faster
            self.rent_increase = 1.02
        else:
            self.decay_constant = base_decay_constant
            self.rent_increase = 1.02 + rent_increase_differential
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
        if self.rent_regulated:
            return base_rent * self.rent_discount * self.rent_increase ** self.renovations
        else:
            return base_rent * self.rent_increase ** self.renovations
        
    @property
    def rent_profit(self):
        # Calculate base rent price based on area average median income (AMI)
        base_rent = 0.5 * self.area_ami
        
        #dealing with first time renovations
        if self.renovations == 0:
            if self.rent_regulated: 
                return base_rent * self.rent_discount * (self.rent_increase - 1) #simple 2% gain in rent
            else: 
                return base_rent * (self.rent_increase - 1) 
        
        else: #when renovation is more than 1
            if self.rent_regulated:
                new_rent = base_rent * self.rent_discount * (self.rent_increase ** (self.renovations + 1)) # for each additional renovation, the percentage increase stacks. 
                current_rent = base_rent * self.rent_discount * (self.rent_increase ** self.renovations)  #calculate the current rent price price
            else:
                # For non-regulated areas, calculate the increase without the discount
                new_rent = base_rent * (self.rent_increase ** (self.renovations + 1))
                current_rent = base_rent * (self.rent_increase ** self.renovations)
            
            # Return the difference between the new rent and the previous rent
            return new_rent - current_rent
    
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
        logging.debug(f"Region Rent Regulation is {self.rent_regulated}, Quality is {self.housing_quality},Rent is {self.rent_price}, Region AMI is {self.area_ami}, Own AMI is {self.own_ami}")
        self.decays()
        if self.num_complaints > 5:
            self.enforcement()
        else:
            logging.debug(f"Region {self.unique_id} did not trigger Enforcement with total {self.num_complaints} Complaints.")

        if self.rent_profit * 60  > self.rent_price * self.num_month_rent_renovation: # if 120 steps of rent increases recoups the renovation cost, renovation occurs
            logging.debug(f"Region renovating -  Rent Profit is {self.rent_profit * 69} and Renovation Cost is {self.rent_price * self.num_month_rent_renovation}")
            self.renovate()
        else:
            logging.debug(f"Region {self.unique_id} did not trigger Renovation with Rent Increase {self.rent_profit * 120} less than {self.rent_price * self.num_month_rent_renovation}.")
    
    def decays(self):
        # Calculate exponential decay
        self.housing_quality = self.initial_quality * np.exp(-self.decay_constant * self.steps)
        logging.debug(f"Region {self.unique_id} Decayed from to {self.housing_quality}.")

    def renovate(self):
        # Resets housing quality and increments renovations counter
        if self.rent_regulated:
            self.housing_quality = 90
        else: 
            self.housing_quality = 100
        self.renovations += 1
        logging.debug(f"Region {self.unique_id} is renovated and has {self.people_count} Households.")
        self.steps = 0  # Reset step counter after renovation
        
    def enforcement(self):
        #After collecting enough complaints, enforecement kicks in, reset the housing quality to an acceptable number
        if self.rent_regulated:
            self.housing_quality = 50
        else:
            self.housing_quality = 60 
        logging.debug(f"Region {self.unique_id} is enforced and has {self.people_count} Households.")
        self.steps = 0 
        
    def get_neighbors(self, distance):
        # Find neighboring regions within a certain distance
        return self.model.space.get_neighbors(self, distance, include_agents=False)
    
    def add_person(self, person):
        self.num_people += 1

    def remove_person(self, person):
        self.num_people -= 1
