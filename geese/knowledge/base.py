import os
import sys
import requests
import json

from jsonschema.exceptions import ValidationError
from openapi_schema_validator import validate
from deepdiff import DeepDiff
from termcolor import colored


class BaseKnowledge:
    obj_type = "base"

    def __init__(self, leader, args, logger, **kwargs):
        try:
            if args is None:
                args = {}
            self.colors = {}
            self.tuning = {}
            self.validate_spec = {"get": {}, "post": {}}
            self.api_path = "/system/info"
            self.supports_groups = True
            self.openapi = None
            self.log = logger
            if "display" in kwargs.keys():
                self._display = kwargs["display"]
            if "validate_spec" in kwargs:
                self.validate_spec = kwargs["validate_spec"]
                self.openapi = validate
            if "supports_groups" in kwargs:
                self.supports_groups = kwargs["supports_groups"]
            if "colors" in kwargs.keys():
                self.colors = kwargs["colors"]
            if "tuning" in kwargs.keys():
                self.tuning = kwargs["tuning"]
            self.group = leader["group"] if "group" in leader and len(leader["group"]) > 0 else None
            self.is_fleet = False
            self.leader = leader
            self.endpoint = None
            self.url = leader["url"]
            self.token = leader["token"] if "token" in leader else ''
            self.verify_ssl = leader["verify_ssl"] if "verify_ssl" in leader else True
            self.args = args
            self.headers = {"Content-type": "application/json",
                            "Authorization": "Bearer " + self.token}
            self.payload = None
            self.update_items_200 = ["cribllogs", "criblmetrics input", "already exist"]
        except Exception as e:
            self._display_error("Unhandled INIT BASE Exception", e)

    def to_json(self):
        return dict(self)

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if not attr.startswith("_") and not callable(value):
                yield attr, value

    def supports_groups(self):
        return self.supports_groups

    def _gen_save_dir(self, base_dir, ko_type):
        grp = self.group if self.group else "default"
        dur = os.path.join(base_dir, grp, ko_type)
        if self.args.use_namespace:
            dur = os.path.join(base_dir, self.leader["namespace"], grp, ko_type)
        if not os.path.exists(dur):
            os.makedirs(dur)
        return dur

    def _display_error(self, msg, err, exit_code=False):
        emsg, fname, fnum, etype = self.get_exception_info(err)
        erre = [
            f'{msg}',
            f'\t{emsg}: ({etype})',
            f'\t{fname}:{fnum}'
        ]
        t_msg = '\n'.join(erre)
        print(colored(f'{t_msg}', self.colors.get("error", "red")))
        self.log.error(" ".join(erre))
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

    def _display(self, string, color=None):
        print(string)
        self._log("info", action="display", color=color, string=string)

    def list(self):
        self._log("debug", action="List", message="base_implementation")

    def simulate(self, item=None):
        self._log("debug", action="Simulation", message="base_implementation", item=item)
        return []

    def export(self):
        self._log("debug", action="Export", message="base_implementation")
        return []

    def _load_spec(self, spec_name=None):
        s = None
        if spec_name:
            s = (self.validate_spec.get("paths")
                 .get(spec_name, {})
                 .get("post", {})
                 .get("requestBody", {})
                 .get("content", {})
                 .get("application/json", {})
                 .get("schema", None))
        return s

    def validate(self, item=None, api_path=None):
        if api_path is None:
            api_path = self.api_path
        self._log("debug", action="Validation", message="base_implementation", item=item)
        errors = {"id": api_path, "result": ""}
        if self.openapi and api_path in list(self.validate_spec.get("paths", {}).keys()):
            spec = self._load_spec(spec_name=api_path)
            if spec:
                try:
                    self._log("debug", action="checking_spec", type=api_path, item=item, spec_keys=spec["oneOf"][0]["properties"])
                    self.openapi(item, spec)
                    self._display(f"\t\t{api_path}: valid", self.colors.get("success", "green"))
                    errors["result"] = "success"
                    errors["message"] = f"{api_path}: valid"
                except ValidationError as e:
                    self._display(f"\t\t{api_path}: {e.message}", self.colors.get("error", "red"))
                    errors["result"] = "failure"
                    errors["message"] = f"{api_path}: {e.message}"
            else:
                self._display(f"\t\t{api_path}: invalid schema, or not found", self.colors.get("warning", "yellow"))
        return errors

    def _endpoint_by_id(self, item_id=None):
        return f'{self.endpoint}/{item_id if item_id is not None else ""}'

    def _build_endpoint(self, endpoint):
        return f"{self.url}/{endpoint if endpoint is not None else ''}"

    def get(self, endpoint=None, headers=None, payload=None, stream=False, use_session=False, url=None):
        try:
            url = self._build_endpoint(endpoint) if url is None else url
            self._log("debug", method="get", url=url, headers=headers, payload=payload, stream=stream,
                      use_session=use_session)
            if headers is None:
                headers = self.headers
            if payload is None:
                payload = self.payload
            if payload is not None:
                if use_session is True:
                    return requests.Session().get(url, data=json.dumps(payload),
                                                  params=payload,
                                                  headers=headers, stream=stream,
                                                  verify=self.verify_ssl)
                return requests.get(url, data=json.dumps(payload),
                                    params=payload, headers=headers, stream=stream,
                                    verify=self.verify_ssl)
            else:
                if use_session is True:
                    return requests.Session().get(url, headers=headers, stream=stream, verify=self.verify_ssl)
                else:
                    return requests.get(url, headers=headers, stream=stream, verify=self.verify_ssl)
        except Exception as e:
            raise Exception(
                f"General exception raised while attempting GET {self._build_endpoint(endpoint)}: {e}")

    def post(self, endpoint=None, headers=None, payload=None, stream=False, use_session=False, data=None, url=None):
        try:
            url = self._build_endpoint(endpoint) if url is None else url
            pay_me = json.dumps(payload) if payload is not None else data
            headers = headers if headers is not None else self.headers
            self._log("debug", stage="request", method="post", url=url, headers=headers, payload=pay_me, stream=stream,
                      use_session=use_session)
            response = None
            if use_session is True:
                response = requests.Session().post(url, data=pay_me, headers=headers, verify=self.verify_ssl)
            else:
                response = requests.post(url, data=pay_me, headers=headers, verify=self.verify_ssl)
            self._log("debug", stage="response", response=response.text, status=response.status_code, method="post",
                      url=url, headers=headers, payload=pay_me, stream=stream,
                      use_session=use_session)
            return response
        except Exception as e:
            raise Exception(
                f"General exception raised while attempting POST {self._build_endpoint(endpoint)}: {e}")

    # should be used for file uploads (e.g. lookup files, packs)
    def put(self, endpoint=None, headers=None, payload=None, stream=False, use_session=False, data=None, url=None):
        try:
            pay_me = json.dumps(payload) if payload is not None else data
            url = self._build_endpoint(endpoint) if url is None else url
            headers = headers if headers is not None else self.headers
            self._log("debug", method="put", url=url, headers=headers, payload=pay_me, stream=stream,
                      use_session=use_session)
            if use_session is True:
                return requests.Session().put(url, headers=headers, data=pay_me, verify=self.verify_ssl)
            else:
                return requests.put(url, headers=headers, data=pay_me, verify=self.verify_ssl)
        except Exception as e:
            raise Exception(
                f"General exception raised while attempting PUT {self._build_endpoint(endpoint)}: {e}")

    def patch(self, endpoint=None, headers=None, payload=None, stream=False, use_session=False, data=None, url=None):
        try:
            url = self._build_endpoint(endpoint) if url is None else url
            pay_me = json.dumps(payload) if payload is not None else data
            headers = headers if headers is not None else self.headers
            self._log("debug", method="patch", url=url, headers=headers, payload=pay_me, stream=stream,
                      use_session=use_session)
            if use_session is True:
                return requests.Session().patch(url, data=pay_me, headers=headers, verify=self.verify_ssl)
            else:
                return requests.patch(url, data=pay_me, headers=headers, verify=self.verify_ssl)
        except Exception as e:
            raise Exception(
                f"General exception raised while attempting PATCH {self._build_endpoint(endpoint)}: {e}")

    def delete(self, endpoint=None, headers=None, payload=None, stream=False, use_session=False, url=None):
        try:
            url = self._build_endpoint(endpoint) if url is None else url
            headers = headers if headers is not None else self.headers
            self._log("debug", method="delete", url=url, headers=headers, payload=payload, stream=stream,
                      use_session=use_session)
            if payload is not None:
                if use_session is True:
                    requests.Session().delete(url, headers=headers, verify=self.verify_ssl, data=json.dumps(payload))
                else:
                    return requests.delete(url, headers=headers, verify=self.verify_ssl, data=json.dumps(payload))
            else:
                if use_session is True:
                    return requests.Session().delete(url, headers=headers, verify=self.verify_ssl)
                else:
                    return requests.delete(url, headers=headers, verify=self.verify_ssl)
        except Exception as e:
            raise Exception(
                f"General exception raised while attempting DELETE {self._build_endpoint(endpoint)}: {e}")

    def _update_item(self, action, item, id_field="id", changes=None, update_on_create_failure=True):
        if changes is None:
            changes = {"id": item[id_field] if id_field in item else "Unknown",
                       "previous": {"status": "not_updated", "data": {}},
                       "updated": {"status": "not_updated", "data": {}}}
        try:
            self._log("info", action=action,
                      item_type=self.obj_type,
                      item_id=item[id_field],
                      destination=self.url,
                      group=self.group)
            result = self.export()
            if len(result) > 0:
                for r in result:
                    if r[id_field] == item[id_field]:
                        changes["previous"] = {"status": "exists", "data": r}
            else:
                changes["previous"] = {"status": "error", "result": result}
            result = self.post(self.endpoint, payload=item)
            if result.status_code != 200:
                self._log("info", action=action, item_type=self.obj_type, item_id=item[id_field],
                          destination=self.url, message="Could not Create",
                          conflict_resolution=self.args.conflict_resolve)
                if (any([True if result.text.find(txt) != -1 else False for txt in self.update_items_200])
                        and self.args.conflict_resolve == "update"
                        and update_on_create_failure):
                    result = self.patch(self._endpoint_by_id(item_id=item[id_field]), payload=item)
                    if result.status_code != 200:
                        self._display(f"\t{item[id_field]}: Update failed. {result.text}", self.colors.get("error"))
                        changes["updated"] = {"status": "update_failed", "data": item, "error": result.text}
                    else:
                        self._display(f"\t{item[id_field]}: Update successful.", self.colors.get("success", "green"))
                        changes['updated'] = {"status": "success", "data": item}
                elif result.text.find("should have required property") != -1:
                    msg = result.text
                    try:
                        msg = result.json()["message"]
                        msg = json.loads(msg)
                        t = []
                        for m in msg:
                            t.append(f'{m["keyword"]}:\n\t\t{m["message"]}\n\t\t{m["params"]}\n\t\t{m["schemaPath"]}')
                        msg = "\n\t".join(t)
                    except:
                        msg = result.text
                    self._display(f"\t{item[id_field]}: Create failed. \n\t{msg}", self.colors.get("error", "red"))
                    changes["updated"] = {"status": "create_failed", "data": item, "error": result.text}
                elif self.args.conflict_resolve == "ignore":
                    self._display(f"\t{item[id_field]}: Ignoring conflict/error.", self.colors.get("success", "green"))
                    changes["updated"] = {"status": "ignored", "data": item}
                else:
                    # some other error
                    self._display(f"\t{item['id']}: Error while trying to create. {result.text}",
                                  self.colors.get("error"))
                    changes["updated"] = {"status": "update_failed", "data": item, "error": result}
            else:
                self._display(f"\t{item['id']}: Update succeeded.", self.colors.get("success", "green"))
                changes['updated'] = {"status": "success", "data": item}
                changes["diff"] = json.loads(
                    DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes
        except Exception as e:
            self._display_error("Unhandled Exception", e)
            changes["diff"] = json.loads(
                DeepDiff(changes["previous"]["data"], changes["updated"]["data"]).to_json())
            return changes

    def get_ot(self):
        return self.obj_type

    def _log(self, log_level="info", **kwargs):
        if self.log:
            my_string = self._build_string(**kwargs)
            ll = f'{log_level}'.lower()
            if ll == "info":
                self.log.info(my_string)
            if ll == "warn":
                self.log.warn(my_string)
            if ll == "debug":
                self.log.debug(my_string)
            if ll == "error":
                self.log.error(my_string)

    def _build_string(self, **kwargs):
        my_string = []
        for key, value in kwargs.items():
            my_string.append(f"{key}=\"{value}\"")
        return " ".join(my_string)
