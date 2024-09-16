import base64
import os

from modal import method, gpu

from modal_config import app, unav_image, volume


@app.cls(image=unav_image, volumes={"/root/UNav-IO": volume}, gpu=gpu.Any())
class UnavServer:

    @method()
    def localize(self, query_image_base64):
        import base64
        import io
        from PIL import Image
        import numpy as np
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

        # pose = server.handle_localization(np.array(query_image))
        # rounded_pose = [int(coord) for coord in pose] if pose else None

        return "Image localized"



@app.local_entrypoint()
def main():
    unav_server = UnavServer()
    current_directory = os.getcwd()
    full_image_path = os.path.join(current_directory, "modal_functions/misc/sample.png")

    with open(full_image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
    print(unav_server.localize.remote(base64_encoded))