import sys
import importlib
from time import time

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
import yaml


class DummyContext:
    def __init__(self, timeout=10):
        self.created = time()
        self.timeout = timeout

    def get_remaining_time_in_millis(self):
        return int(
            max(
                (self.timeout * 1000)
                - (int(round(time() * 1000)) - int(round(self.created * 1000))),
                0,
            )
        )


def compose_lambda_payload_v1(request):
    headers = {}
    multi_value_headers = {}
    for header in request.headers.keys():
        headers[header] = ""
        multi_value_headers[header] = []
        if value_list := request.headers.getlist(header):
            values = value_list[0].split(",")
            headers[header] = values[0]
            multi_value_headers[header] = values

    return {
        "httpMethod": request.method,
        "multiValueQueryStringParameters": request.args.to_dict(flat=False),
        "queryStringParameters": dict(request.args),
        "body": request.data,
        "path": request.path,
        "headers": headers,
        "multiValueHeaders": multi_value_headers,
    }


def compose_lambda_payload_v2(request):
    return {
        "httpMethod": request.method,
        "rawPath": request.path,
        "rawQueryString": request.query_string,
        "body": request.data,
        "headers": request.headers,
        "requestContext": {
            "http": {
                "method": request.method,
                "path": request.path,
            }
        },
    }


def compose_lambda_payload(request, payload_format_version):
    payload_handlers = {
        "1.0": compose_lambda_payload_v1,
        "2.0": compose_lambda_payload_v2,
    }
    return payload_handlers[payload_format_version](request)


class App:
    def __init__(self, url_map, views, payload_version):
        self.url_map = url_map
        self.views = views
        self.payload_version = payload_version

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            lambda_event = compose_lambda_payload(request, self.payload_version)
            func_response = self.views.get(endpoint)(
                lambda_event, DummyContext(**values), **values
            )
            return Response(
                func_response["body"],
                func_response["statusCode"],
                headers=func_response["multiValueHeaders"],
            )
        except NotFound:
            return Response("404 Not Found", mimetype="text/html")
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(config: str, payload_version: str = "2.0"):
    sys.path.append(".")

    with open(config, "r") as file:
        serverless = yaml.safe_load(file)

    urls = []
    views = {}

    if functions := serverless.get("functions"):
        for func_name, func_config in functions.items():
            if events := func_config.get("events"):
                for event in events:
                    event_config = event.get("http") or event.get("httpApi")
                    if event_config:
                        rule_kwargs = {}
                        if timeout := func_config.get("timeout"):
                            rule_kwargs["timeout"] = timeout
                        try:
                            module_path, handler_name = func_config["handler"].rsplit(
                                ".", maxsplit=1
                            )
                            module = importlib.import_module(module_path)
                            handler = getattr(module, handler_name)
                        except ImportError:
                            pass
                        else:
                            path = event_config["path"]
                            if not path.startswith("/"):
                                path = "/" + path
                            urls.append(Rule(path, endpoint=func_name, **rule_kwargs))
                            views[func_name] = handler

    return App(url_map=Map(urls), views=views, payload_version=payload_version)
