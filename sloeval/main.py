import logging

from . import config


def cronrun():
    logging.basicConfig(level=0)
    config.load_configs()
    for slo in config.SLOs:
        slomet, sloval = slo.evaluate()
        logging.info(f'SLO "{slo.name}" met: {slomet}, SLO value: {sloval}')
