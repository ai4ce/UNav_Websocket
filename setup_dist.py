import subprocess
from pathlib import Path

import modal


image  = (
    modal.Image.debian_slim(python_version="3.8")
    .run_commands(
         "apt-get update",
        "apt-get install -y build-essential python3 python3-pip git cmake libeigen3-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev libsuitesparse-dev pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "apt-get remove -y libeigen3-dev",  # Remove the existing version of Eigen3
    )
    .run_commands(
        "apt-get install -y  cmake libsuitesparse-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev"
    )
   .run_commands(
       "apt-get install -y libceres-dev"
   )
   .run_commands(
       "git clone https://gitlab.com/libeigen/eigen.git eigen"
   )
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
   .run_commands("ls")
    .run_commands(
        "git clone https://github.com/cvg/implicit_dist.git implicit_dist",
        )
    .workdir("/implicit_dist")
    .run_commands(
        "ls",
        "python3 -m venv .venv",
        ". .venv/bin/activate",
        "pip install ."
    )
    # .run_commands(
    #     "git clone https://github.com/KarypisLab/GKlib.git GKlib",
    #     "cd GKlib",
    #     "ls",
    #     "make config",
    #     "make",
    #     "cd .."
    # )
    
    


)

app = modal.App(name="setup-dist", image=image)


@app.function()
def run():
    print("hello world")