import yaml

def read_config(file="config.yml"):
    data = {} 
    with open(file, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"\n Config file config.yml could not be found in the config directory\n")
    return data