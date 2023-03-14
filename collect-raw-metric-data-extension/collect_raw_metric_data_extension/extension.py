import os

from localstack import config
from localstack.aws.handlers.metric_handler import MetricHandler
from localstack.extensions.api import Extension, aws, http
from localstack.http import Request


class MyExtension(Extension):
    name = "collect-raw-metric-data-extension"

    def on_extension_load(self):
        # enable the metric collection by setting the env
        os.environ["LOCALSTACK_INTERNAL_TEST_COLLECT_METRIC"] = "1"
        print("MetricCollectionExtension: extension is loaded")

    def on_platform_start(self):
        print("MetricCollectionExtension: localstack is starting")

    def on_platform_ready(self):
        print("MetricCollectionExtension: localstack is running")
        print(f"--> collect-metric-mode: {config.is_collect_metrics_mode()}")

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        print("---> adding custom route endpoint")
        # add two endpoints to retrieve and reset the metrics data
        router.add(
            "/metrics/raw", endpoint=retrieve_collected_metric_handler, methods=["GET"]
        )
        router.add(
            "/metrics/reset",
            endpoint=reset_collected_metric_handler,
            methods=["DELETE"],
        )

    def update_request_handlers(self, handlers: aws.CompositeHandler):
        pass

    def update_response_handlers(self, handlers: aws.CompositeResponseHandler):
        pass


def _create_simple_dict(metric):
    """creates a simple dict represenation of the metric
    currently only considering metrics we are interested in/use for docs coverage"""
    return {
        "service": metric.service,
        "operation": metric.operation,
        "parameters": metric.parameters,
        "response_code": metric.response_code,
        "response_data": metric.response_data,
        "exception": metric.exception,
        "origin": metric.origin,
    }


def reset_collected_metric_handler(request: Request):
    """endpoint for /metrics/reset
    clears the data in the MetricHandler"""
    MetricHandler.metric_data.clear()
    return


def retrieve_collected_metric_handler(request: Request):
    """endpoint for /metrics/raw
    returns the data collected by the MetricHandler"""
    res = [_create_simple_dict(m) for m in MetricHandler.metric_data]
    return {"metrics": res}
