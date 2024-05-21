import mesa
import mesa_geo as mg
import xyzservices.providers as xyz
from .agents import PersonAgent, RegionAgent
from .model import GeoHousing


class MovementElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total movements: {model.movement}"
    
class RenovationElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total renovations: {model.renovations}"
    
class DisplacedElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Housholds Displaced: {model.displaced}"
    
class LowIncomeDisplacedElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Low-Income Housholds Displaced: {model.low_income_displaced}"

class LowIncomeMovementElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Low-Income Housholds movements: {model.low_income_movement}"
    
class ComplaintsElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Housholds complaints: {model.complaints}"
    
class LowIncomeComplaintsElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Low-Income Housholds complaints: {model.low_income_complaints}"

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
            portrayal["color"] = "Red" if agent.income_level < 0.5 else "Blue"
    return portrayal


movement_element = MovementElement()
displaced_element = DisplacedElement()
renovation_element = RenovationElement()
low_income_displaced_element = LowIncomeDisplacedElement()
low_income_movement_element = LowIncomeMovementElement()
complaints_element = ComplaintsElement()
low_income_complaints_element = LowIncomeComplaintsElement()

map_element = mg.visualization.MapModule(
    housing_draw, tiles=xyz.CartoDB.Positron
)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "movement", "Color": "Blue"},
        {"Label": "displaced","Color": "Grey"},
       
    ]
)
server = mesa.visualization.ModularServer(
    GeoHousing,
    [map_element, movement_element, low_income_movement_element, 
     displaced_element, low_income_displaced_element, 
     renovation_element, 
     complaints_element, low_income_complaints_element, 
     chart],

    "Housing Quality and Movement",
    model_params,
)
