

from modal import method,enter

from modal_config import app,unav_image


@app.cls(image=unav_image)
class UnavServer:
    
    
    def settings(self):
        pass
    
    @method()
    def get_floor_plan_and_destination(self):
        pass
    
    @method()
    def select_destination(self):
       pass
    
    @method()
    def localize(self):
        return "Image localized"



    @method()
    def get_navigation_instructions(self):
       pass
   



@app.local_entrypoint()
def main():
    unav_server = UnavServer()
    print(unav_server.localize.remote())