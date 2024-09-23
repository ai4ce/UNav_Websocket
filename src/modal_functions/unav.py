from modal import method, gpu
from modal_config import app, unav_image, volume


@app.cls(image=unav_image, volumes={"/root/UNav-IO": volume}, gpu=gpu.Any())
class UnavServer:

    @method()
    def localize(self, query_image_base64):
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

        pose = server.handle_localization(frame=query_image, session_id="test")
        print("Pose: ", pose)
        if pose["pose"] is not None:
            pounded_pose = [int(coord) for coord in pose] if pose else None
            print(pounded_pose)
            return pounded_pose

        return pose

    @method()
    def planner(self):
        pass
