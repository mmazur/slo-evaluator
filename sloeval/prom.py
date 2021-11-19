import requests
from urllib.parse import urljoin


class PrometheusClient:
    """Class for connecting to and querying a Prometheus instance. Returns a json with the result."""
    def __init__(self, hosturl, token=None):
        self.hosturl = hosturl
        self.token = token
    
    def query(self, query, ts="Not supported yet"):
        url = urljoin(self.hosturl, "api/v1/query")
        headers = {
            "accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        params = {'query': query}
        response = requests.get(url, params=params, headers=headers)

        if response.ok: # TODO: this needs to be made more reliable
            return response.json()['data']
        else:
            return None


    #def query_range(self, query, start, end, step):
