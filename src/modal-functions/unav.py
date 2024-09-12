from modal import method

from modal_config import app,unav_image


with unav_image.imports():
    import base64
    import io
    from PIL import Image
    
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
    def localize(self,query_image_base64):
        """
            Handle localization request by processing the provided image and returning the pose.
        """
        query_image_data = base64.b64decode(query_image_base64.split(',')[1]) if ',' in query_image_base64 else base64.b64decode(query_image_base64)
        query_image = Image.open(io.BytesIO(query_image_data)).convert('RGB')
        return "Image localized"



    @method()
    def get_navigation_instructions(self):
       pass
   



@app.local_entrypoint()
def main():
    unav_server = UnavServer()
    print(unav_server.localize.remote())
    