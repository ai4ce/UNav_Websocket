from modal import App, Image

app = App(name="unav-server")

unav_image = (
    Image.debian_slim(python_version="3.8")
    .run_commands(
        "apt-get update",
        "apt-get install -y cmake git libceres-dev libsuitesparse-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev",
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
    .pip_install_from_requirements("requirements.txt")
    .workdir('/root')
)
