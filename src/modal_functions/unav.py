from modal import method, gpu
from typing import Optional, Dict

from modal_config import app, unav_image, volume


@app.cls(image=unav_image, volumes={"/root/UNav-IO": volume}, gpu=gpu.Any())
class UnavServer:

    @method()
    def get_destinations_list(self):
        from server_manager import Server
        from modules.config.settings import load_config

        config = load_config("config.yaml")

        server = Server(logger=None, config=config)

        response = server.get_destinations_list(building="LightHouse", floor="6_floor")
        return response

    @method()
    def select_user_destination(self, destination_id: str = "07993"):
        from server_manager import Server
        from modules.config.settings import load_config
        import logging

        logger = logging.getLogger("server_logger")

        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        config = load_config("config.yaml")

        server = Server(logger=logger, config=config)
        print("Server Initialized")
        response = server.select_destination(
            session_id="test_session_id",
            place="New_York_City",
            building="LightHouse",
            floor="6_floor",
            destination_id=destination_id,
        )

        return response

    @method()
    def localize(
        self, query_image_base64: str, session_id: str = "test_session_id"
    ) -> Dict[str, Optional[str]]:
        import base64
        import io
        from PIL import Image
        from server_manager import Server
        from modules.config.settings import load_config

        config = load_config("config.yaml")

        server = Server(logger=None, config=config)

        """
            Handle localization request by processing the provided image and returning the pose.
        """

        query_image_data = (
            base64.b64decode(query_image_base64.split(",")[1])
            if "," in query_image_base64
            else base64.b64decode(query_image_base64)
        )
        query_image = Image.open(io.BytesIO(query_image_data)).convert("RGB")

        pose = server.handle_localization(frame=query_image, session_id=session_id)
        print("Pose: ", pose)
        if pose["pose"] is not None:
            pounded_pose = [int(coord) for coord in pose] if pose else None
            print(pounded_pose)
            return pounded_pose

        return pose

    @method()
    def planner(self):
        pass
