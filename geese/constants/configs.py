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
    "directory": os.path.join(root_folder, "import"),
    "file": "import_result.yaml"
}
export_cmd = {
    "directory": os.path.join(root_folder, "export"),
    "file": "export.yaml"
}
simulate_cmd = {
    "directory": os.path.join(root_folder, "simulation"),
    "file": "simulate_results.yaml"
}
validate_cmd = {
    "directory": os.path.join(root_folder, "validation"),
    "file": "validate_results.yaml"
}
tuning = {
    "file": None
}
