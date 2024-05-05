import mesa
import mesa_geo as mg
import xyzservices.providers as xyz
from .agents import PersonAgent, RegionAgent
from .model import GeoHousing



class HappyElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Happy agents: {model.happy}"

class MovementElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total movements: {model.movement}"
    
class RenovationElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total removations: {model.renovations}"
    
class DisplacedElement(mesa.visualization.TextElement):
    def render(self, model):
        return f"Total Housholds Displaced: {model.displaced}"


model_params = {
    "rent_discount": mesa.visualization.Slider("% Discount", 0.1, 0.2, 0,3, 0.4),
}


def schelling_draw(agent):
    portrayal = {}
    if isinstance(agent, RegionAgent):
        if agent.housing_quality > 50:
            portrayal["color"] = "Blue"
        elif agent.housing_quality < 50:
            portrayal["color"] = "Red"
        else:
            portrayal["color"] = "Grey"
    elif isinstance(agent, PersonAgent):
        portrayal["radius"] = 1
        portrayal["shape"] = "circle"
        portrayal["color"] = "Red" if agent.income_level < 0.3 else "Blue"
    return portrayal


happy_element = HappyElement()
movement_element = MovementElement()
displaced_element = DisplacedElement()
renovation_element = RenovationElement()

map_element = mg.visualization.MapModule(
    schelling_draw, tiles=xyz.CartoDB.Positron
)
happy_chart = mesa.visualization.ChartModule(
    [
        {"Label": "happy", "Color": "Blue"},
        {
            "Label": "displaced",
            "Color": "Grey",
        },
    ]
)
server = mesa.visualization.ModularServer(
    GeoHousing,
    [map_element, happy_element, movement_element, displaced_element, renovation_element, happy_chart],
    "Housing Quality and Movement",
    model_params,
)
