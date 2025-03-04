import glob
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
    if "import_dir" in args:
        if not args.import_file.endswith(".yaml") and not args.import_file.endswith(".json"):
            self._display(f"Import file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
            sys.exit(ec.FILE_NOT_FOUND)
        if not os.path.exists(args.import_dir):
            self._display(f"Import Directory does not exist: {args.import_dir}", colors.get("error", "red"))
            sys.exit(ec.LOCATION_NOT_FOUND)
    if "save_file" in args and not args.save_file.endswith(".yaml") and not args.save_file.endswith(".json"):
        self._display(f"Save file: {args.export_file} is not a YAML or JSON file.", colors.get("error"))
        sys.exit(ec.FILE_NOT_FOUND)
    tuning_object = {}
    if args.tune_ids:
        if not args.tune_ids.endswith(".yaml") and not args.tune_ids.endswith(".json"):
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

def load_configurations(self, args, ko):
    all_objects = {}
    base_dir = args.import_dir
    recursive = True
    if args.split:
        glob_path = os.path.join(base_dir, "**", "configs", f"*{args.file}")
    else:
        glob_path = os.path.join(base_dir, "**", "configs", f"{args.import_file}")
    files = glob.glob(glob_path, recursive=recursive)
    self._dbg(action="load_configurations",
              search=glob_path,
              files=files)
    if len(files) == 0:
        self._display(f"No configuration files found in {glob_path} with name {args.import_file}", colors.get("error", "red"))
        sys.exit(ec.FILE_NOT_FOUND)
    for conf_file in files:
        self._display(f"Loading configuration file: {conf_file}", colors.get("info", "blue"))
        with open(conf_file, "r") as of:
            if conf_file.endswith(".json"):
                file_data = json.load(of)
            elif conf_file.endswith(".yaml"):
                file_data = yaml.safe_load(of)
            else:
                self._display(f"Configuration File {conf_file} is not a YAML or JSON file.", colors.get("error", "red"))
                continue
            if args.use_namespace:
                if args.split:
                    root = file_data.get("namespace", "no_namespace")
                    wg = file_data.get("group", "default")
                    k = file_data.get("object_type", "no_object_type")
                    if root not in all_objects:
                        all_objects[root] = {}
                    if wg not in all_objects[root]:
                        all_objects[root][wg] = {}
                    if "data" in file_data and k in ko :
                        all_objects[root][wg][k] = file_data["data"]
                        self._dbg(action="load_configurations",
                                  use_namespace=args.use_namespace,
                                  namespace=root,
                                  group=wg,
                                  object_type=k,
                                  keys=list(all_objects.get(root, {}).get(wg, {}).get(k, {}).keys()))
                else:
                    root = file_data.get("namespace", "no_namespace")
                    if root not in all_objects:
                        all_objects[root] = {}
                    if "data" in file_data:
                        for wg in file_data["data"]:
                            all_objects[root][wg] = {k: v for k, v in file_data["data"][wg].items() if k in ko}
                            self._dbg(action="load_configurations",
                                      use_namespace=args.use_namespace,
                                      namespace=root,
                                      group=wg,
                                      keys=list(all_objects.get(root, {}).get(wg, {}).keys()))
            else:
                if args.split:
                    root = file_data.get("group", "default")
                    k = file_data.get("object_type", "no_object_type")
                    if root not in all_objects:
                        all_objects[root] = {}
                    if k not in all_objects[root]:
                        all_objects[root][k] = {}
                    if "data" in file_data and k in ko:
                        all_objects[root][k] = file_data["data"]
                        self._dbg(action="load_configurations",
                                  use_namespace=args.use_namespace,
                                  group=root,
                                  object_type=k,
                                  keys=list(all_objects.get(root, {}).get(k, {}).keys()))
                else:
                    root = file_data.get("group", "default")
                    if "data" in file_data:
                        all_objects[root] = {k: v for k, v in file_data["data"].items() if k in ko}
                        self._dbg(action="load_configurations",
                                  use_namespace=args.use_namespace,
                                  group=root,
                                  keys=list(all_objects.get(root, {}).keys()))
    self._dbg(action="load_configurations",
              use_namespace=args.use_namespace,
              all_objects_keys=list(all_objects.keys()))
    return all_objects

def _filter_groups(self, all_objects=None):
    if all_objects is None:
        all_objects = {}
    filtered_objects = {}
    for record in all_objects:
        for check_object in all_objects[record]:
            c_object = all_objects[record][check_object] if isinstance(check_object, str) else check_object
            if validate(record, c_object, self.tuning_object):
                if record not in filtered_objects:
                    filtered_objects[record] = {}
                if check_object not in filtered_objects[record]:
                    filtered_objects[record][check_object] = []
                for objs in all_objects[record][check_object]:
                    filtered_objects[record][check_object].append(all_objects[record][check_object][objs])
    return filtered_objects

def filter_groups(self, all_objects=None):
    filtered_objects = {}
    if self._args.use_namespace:
        for ns in all_objects:
            if ns not in list(filtered_objects.keys()):
                self._dbg(action="filtering_namespace",
                          groups=f"{list(all_objects[ns].keys())}", )
                filtered_objects[ns] = _filter_groups(self, all_objects[ns])
    else:
        filtered_objects = _filter_groups(self, all_objects)
    return filtered_objects