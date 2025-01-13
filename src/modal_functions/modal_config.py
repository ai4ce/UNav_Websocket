from modal import App, Image, Mount, NetworkFileSystem, Volume
from pathlib import Path

volume = Volume.from_name("NewVisiondata")

MODEL_URL = "https://download.pytorch.org/models/vgg16-397923af.pth"
LIGHTGLUE_URL = "https://github.com/cvg/LightGlue/releases/download/v0.1_arxiv/superpoint_lightglue.pth"

# Get the current file's directory
current_dir = Path(__file__).resolve().parent

# Construct the path to the src directory
local_dir = current_dir / ".."


def download_torch_hub_weights():
    import torch
    model_weights = torch.hub.load_state_dict_from_url(MODEL_URL, progress=True)
    torch.save(model_weights, "vgg16_weights.pth")

    lightglue_weights = torch.hub.load_state_dict_from_url(LIGHTGLUE_URL, progress=True)
    torch.save(lightglue_weights,"superpoint_lightglue_v0-1_arxiv-pth")


app = App(
    name="unav-server",
    mounts=[
        Mount.from_local_dir(local_dir.resolve(), remote_path="/root"),
        Mount.from_local_file(
            "modal_functions/config.yaml", remote_path="/root/config.yaml"
        ),
    ],
)

unav_image = (
    Image.debian_slim(python_version="3.8")
    .run_commands(
        "apt-get update",
        "apt-get install -y cmake git libgl1-mesa-glx libceres-dev libsuitesparse-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev",
    )
    .run_commands("git clone https://gitlab.com/libeigen/eigen.git eigen")
    .workdir("/eigen")
    .run_commands(
        "git checkout 3.4",
        "mkdir build",
    )
    .workdir("/eigen/build")
    .run_commands(
        "cmake ..",
        "make",
        "make install",
    )
    .workdir("/")
    .run_commands(
        "git clone https://github.com/cvg/implicit_dist.git implicit_dist",
    )
    .workdir("/implicit_dist")
    .run_commands(
        "ls",
        "python3 -m venv .venv",
        ". .venv/bin/activate",
        "pip install .",
        "pip freeze",
    )
    .pip_install_from_requirements("modal_functions/modal_requirements.txt")
    .workdir("/root")
    .run_function(download_torch_hub_weights)
)
