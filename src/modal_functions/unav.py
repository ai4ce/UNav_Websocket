from modal import method, gpu, build, enter

from modal_config import app, unav_image, volume
from logger_utils import setup_logger


@app.cls(
    image=unav_image,
    volumes={"/root/UNav-IO": volume},
    gpu=gpu.Any(),
    enable_memory_snapshot=True,
    concurrency_limit=3,
    allow_concurrent_inputs=3,
)
class UnavServer:
    
    @build()
    @enter()
    def load_server(self):
        from server_manager import Server
        from modules.config.settings import load_config

        config = load_config("config.yaml")

        self.server = Server(logger=setup_logger(), config=config)

    @method()
    def get_destinations_list(self):

        response = self.server.get_destinations_list(
            building="LightHouse", floor="6_floor"
        )
        return response

    @method()
    def planner(
        self,
        session_id: str = "",
        destination_id: str = "",
        building: str = "",
        floor: str = "",
        place: str = "",
        base_64_image: str = None,
    ):

        import json
        import base64
        import io
        from PIL import Image

        """
            Handle localization request by processing the provided image and returning the pose.
        """

        query_image_data = (
            base64.b64decode(base_64_image.split(",")[1])
            if "," in base_64_image
            else base64.b64decode(base_64_image)
        )
        query_image = Image.open(io.BytesIO(query_image_data)).convert("RGB")

        print("Query Image Converted from base64 to PIL Image")

        response = self.server.select_destination(
            session_id=session_id,
            place=place,
            building=building,
            floor=floor,
            destination_id=destination_id,
        )
        if response == None:
            print("Desintation Set to id: " + "07993")
        else:
            print(response)

        pose = self.server.handle_localization(frame=query_image, session_id=session_id)

        print("Pose: ", pose)

        trajectory = self.server.handle_navigation(session_id)

        return json.dumps({"trajectory": trajectory})
