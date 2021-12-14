from dataclasses import dataclass, field
from enum import Enum
import logging
from prometheus_api_client import PrometheusConnect

# Once OpenSLO spec is stable it might be good to replace this with just using the spec data structure directly.
# OTOH that might not end up being super viable if the code needs to do enough complicated things.

class OSLOElementNotSupported(Exception):
    """Raised when encountering an element of OpenSLO spec that is not supported."""
    pass


class SLIType(Enum):
    OBJECTIVE = "objectiveMetric"
    THRESHOLD = "thresholdMetric"


class SLIQueryType(Enum):
    PROMQL = "promql"


@dataclass
class SLI:
    """Class for storing Indicators. Assumes thresholdMetric type."""
    type: SLIType
    source: str
    query: str
    query_type: SLIQueryType
    multi_system: bool = False # Does this query return values for a single or multiple systems
    multi_system_id_fields: dict = field(default_factory=dict) # What to use to identify different systems, e.g. 'labels'


class TimeWindowUnit(Enum):
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    MONTH = "M"
    QUARTER = "Q"
    YEAR = "Y"


@dataclass
class TimeWindow:
    count: int
    unit: TimeWindowUnit
    rolling: bool

    def prom_shorthand(self):
        """Return a prom-compatible shorthand string of the time window."""
        # TODO: make sure this is actually prom-compatible; there was golib for this that set the standard…
        return f"{self.count}{self.unit.value}"


class SLOOp(Enum):
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="


@dataclass
class SLO:
    """Class for storing Objectives"""
    # These floats might be better off as Decimals maybe?
    name: str
    sli: SLI
    target: float
    time_window: TimeWindow
    op: SLOOp = None
    value: float = None
    multi_system_aggregate: bool = True # For multiSystem SLIs also generate an aggregate SLO

    def evaluate(self, ts="Not supported yet"):
        """Evaluate the value of the SLO at the moment or at timestamp if provided.
        
        Returns a tuple of (SLO isMet bool, SLO value float)"""
        if self.sli.type == SLIType.OBJECTIVE and self.sli.query_type == SLIQueryType.PROMQL:
            pc = PrometheusConnect(url=self.sli.source)
            querystr = f'avg_over_time({self.sli.query}[{self.time_window.prom_shorthand()}])'
            logging.debug(f'Running promql query: "{querystr}"')
            result = pc.custom_query(querystr)
            res_value = int(result[0]["value"][1])
            res_ismet = res_value >= self.target
            return(res_ismet, res_value)
        else:
            return (None, None)
