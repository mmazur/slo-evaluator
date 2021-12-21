# slo-evaluator
Evaluate&amp;Store Engine for OpenSLO–defined Objectives

## How it works

SLO Evaluator is intended to be run at predefined intervals (like a cronjob) and on each perform the following steps:

1. (TODO) Read configs defininig data sources and data sinks.
2. Read all yaml files from the `SLOs` directory and parse all SLOs defined therein (see [example-SLOs](example-SLOs) dir).
3. For each SLO defined connect to the data source, retrieve required data, evaluate the SLO for the current time window and (TODO) store the results in the appropriate data sinks.

## Dev Env

1. Clone this repo.
2. Make sure you have all the python modules from `requirements.txt`.
3. Generate some fake data like so:
   ```
   ./test/datagen.py --id-column-header sensor --ids=cpu,system,gpu --column node=klapek --column instance="localhost:9100" -c 200000 -s 60 -o test/node_temps.csv
   ```
4. Give it some test files and run the code:
   ```
   ln -s example-SLOs SLOs
   ./cronrun
   ```

You should see some example SLOs being calculated from the fake data you just generated.

## Design

* All configs are in yaml format.
* SLO configs are in the [OpenSLO](https://github.com/OpenSLO/OpenSLO/) format.
  * Deviations from the upstream spec should be kept to a minimum. Working with upstream on extending the spec where needed is emphasized.
* The code is in Python.
  * Data manipulation is done using [Pandas](https://pandas.pydata.org/) DataFrames.
* In principle any combination of data source and data sink should be supported.
  * However the initial design is based around supporting Prometheus and influences of that choice might be visible in places.

## TODO

* [ ] Unit tests all the things.
  * Start with functions that perform calculations, those are critical to be kept stable.
* [ ] Set up CI in the project once the tests are up.
  * Maybe a linter while we're at it (PEP8 at least?).
* [ ] Add `ratioMetric` support.
* [ ] Fully support Prometheus as a data source.
  * Waiting on [this prometheus-api-client PR](https://github.com/AICoE/prometheus-api-client-python/pull/234) to land first.
* [ ] Add support for [Vault](https://www.vaultproject.io/) for auth token retrieval for Prom.
* [ ] Spin off source–agnostic calculation code into its own module.
* [ ] Add some basic cli options to `cronjob` using Click module.
  * Log level, defining where configs are, maybe something else.
* [ ] Add an initial data sink.
  * SQL? Prom using [pushgateway](https://github.com/prometheus/pushgateway)?
* [ ] Morph `objectiveMetric` in current code into whatever the new metric becomes ([discussion](https://gist.github.com/nobl9-mikec/a1a55d97d77f10216be775eaad7221ac#gistcomment-3998338)).
