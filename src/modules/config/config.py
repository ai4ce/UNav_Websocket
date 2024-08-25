import yaml

def load_config(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)
