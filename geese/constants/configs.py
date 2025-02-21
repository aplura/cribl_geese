import os

global_log_folder = ".logs"
global_log_filename = "geese.log"
colors = {
    "error": "red",
    "warn": "yellow",
    "warning": "yellow",
    "info": "blue",
    "progress": "magenta"
}

root_folder = "cribl"
import_cmd = {
    "resolve_conflict": "update",
    "directory": os.path.join(root_folder),
    "file": "objects.yaml",
    "save_file": "results.yaml"
}
export_cmd = {
    "directory": os.path.join(root_folder),
    "file": "objects.yaml"
}
simulate_cmd = {
    "directory": os.path.join(root_folder),
    "file": "simulate_results.yaml"
}
validate_cmd = {
    "directory": os.path.join(root_folder),
    "file": "validate_results.yaml"
}
tuning = {
    "file": None
}
