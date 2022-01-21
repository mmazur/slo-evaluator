import glob
import logging
from pathlib import Path

import yaml

from . import oslo

SLOs = []


def load_slo_file(path):
    """Read and parse a yaml file from "path" with OpenSLO contents. Returns an SLO() object if successful."""
    with open(path, "r") as slofile:
        # Once the spec is compatible with what we're doing, there should be a validation step here so the code
        # can just assume elements being places and having valid values
        y = yaml.safe_load(slofile)

        # Parse Indicator bits
        if "thresholdMetric" in y["spec"]["indicator"]:
            slitype = oslo.SLIType.THRESHOLD
        #elif "objectiveMetric" in y["spec"]["indicator"]:
        #    slitype = oslo.SLIType.OBJECTIVE
        else:
            raise oslo.OSLOElementNotSupported(
                "Unsupported indicator type: {}".format(list(y["spec"]["indicator"].keys())))

        metric = y["spec"]["indicator"][slitype.value]
        slisource = metric["source"]
        sliquery_type = oslo.SLIQueryType[metric["queryType"].replace("/", "_").upper()]
        sliquery = metric["query"]
        slimulti_system = oslo.SLI.multi_system # get the default value from oslo.SLI class
        slimulti_system_columns = {} # not possible to get the default value from oslo.SLI class
        if "metadata" in metric:
            slimulti_system = metric["metadata"].get("multiSystem", slimulti_system)
            slimulti_system_columns = metric["metadata"].get("multiSystemColumns", slimulti_system_columns)
            # TODO: support len(multiSystemColumns) > 1
            if len(slimulti_system_columns) > 1:
                raise oslo.OSLOElementNotSupported("metadata.multiSystemColumns currently supports only one column")

        newsli = oslo.SLI(type=slitype, source=slisource,
                          query_type=sliquery_type, query=sliquery,
                          multi_system=slimulti_system, multi_system_columns=slimulti_system_columns)

        # Parse timeWindow bits
        twcount = y["spec"]["timeWindow"][0]["count"]
        twunit = oslo.TimeWindowUnit[y["spec"]
                                     ["timeWindow"][0]["unit"].upper()]
        twrolling = y["spec"]["timeWindow"][0]["isRolling"]
        tw = oslo.TimeWindow(count=twcount, unit=twunit, rolling=twrolling)

        # Parse Objective bits, combine all of it into a single object
        name = y["metadata"]["name"]
        target = y["spec"]["objectives"][0]["target"]
        if slitype == oslo.SLIType.THRESHOLD:
            op = oslo.SLOOp[y["spec"]["objectives"][0]["op"].upper()]
            value = y["spec"]["objectives"][0]["value"]
            newslo = oslo.SLO(name=name, sli=newsli, target=target, time_window=tw, op=op, value=value)
        else:
            newslo = oslo.SLO(name=name, sli=newsli, target=target, time_window=tw)

        return newslo


def load_configs(slopath="SLOs", sourcespath="sources"):
    """Load SLOs from a directory full of yamls."""
    path = Path(slopath) / '*.yaml'
    for slofile in glob.glob(str(path)):
        try:
            newslo = load_slo_file(slofile)
            if newslo:
                SLOs.append(newslo)
        except BaseException as err:
            logging.error(
                f'Something went wrong while parsing "{slofile}", this SLO will not be evaluated.')
            logging.error(f'Encountered error: {err}')
    logging.info(
        f"SLO config parsing complete, got {len(SLOs)} SLOs to evaluate")
