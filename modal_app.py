import modal

# Define the base image
image = (
    modal.Image.debian_slim()
    .pip_install("pip", "setuptools", "wheel")  # Ensure pip is up-to-date
    .apt_install(
        "pkg-config",
        "libhdf5-dev",
        "gcc",
        "libgl1-mesa-glx",
        "libglib2.0-0"
    )  # Install system dependencies
    .run_commands("mkdir /app")  # Create working directory
    
)

# Define the function to run the container
@modal.function(image=image, mounts=[modal.mount(local_dir=".", remote_dir="/app")])
def run_flask_app():
    # Change directory to /app
    import os
    os.chdir("/app")
    
    # Install Python dependencies
    os.system("pip install -r requirements.txt")
    
    # Run the Flask app
    os.system("python -m flask run --host=0.0.0.0")

if __name__ == "__main__":
    with modal.run(run_flask_app):
        pass  # This will start the Flask app in the Modal environment
