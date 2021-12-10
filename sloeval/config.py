import glob
import logging
import os

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
        if "objectiveMetric" in y["spec"]["indicator"]:
            slitype = oslo.SLIType.OBJECTIVE
        elif "thresholdMetric" in y["spec"]["indicator"]:
            slitype = oslo.SLIType.THRESHOLD
        else:
            raise oslo.OSLOElementNotSupported(
                "Unsupported indicator type: {}".format(list(y["spec"]["indicator"].keys())))

        metric = y["spec"]["indicator"][slitype.value]
        slisource = metric["source"]
        sliquery_type = oslo.SLIQueryType[metric["queryType"].upper()]
        sliquery = metric["query"]
        slimulti_system = oslo.SLI.multi_system # get the default value from the data class
        slimulti_system_id_fields = {} # not possible to get the default value from the data class
        if "metadata" in metric:
            slimulti_system = metric["metadata"].get("multiSystem", slimulti_system)
            slimulti_system_id_fields = metric["metadata"].get("multiSystemIdFields", slimulti_system_id_fields)

        newsli = oslo.SLI(type=slitype, source=slisource,
                          query_type=sliquery_type, query=sliquery,
                          multi_system=slimulti_system, multi_system_id_fields=slimulti_system_id_fields)

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
    for slofile in glob.glob("*.yaml", root_dir=slopath):
        try:
            newslo = load_slo_file("{}/{}".format(slopath, slofile))
            if newslo:
                SLOs.append(newslo)
        except BaseException as err:
            logging.error(
                f'Something went wrong while parsing "{slofile}", this SLO will not be evaluated.')
            logging.error(f'Encountered error: {err}')
    logging.info(
        f"SLO config parsing complete, got {len(SLOs)} SLOs to evaluate")
