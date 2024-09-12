

from modal import method

from modal_config import app,unav_image


@app.cls(image=unav_image)
class UnavServer:
    
    @method
    def localize():
        return

    @method
    def get_options():
        pass

    @method
    def list_places():
        pass

    @method
    def list_buildings():
       pass

    @method
    def list_floors():
        pass

    @method
    def get_destinations_list():
        pass

    @method
    def select_destination():
       pass

    @method
    def planner():
       pass