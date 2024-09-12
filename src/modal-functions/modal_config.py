from modal import App, Image

app = App(name="unav-server")

unav_image = (
    Image.debian_slim(python_version="3.8")
    .run_commands(
        "apt-get update",
        "apt-get install -y pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "pip install --upgrade pip",
    )
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
        "pip install .",
        "pip freeze",
    )
    .workdir('/root')
    .run_commands("ls")
    .pip_install_from_requirements("requirements.txt")
    .pip_install("kornia")
    .pip_install("unav==0.1.40")
    .pip_install("pytorch_lightning")
    .pip_install("gdown"))