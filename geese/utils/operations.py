import json
import yaml

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
