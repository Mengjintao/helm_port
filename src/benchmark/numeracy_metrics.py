from typing import List

from common.request import RequestResult
from .adapter import AdapterSpec, RequestState
from .metric import Metric
from .metric_name import MetricName
from .metric_service import MetricService
from .statistic import Stat

from .numeracy_scenario import (  # noqa
    NumeracyScenario,
    Polynomial,
    RELTYPE_INFO,
    distance_linear,
    distance_parabola,
    distance_plane,
    distance_paraboloid,
)


class DistanceMetric(Metric):
    """Returns the minimum geometric distance between the point represented by the completion
       and the curve or surface specified by `rel_str`.

       Expects `references.outputs` to be a list containing the following:
        - val_GT (str): the last coordinate of the point lying on the given curve / surface
            with first coordinates as given in the input
        - rel_str (str): the relation
        - relation_type (str): one of {'linear', 'parabola', 'plane', 'paraboloid'}

        Returns:
            The minimum geometric distance from the point to the curve / surface (float).
    """

    def evaluate_generation(
        self, adapter_spec: AdapterSpec, request_state: RequestState, metric_service: MetricService, runs_path: str
    ) -> List[Stat]:
        """For given request, compute the following two metrics:
        1. geometric distance metric in range [0, ∞), calling the appropriate distance method, if possible, and
        2. percent valid metric in range [0., 1.] of completions that are a valid number, ignoring commas.
        """
        references = request_state.instance.references
        _, rel_str, relation_type = map(lambda _: _.output, references)
        input = request_state.instance.input
        datapoint_input = input.split("\n")[-1]
        val = list(map(int, datapoint_input.split(NumeracyScenario.delimiter)))

        distance_func = globals()[f"distance_{relation_type}"]
        result = 0.0
        num_valid = 0
        request_result: RequestResult = request_state.result
        for completion in request_result.completions:
            completion = completion.text.strip()
            try:
                pred = int(completion.replace(",", ""))  # ignore commas in numbers
            except Exception:
                continue
            point = val + [pred]
            result += distance_func(point, rel_str)
            num_valid += 1
        percent_valid = 1.0 * num_valid / len(request_result.completions)

        return [
            Stat(MetricName("distance")).add(result),
            Stat(MetricName("percent_valid")).add(percent_valid),
        ]
