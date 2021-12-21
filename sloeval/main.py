import logging

from . import config


def cronrun():
    logging.basicConfig(level=0)
    config.load_configs()
    for slo in config.SLOs:
        #TODO: catch exceptions to not abort the whole thing if a single SLO fails oddly?
        slomet, windowperf = slo.evaluate()
        logging.info(f'SLO "{slo.name}" met: {slomet}, window performance: {windowperf}')
