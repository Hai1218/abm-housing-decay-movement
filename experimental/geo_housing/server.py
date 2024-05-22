import mesa
import mesa_geo as mg
import xyzservices.providers as xyz
from .agents import PersonAgent, RegionAgent
from .model import GeoHousing


class MovementElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total movements: {model.movement}"
    
class QualityElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Mean Quality Experienced (Regular/Low Income Households): {model.mean_quality}"
    
class ComplaintsElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Mean Housing Complaints (Regular/Low Income Households): {model.mean_complaints}"
    
class DisplacementElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Mean Displacement (Regular/Low Income Households): {model.mean_displacement}"
    
class HHLowQualityElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Number of Households in Low Quality Housing (Regular/Low Income) {model.hh_low_quality}"
    
class HousingQualityElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Mean Housing Quality (Regulated/Non-Regulated): {model.mean_housing_quality}"

class RentElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Mean Rent (Regulated/Non-Regulated) {model.mean_rent_price}"


model_params = {
    "has_regulation": mesa.visualization.Checkbox("Rent Regulation Enabled", True),
    "rent_discount": mesa.visualization.Slider("Rent Regulation Rent Discount", 
                                               0.5, 0, 0.9, 0.1,
                                               description="The discount in rent for regulated housing.",
                                               ),
    "decay_differential": mesa.visualization.Slider("Rent Regulated Decay Differential", 
                                                    0.05, 0, 0.2, 0.01,
                                                    description="The rate at which regulated housing decays faster.",
                                                    ),
    "base_decay_constant": mesa.visualization.Slider("Housing Decay Constant", 
                                                     0.15, 0, 0.5, 0.01,
                                                     description="The base rate at which all housing decays.",
                                                     ),
    "num_month_rent_renovation": mesa.visualization.Slider("Number of Months of Rent as Renovation Cost", 
                                                      2, 1, 10, 1,
                                                      description="The cost for a housing renovation.",
                                                      ),
    "rent_increase_differential": mesa.visualization.Slider("Rent Increase Differential", 
                                                            0.08, 0, 0.2, 0.01,
                                                            description="The rent premium non-regulated housing can charge after renovations.",
                                                            ),
    "init_num_people": mesa.visualization.Slider("Initial Number of Households", 
                                                 2, 1, 10, 1,
                                                 description="More than 2 housholds could slow down your computer.",
                                                 ),
    "max_complaint": mesa.visualization.Slider("Number of complaints made before Household moves", 
                                               5, 1, 10, 1,),
}


def housing_draw(agent):
    portrayal = {}
    if isinstance(agent, RegionAgent):
        if agent.housing_quality > 70:
            portrayal["color"] = "Green"
            if agent.rent_regulated:
                portrayal['opacity'] = 0.1
            else:
                portrayal["opacity"] = 1.0
        elif agent.housing_quality < 30:
            portrayal["color"] = "Red"
            if agent.rent_regulated:
                portrayal['opacity'] = 0.1
            else:
                portrayal["opacity"] = 1.0
        else:
            portrayal["color"] = "Blue"
            if agent.rent_regulated:
                portrayal['opacity'] = 0.1
            else:
                portrayal["opacity"] = 1.0

    elif isinstance(agent, PersonAgent):
        portrayal["radius"] = 1
        portrayal["shape"] = "circle"
        if agent.is_displaced:
            portrayal["color"] = "Grey"
        else:
            portrayal["color"] = "Red" if agent.income_level < 0.8 else "Blue"
    return portrayal


movement_element = MovementElement()
quality_element = QualityElement()
complaints_element = ComplaintsElement()
displacement_element = DisplacementElement()
hh_low_quality_element = HHLowQualityElement()
housing_quality_element = HousingQualityElement()
rent_element = RentElement()

map_element = mg.visualization.MapModule(
    housing_draw, tiles=xyz.CartoDB.Positron
)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "movement", "Color": "Blue"},
        {"Label": "mean_quality","Color": "Grey"},
       
    ]
)
server = mesa.visualization.ModularServer(
    GeoHousing,
    [map_element, movement_element, 
     quality_element, complaints_element, 
     displacement_element, hh_low_quality_element, 
     housing_quality_element, rent_element, 
     chart],

    "Housing Quality and Movement",
    model_params,
)
