import time
from copy import deepcopy
from geese.knowledge import Outputs, Pipelines, Certificates, Secrets, Keys, AuthConfig, Routes, Inputs
from geese.knowledge import CollectorJobs, GlobalVariables, Parsers, Regexes, GrokFiles, Schemas
from geese.knowledge import AppScopeConfigs, DatabaseConnections, EventBreakerRules, FleetMappings, Groups
from geese.knowledge import Mappings, Notifications, NotificationTargets, ParquetSchemas, Lookups, Packs
from geese.knowledge import Authentication, Versioning, SrchRegexes, SrchGrok, SrchUsageGroups, SrchDatasetProviders
from geese.knowledge import SrchDatasets, SrchSearches, SrchMacros, SrchParsers, SrchDashboards, SrchDashboardCategories
from geese.utils.operations import validate_knowledge, validate
from geese.KennyLoggins import KennyLoggins
import os
import sys
import yaml
import logging as logger
from termcolor import colored
import geese.constants.exit_codes as ec
from deepmerge import always_merger
import urllib3
from geese.constants.configs import colors

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def display(message, color="blue"):
    print(colored(f"{message}", colors.get(color, "blue")))


class Goose(object):
    objects = {}
    validate_spec = {"get": {}, "post": {}}
    spec_file = None

    def __init__(self, cmd, args, **kwargs):
        kl = KennyLoggins()
        self._cwd = os.getcwd()
        self._args = args
        self._cmd = cmd
        self._edir = os.path.dirname(__file__)
        default_log_level = logger.getLevelName(args.log_level)
        self._logger = kl.get_logger(file_name="duck_duck_goose",
                                     root_folder=self._cwd,
                                     log_level=default_log_level)
        # Set the logger to propagate errors to console.
        self._logger.propagate = args.propagate or False
        with open(self._get_asset_location(["constants", "base_config.yaml"]), "r") as f:
            self.base_config = yaml.safe_load(f)
        self.sources = []
        self.destination = deepcopy(self.base_config["destination"])
        self.tuning_object = {}
        if args.config:
            try:
                with open(args.config, "r") as f:
                    yaml_config = yaml.safe_load(f)
                    if "source" in yaml_config and yaml_config["source"] and len(yaml_config["source"]) > 0:
                        [self.sources.append(y) for y in
                         [self._create_source(x, i) for i, x in enumerate(yaml_config["source"])] if y is not None]
                    if "destination" in yaml_config and yaml_config["destination"] and len(
                            yaml_config["destination"]) > 0:
                        always_merger.merge(self.destination, yaml_config["destination"])
                        self.destination["orig_url"] = self.destination["url"]
                        self.destination["url"] = f'{self.destination["url"]}/api/v1'
                        if self.destination["enabled"]:
                            self.destination["token"] = self._get_source_token(self.destination)
                        else:
                            self.destination = None
                    else:
                        self.destination = None
            except Exception as e:
                self._display_error("File Not Found", e, ec.FILE_NOT_FOUND)
        self._execute = args.handler
        self._log_level = default_log_level
        self.use_namespace = args.use_namespace if len(self.sources) > 1 and hasattr(args, 'use_namespace') else False
        for ds in [Groups, Pipelines, Outputs, Inputs, CollectorJobs, GlobalVariables, Mappings, Parsers, Regexes,
                   GrokFiles, Schemas, ParquetSchemas, DatabaseConnections, Notifications,
                   NotificationTargets, AppScopeConfigs, AuthConfig, FleetMappings, EventBreakerRules, Routes,
                   Lookups, Packs, Secrets, Keys, Certificates, SrchDatasets, SrchSearches, SrchMacros, SrchParsers,
                   SrchDashboards, SrchDashboardCategories, SrchGrok, SrchRegexes, SrchUsageGroups,
                   SrchDatasetProviders]:
            self.objects[ds.obj_type] = ds

    @staticmethod
    def _log_line(**kwargs):
        lines = []
        for k, v in kwargs.items():
            lines.append(f"{k}=\"{v}\"")
        return " ".join(lines)

    def _get_source_token(self, source):
        try:
            auth_obj = Authentication(source, self._args, self._logger,
                                      display=self._display)
            src_cribl_auth_token = None
            if source["is_cloud"] is False:
                # call on-prem leader API for auth token
                self._logger.debug("Artificial Sleep of 1 second.")
                time.sleep(1)
                src_cribl_auth_token, response = auth_obj.api_get_auth_data()
                if src_cribl_auth_token is None:
                    raise Exception(f"Unable to retrieve on-prem token. {source['orig_url']} API response: {response}")
            else:
                # get access token by passing client ID and secret to https://login.cribl.cloud/oauth/token
                client_id = source.get("client_id", "")
                client_secret = source.get("client_secret", "")
                if len(client_id) == 0 or len(client_secret) == 0:
                    raise Exception(
                        "Cribl.cloud client id and/or secret found in configuration, but value is empty. Ensure"
                        f" the values are present.\nServer Config:\n\t{source}")
                else:
                    src_cribl_auth_token, response = auth_obj.get_cloud_access_token()
                    if src_cribl_auth_token is None:
                        raise Exception(
                            f"Unable to retrieve access token from cribl.cloud instance {source['orig_url']}. Response: {response}")
            return src_cribl_auth_token
        except Exception as e:
            self._display_error("Error getting Auth Token", e)
            return ""

    def _create_source(self, source, idx):
        src = deepcopy(self.base_config["source"])
        always_merger.merge(src, source)
        if src["enabled"]:
            src["orig_url"] = src["url"]
            src["url"] = f'{src["url"]}/api/v1'
            src["token"] = self._get_source_token(src)
            src["namespace"] = src["namespace"] if "namespace" in src else f"source_{idx}"
            self._logger.debug("action=_create_source %s" % " ".join([f"{k}=\"{v}\"" for k, v in src.items()]))
            return src
        else:
            self._logger.debug("action=_create_source %s" % " ".join([f"{k}=\"{v}\"" for k, v in src.items()]))
            return None

    def _get_asset_location(self, path=None):
        if path is None:
            path = []
        return os.path.join(self._edir, *path)

    def _display(self, message, color=None, **kwargs):
        print(colored(f"{message}", color, **kwargs))
        self._logger.info(f"action=display_message message=\"{message}\"")

    def _display_error(self, msg, err, exit_code=False):
        emsg, fname, fnum, etype = self.get_exception_info(err)
        erre = [
            f'{msg}',
            f'\t{emsg}: ({etype})',
            f'\t{fname}:{fnum}'
        ]
        t_msg = '\n'.join(erre)
        print(colored(f'{t_msg}', colors.get("error", "red")))
        self._logger.error(" ".join(erre))
        if exit_code:
            sys.exit(exit_code)

    @staticmethod
    def get_exception_info(err):
        """
        The get_exception_info function is a helper function that returns the following information about an exception:
            - The error message
            - The file name where the exception occurred
            - The line number in the file where the exception occurred
            - The type of error

        :param self: Represent the instance of the class
        :param err: Get the error message
        :return: A tuple of the error message, file name, line number and exception type
        :doc-author: Trelent
        """
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        # Message, FileName, Line Number, Exception Type
        return f'{err}', fname, exc_tb.tb_lineno, f"{type(err)}"

    def execute(self):
        try:
            self._execute(self, self._args)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            msgs = [
                "Uncaught Exception",
                f"File: {fname}",
                f"Line: {exc_tb.tb_lineno}",
                f"{e}"
            ]
            self._display('\n\t'.join(msgs), colors["error"])
            sys.exit(ec.INVALID_COMMAND_PARAMETERS)

    def get(self, knowledge=None, restrict_sources=None):
        try:
            valid_source = [s["namespace"] for s in self.sources]
            if restrict_sources:
                valid_source = f"{restrict_sources}".split(",")
                self._display(f"Restricting Sources to: {', '.join(valid_source)}", colors.get("warning", "yellow"))
            if knowledge is None:
                knowledge = []
            self._logger.debug(f"action=get_knowledge valid_sources={','.join(valid_source)}")
            ret_objs = {}
            for s in self.sources:
                if s["namespace"] not in valid_source:
                    self._display(f"Ignoring Source: {s['namespace']}", colors.get("error", "red"))
                else:
                    ret_objs[s["namespace"]] = self._get_source(knowledge, s)
            return ret_objs
        except Exception as e:
            self._display_error(f"Get Error: {knowledge}", e)

    def _get_source(self, knowledge, source):
        kos = {}
        self._display(f"Gathering Knowledge Objects: {source.get('namespace')}", colors.get("info", "blue"))
        if "worker_groups" in source:
            for group in source["worker_groups"]:
                self._display(f"\tWorker Group: {group}", colors.get("info", "blue"))
                kos[group] = {x: self._get(x, source, group=group) for x in knowledge if
                              x in self.objects and validate_knowledge(x, self.tuning_object)}
        if "fleets" in source:
            for fleet in source["fleets"]:
                self._display(f"\tFleet: {fleet}", colors.get("info", "blue"))
                if fleet in kos:
                    fleet = f"fleet-{fleet}"
                kos[fleet] = {x: self._get(x, source, group=fleet) for x in knowledge if
                              x in self.objects and validate_knowledge(x, self.tuning_object)}
        if "worker_groups" not in source and "fleets" not in source:
            kos["default"] = {x: self._get(x, source) for x in knowledge if
                              x in self.objects and validate_knowledge(x, self.tuning_object)}
        return kos

    @staticmethod
    def _empty(*args, **kwargs):
        return []

    def _perform_operation(self, cls, operation, leader, group=None, fleet=None, item=None):
        obj_type = "base"
        try:
            conf_obj = cls(leader, self._args, self._logger, group=group, fleet=fleet,
                           display=self._display, validate_spec=self.validate_spec, spec_file=self.spec_file)
            obj_type = conf_obj.get_ot()
            self._display(f"\t\tPerforming Operation: '{operation}' on '{obj_type}'", colors.get("info", "blue"))
            if operation == "export":
                return conf_obj.export()
            elif operation == "import":
                return conf_obj.update(item)
            elif operation == "simulate":
                return conf_obj.simulate(item)
            elif operation == "validate":
                return conf_obj.validate(item)
            else:
                self._display(f"Unhandled Item: {operation} for '{obj_type}'", colors.get("warning"))
                return {}
        except Exception as e:
            self._display_error(f"Error while Executing {operation} on {obj_type}", e)

    def _get(self, func, source, group=None, fleet=None):
        try:
            data = []
            if func in list(self.objects.keys()):
                self._display(f"Getting Source: {source['url']} ({func}) [{group}]", colors["info"])
                [data.append(g) for g in self._perform_operation(self.objects[func], "export", source,
                                                                 group=group, fleet=fleet) if
                 validate(func, g, self.tuning_object)]
                self._display(f"\tFound {len(data)} items in group [{group}]", colors["info"])
            return data
        except Exception as e:
            self._display_error(f"_get Error: {e}", e)
            return []

    def _process_items(self, ns, item):
        if self._args.use_namespace:
            item["id"] = f"{ns}-{item['id']}"
        return item

    def simulate(self, items):
        try:
            if self.destination is None:
                raise Exception("Destination Leader to simulate is not defined")
            results = {}
            conflict_ids = {}
            for func in [i for i in items if i in list(self.objects.keys())]:
                self._display(
                    f"Simulating Import: '{func}' configurations",
                    colors["info"])
                if func not in results:
                    results[func] = {"items": []}
                if func not in conflict_ids:
                    conflict_ids[func] = []
                func_ids = []
                for individual in items[func]:
                    self._logger.debug(self._log_line(action="simulating_object",
                                                      type=func,
                                                      individual=individual,
                                                      is_string=isinstance(individual, str)))
                    individual_item = items[func][individual] if isinstance(individual, str) else individual
                    myID = individual_item["id"] if "id" in individual_item else "UnKnown ID Param"
                    if myID in func_ids and myID not in conflict_ids[func]:
                        conflict_ids[func].append(myID)
                        if "conflicts" not in results[func]:
                            results[func]["conflicts"] = []
                        results[func]["conflicts"].append(myID)
                    else:
                        func_ids.append(myID)
                    self._display(f"\tSimulating: {myID}", colors["info"])
                    import_result = self._perform_operation(self.objects[func], "simulate", self.destination,
                                                            item=individual_item)
                    if "action" in import_result:
                        self._display(f"\tAction: {import_result['action']}", colors["info"])
                    results[func]["items"].append(
                        import_result if import_result is not None else {"status": "error", "result": import_result})
            return True, {k: results[k] for k in results if len(results[k]) > 0}
        except Exception as e:
            self._display_error("Simulate Error", e)
            return False, {}

    def validate(self, items):
        try:
            # Removed leader config, we don't care. We will use the API SPEC
            results = {}
            conflict_ids = {}
            if self._args.use_namespace:
                for ns in items:
                    self._display(f"Validating Namespace: {ns}", colors.get("info", "blue"))
                    if ns not in list(results.keys()):
                        self._dbg(action="validating_namespace",
                                  groups=f"{list(items[ns].keys())}",)
                        results[ns] = self._validate_group(items=items[ns], conflict_ids=conflict_ids)
            else:
                results = self._validate_group(items=items, conflict_ids=conflict_ids)
            return True, {k: results[k] for k in results if len(results[k]) > 0}
        except Exception as e:
            self._display_error("Validate Error", e)
            return False, {}

    def _validate_group(self, items=None, conflict_ids=None):
        results = {}
        if items is None:
            items = {}
        if conflict_ids is None:
            conflict_ids = {}
        for group in items:
            self._display(f"Validating Group: {group}", colors.get("info", "blue"))
            if group not in results:
                results[group] = {}
            if group not in conflict_ids:
                conflict_ids[group] = {}
            for func in items[group]:
                if len(items[group][func]) < 1:
                    self._dbg(action="validating_group", result="continuing", length=len(items[group][func]), group=group)
                    continue
                self._dbg(action="validating_group", type=f"{func}", group=group)
                if func in list(self.objects.keys()):
                    self._display(
                        f"\tValidating Import: '{func}' configurations",
                        colors["info"])
                else:
                    self._display(
                        f"\tNOT Validating Import: '{group}' configurations",
                        colors["info"])
                    continue
                if func not in results[group]:
                    results[group][func] = {"items": []}
                if func not in conflict_ids:
                    conflict_ids[group][func] = []
                func_ids = []
                for individual in items[group][func]:
                    self._logger.debug(self._log_line(action="validating_object",
                                                      type=func,
                                                      group=group,
                                                      individual=individual,
                                                      is_string=isinstance(individual, str)))
                    individual_item = items[group][func][individual] if isinstance(individual, str) else individual
                    myID = individual_item["id"] if "id" in individual_item else "UnKnown ID Param"
                    if myID in func_ids and myID not in conflict_ids[group][func]:
                        conflict_ids[group][func].append(myID)
                        if "conflicts" not in results[func]:
                            results[group][func]["conflicts"] = []
                        results[group][func]["conflicts"].append(myID)
                    else:
                        func_ids.append(myID)
                    self._display(f"\tValidating: {myID}", colors["info"])
                    import_result = self._perform_operation(self.objects[func], "validate", self.destination,
                                                            item=individual_item)
                    results[group][func]["items"].append(
                        import_result if import_result is not None else {"status": "error", "result": import_result})
        return results

    def _load_prop_value(self, ref):
        loaded_spec = self.validate_spec
        spec_list = ref.split("/")
        for sl in spec_list:
            if sl == "#":
                continue
            loaded_spec = loaded_spec.get(sl, {})
        return loaded_spec

    def _load_property(self, s_prop):
        if isinstance(s_prop, dict):
            for props in s_prop:
                if isinstance(s_prop[props], dict):
                    v = self._load_property(s_prop[props])
                    s_prop[props] = v
                elif "$ref" == props:
                    v = self._load_prop_value(s_prop["$ref"])
                    s_prop = self._load_property(v)
                elif isinstance(s_prop[props], list):
                    s_prop[props] = [self._load_property(x) for x in s_prop[props]]
                elif isinstance(s_prop[props], str):
                    pass
                else:
                    pass
                    # print(f"IS SUB: {type(s_prop[props])}")
        elif isinstance(s_prop, str):
            pass
        else:
            pass
            # print(f"IS: {type(s_prop)}")
        return s_prop

    def load_spec(self, spec):
        self.validate_spec = spec
        for path in list(spec.get("paths", {}).keys()):
            s = (spec["paths"]
                 .get(path, {})
                 .get("post", {})
                 .get("requestBody", {})
                 .get("content", {})
                 .get("application/json", {})
                 .get("schema", {}))
            sp = self._load_property(s)
            if len(list(sp.keys())) > 0:
                self.validate_spec["paths"][path]["post"]["requestBody"]["content"]["application/json"]["schema"] = sp

    # pipelines, inputs, outputs, packs, lookups, globals, parsers, regexes, event_breakers, schemas, parquet_scheemas,
    # database, appscore, auth_config, notifications, mappings, fleet mappings, routes
    def perform_import(self, items):
        try:
            if self.destination is None:
                raise Exception("Destination Leader to import is not defined")
            destination_groups_only = ["routes", "outputs", "inputs", "pipelines"]
            updated_worker_groups = []
            results = {}
            self._dbg(action="importing_items", item_keys=list(items.keys()), destination=self.destination)

            for func in [i for i in items if i in list(self.objects.keys())]:
                if len(items[func]) > 0:
                    self._display(
                        f"Importing {func} configurations: {len(items[func])}",
                    colors["info"])
                if func not in results:
                    results[func] = []
                for individual in items[func]:
                    individual_item = items[func][individual] if isinstance(individual, str) else individual
                    item_id = individual_item["id"] if "id" in individual_item else "UnKnown ID Param"
                    self._display(f"\tImporting {func}; {item_id}", colors["info"])
                    import_result = {}
                    if "worker_groups" in individual_item:
                        self._display(f"\t\tItem Groups: {individual_item['worker_groups']}", colors["info"])
                        import_result["groups"] = {}
                        item_groups = [group for group in individual_item["worker_groups"]]
                        del individual_item["worker_groups"]
                        for group in item_groups:
                            self._display(f"\t Importing item '{item_id}' to group '{group}'")
                            import_result["groups"][group] = self._perform_operation(self.objects[func],
                                                                                     "import",
                                                                                     self.destination,
                                                                                     group=group,
                                                                                     item=individual_item)
                            updated_worker_groups.append(group)
                    elif "conf" in individual_item and "worker_groups" in individual_item["conf"]:
                        self._display(f'\t\tConf Item Groups: {individual_item["conf"]["worker_groups"]}', colors["info"])
                        import_result["groups"] = {}
                        for group in individual_item["conf"]["worker_groups"]:
                            self._display(f"\t Importing {item_id} to group {group}")
                            import_result["groups"][group] = self._perform_operation(self.objects[func],
                                                                                     "import",
                                                                                     self.destination,
                                                                                     group=group,
                                                                                     item=individual_item)
                            updated_worker_groups.append(group)
                    elif func not in destination_groups_only:
                        self._display("\t\tNo Groups", colors["info"])
                        import_result = self._perform_operation(self.objects[func], "import", self.destination,
                                                                item=individual_item)
                        updated_worker_groups.append("default")
                    else:
                        self._display(f"\t\tUnknown Issue with item '{item_id}': {','.join(list(individual_item.keys()))}", colors.get("warning", "yellow"))
                    if "worker_groups" in self.destination:
                        self._display(f'\t\tDestination Groups: {self.destination["worker_groups"]}', colors["info"])
                        import_result["dest_groups"] = {}
                        for group in self.destination["worker_groups"]:
                            self._display(f"\t Importing {item_id} to group {group}")
                            import_result["dest_groups"][group] = self._perform_operation(self.objects[func],
                                                                                          "import",
                                                                                          self.destination,
                                                                                          group=group,
                                                                                          item=individual_item)
                            updated_worker_groups.append(group)
                    results[func].append(import_result)
            self._dbg(action="checking for commit", item_keys=list(items.keys()))
            if self._args.commit:
                for wg in list(set(updated_worker_groups)):
                    vers = Versioning(self.destination, self._args, self._logger, group=wg, fleet=None,
                                      display=self._display)
                    deploy = self._args.deploy and not vers.is_free()
                    if self._args.deploy and vers.is_free():
                        self._display("\tCannot Deploy on Free version, will just commit.", colors.get("warning", "yellow"))
                    self._dbg(action="committing_version", group=wg, leader=self.destination["url"])
                    results["commit"] = vers.commit(self._args.commit_message, deploy=deploy, effective=True)
            return True, {k: results[k] for k in results if len(results[k]) > 0}
        except Exception as e:
            self._display_error("Import Error", e)
            return False, {}

    def _inform(self, **kwargs):
        st = f"{kwargs}"
        if type(kwargs) is dict:
            st = self._log_line(**kwargs)
        self._logger.info(st)

    def _dbg(self, **kwargs):
        st = f"{kwargs}"
        if type(kwargs) is dict:
            st = self._log_line(**kwargs)
        self._logger.debug(st)

    def _warn(self, **kwargs):
        st = f"{kwargs}"
        if type(kwargs) is dict:
            st = self._log_line(**kwargs)
        self._logger.warn(st)

    def _fatal(self, **kwargs):
        st = f"{kwargs}"
        if type(kwargs) is dict:
            st = self._log_line(**kwargs)
        self._logger.fatal(st)