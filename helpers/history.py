import os.path

import yaml


# keep track of the datetime a listing was published
def history_save(history):
    with open("history.yaml", 'w') as file:
        yaml.dump(history, file)


# reload saved status from last program run
def history_load():
    if not os.path.exists("history.yaml"):
        return {}
    with open("history.yaml") as file:
        return yaml.full_load(file)
