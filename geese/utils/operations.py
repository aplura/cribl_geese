import json
import sys
import os
import geese.constants.exit_codes as ec
import yaml
from geese.constants.configs import colors

_exclude_object = "exclude"
_include_object = "include"
_universal_object = "universal"
_knowledge_object = "knowledge_objects"


def validate_knowledge(knowledge, filter_set):
    is_valid = True
    if _include_object in filter_set and _knowledge_object in filter_set[_include_object]:
        if knowledge in filter_set[_include_object][_knowledge_object]:
            return True
    if _include_object in filter_set and knowledge in filter_set[_include_object]:
        return True
    if _exclude_object in filter_set and _knowledge_object in filter_set[_exclude_object]:
        if knowledge in filter_set[_exclude_object][_knowledge_object]:
            return False
    return is_valid


def validate(object_type, cribl_object, filter_set):
    # Include directives will always go first, and always win (if id is in both include/exclude)
    is_valid_id = True
    if _include_object in filter_set:
        if _universal_object in filter_set[_include_object]:
            for attribute in filter_set[_include_object][_universal_object]:
                if attribute in cribl_object and cribl_object[attribute] in filter_set[_include_object][_universal_object][attribute]:
                    return True
        if object_type in filter_set[_include_object]:
            for attribute in filter_set[_include_object][object_type]:
                if attribute in cribl_object and cribl_object[attribute] in filter_set[_include_object][object_type][attribute]:
                    return True
        if _knowledge_object in filter_set[_include_object] and object_type in filter_set[_include_object][_knowledge_object]:
            return True
    if _exclude_object in filter_set:
        if _universal_object in filter_set[_exclude_object]:
            for attribute in filter_set[_exclude_object][_universal_object]:
                if attribute in cribl_object and cribl_object[attribute] in filter_set[_exclude_object][_universal_object][attribute]:
                    return False
        if object_type in filter_set[_exclude_object][_knowledge_object]:
            return False
        if object_type in filter_set[_exclude_object]:
            for attribute in filter_set[_exclude_object][object_type]:
                if attribute in cribl_object and cribl_object[attribute] in filter_set[_exclude_object][object_type][attribute]:
                    return False
    return is_valid_id


def load_tuning(file):
    with open(file, "r") as of:
        if file.endswith(".json"):
            file_data = json.load(of)
        else:
            file_data = yaml.safe_load(of)
    return file_data

def validate_args(self, args):
    if args.import_dir:
        if not args.import_file.endswith(".yaml") and args.import_file.endswith(".json"):
            self._display(f"Import file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        if not os.path.exists(args.import_dir):
            self._display(f"Import Directory does not exist: {args.import_dir}", colors.get("error", "red"))
            sys.exit(ec.LOCATION_NOT_FOUND)
    if args.save_file and not args.save_file.endswith(".yaml") and args.save_file.endswith(".json"):
        self._display(f"Save file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
        sys.exit(ec.FILE_NOT_FOUND)
    tuning_object = {}
    if args.tune_ids:
        if not args.tune_ids.endswith(".yaml") and args.tune_ids.endswith(".json"):
            self._display(f"Tuning file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        tuning_object = load_tuning(args.tune_ids)
    self.tuning_object = tuning_object
    knowledge_objects = list(self.objects.keys())
    if args.list_objects:
        self._display(f"Available objects: {', '.join(knowledge_objects)}", colors.get("info", "blue"))
        sys.exit(ec.ALL_IS_WELL)
    return knowledge_objects if args.all_objects else [a for a in args.objects if
                                                     a in knowledge_objects and validate_knowledge(
                                                         a, self.tuning_object)]

def load_configurations(args, ko):
    all_objects = {}
    with open(os.path.join(args.import_dir, f"{args.import_file}"), "r") as of:
        if args.import_file.endswith(".json"):
            file_data = json.load(of)
        else:
            file_data = yaml.safe_load(of)
        for worker_group in file_data:
            all_objects = {k: v for k, v in file_data[worker_group].items() if k in ko}
    return all_objects