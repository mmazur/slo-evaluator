from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

import pandas as pd
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
    PANDAS_CSV = "pandas/csv"


@dataclass
class SLI:
    """Class for storing Indicators. Assumes thresholdMetric type."""
    type: SLIType
    source: str
    query: str
    query_type: SLIQueryType
    multi_system: bool = False # Does this query return values for a single or multiple systems
    multi_system_id_fields: dict = field(default_factory=dict) # What to use to identify different systems, e.g. 'labels'


# TODO: this is likely a horrible way to represent TimeWindows internally
class TimeWindowUnit(Enum):
    MINUTE = "m"
    HOUR = "h"
    DAY = "d"
    WEEK = "w"
    # TODO: reenable this when non–rolling time windows support gets added
    # MONTH = "M"
    # QUARTER = "Q"
    # YEAR = "Y"


@dataclass
class TimeWindow:
    """Only supports "rolling=True" for now."""
    count: int
    unit: TimeWindowUnit
    rolling: bool

    def to_datetime(self, endtime):
        """Returns the TimeWindow as a datetime object relative to `endtime`."""
        td = pd.to_timedelta(self.count, self.unit.value)
        return endtime-td


    def to_prom_shorthand(self):
        """Return a prom-compatible shorthand string of the time window.
        
        Based on https://prometheus.io/docs/prometheus/latest/querying/basics/#time-durations"""
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


    def _evaluate_window_performance_on_threshold(self, df, op, value, retonnodata=0):
        """Takes a dataframe with index "timestamp" and "value" column.
        Compares each value in `df` by doing `op`eration against `value`.

        Returns window performance (matches/total) as float.
        If dataframe is empty returns `retonnodata`."""
        querystr = f"value {op.value} {value}"
        total = df.value.count()
        if total:
            matching = df.query(querystr).value.count()
            return matching/total
        else:
            return retonnodata


    def evaluate(self, endtime=None):
        """Evaluate the value of the SLO at the moment or at `endtime` if provided.

        Returns a tuple of (SLO isMet bool, SLO value float)"""

        if not endtime:
            endtime = pd.Timestamp.now()
        starttime = self.time_window.to_datetime(endtime)

        if self.sli.type == SLIType.OBJECTIVE and self.sli.query_type == SLIQueryType.PROMQL:
            pc = PrometheusConnect(url=self.sli.source)
            # TODO: does avg_over_time look at all data points for large enough time windows?
            querystr = f'avg_over_time({self.sli.query}[{self.time_window.to_prom_shorthand()}])'
            logging.debug(f"Running promql query: `{querystr}`")
            result = pc.custom_query(querystr)
            #TODO: change to MetricSnapshotDataFrame?
            res_value = int(result[0]["value"][1])
            res_ismet = res_value >= self.target

            return(res_ismet, res_value)
        elif self.sli.type == SLIType.THRESHOLD and self.sli.query_type == SLIQueryType.PANDAS_CSV:
            rawdf = pd.read_csv(self.sli.source, index_col='timestamp', parse_dates=['timestamp'])
            if str(rawdf.index.dtype).startswith("int") or str(rawdf.index.dtype).startswith("float"):
                # Most likely a unix epoch timestamp, convert it to DateTimeIndex
                newindex = rawdf.index.to_series().apply(lambda ts: datetime.fromtimestamp(ts))
                rawdf.set_index(newindex, inplace=True)
            df = rawdf.query(self.sli.query)
            df = df[(df.index >= starttime) & (df.index <= endtime)]
            perf = self._evaluate_window_performance_on_threshold(df, self.op, self.value)
            res_ismet = perf >= self.target

            return (res_ismet, perf)
        else:
            logging.error(f"Unsupported combination of SLI type '{self.sli.type} and query type {self.sli.query_type}")
            return (None, None)
