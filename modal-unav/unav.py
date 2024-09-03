import io
import base64
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from modal import Image, Mount, Stub, asgi_app, build, enter, method, gpu

model_repo_id = "llava-hf/llava-v1.6-mistral-7b-hf"
MODEL_DIR = "/model"
MODEL_NAME = model_repo_id

import os


# def download_model_to_image(model_dir, model_name):
#     os.makedirs(model_dir, exist_ok=True)

#     snapshot_download(
#         model_name,
#         local_dir=model_dir,
#         ignore_patterns=["*.pt", "*.bin"],  # Using safetensors
#     )
#     move_cache()


image = (
    Image.debian_slim()
    .pip_install(
        "unav==0.1.40",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    # .run_function(
    #     download_model_to_image,
    #     timeout=60 * 20,
    #     kwargs={"model_dir": MODEL_DIR, "model_name": MODEL_NAME},
    # )
    .apt_install("fonts-freefont-ttf")
)

stub = Stub("unav-demo")
with image.imports():
    from unav import load_data, localization, trajectory, actions

GPU_CONFIG = gpu.A100(count=1)


@stub.cls(
    gpu=GPU_CONFIG,
    image=image,
    cpu=2,
)
class ImageDescription:
    @build()
    def download_model(self):
        # Assuming model and processor can be directly loaded without downloading
        pass

    @method()
    def describe(self):
        return 1  # Always return 1


web_app = FastAPI()


@web_app.post("/")
async def describe(request: Request):
    return "Sup"


@stub.function()
@asgi_app()
def fastapi_app():
    return web_app
