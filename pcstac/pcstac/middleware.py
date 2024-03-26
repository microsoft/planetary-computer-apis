from http.client import HTTP_PORT, HTTPS_PORT
from typing import List

from stac_fastapi.api.middleware import ProxyHeaderMiddleware
from starlette.types import Receive, Scope, Send


class ProxyHeaderHostMiddleware(ProxyHeaderMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Call from stac-fastapi framework."""
        if scope["type"] == "http":
            proto, domain, port = self._get_forwarded_url_parts(scope)
            proto = self._get_header_value_by_name(scope, "x-forwarded-scheme", proto)
            domain = self.get_preferred_domain(scope, default_value=domain)

            if domain is not None:
                # A port may already be included from the # x-forwarded-host header
                domain_has_port = domain.find(":") > -1

                port_suffix = ""
                if not domain_has_port and port is not None:
                    if (proto == "http" and port != HTTP_PORT) or (
                        proto == "https" and port != HTTPS_PORT
                    ):
                        port_suffix = f":{port}"

                scope["headers"] = self._replace_header_value_by_name(
                    scope,
                    "host",
                    f"{domain}{port_suffix}",
                )
                scope["scheme"] = proto

        await self.app(scope, receive, send)

    def get_forwarded_hosts(self, scope: Scope) -> List[str]:
        """
        x-forwarded-host may contain a CSV of hosts, and also itself may show up
        multiple times within the scope.
        """
        hosts: List[str] = [
            host.decode()
            for key, host in scope["headers"]
            if key == b"x-forwarded-host"
        ]
        return [item for maybe_csv in hosts for item in maybe_csv.split(",")]

    def get_preferred_domain(self, scope: Scope, default_value: str) -> str:
        """
        Determine and return the most appropriate value for the host domain from
        a list of possible sources.
        """
        tlds = (".com", ".org", ".net")
        domains = self.get_forwarded_hosts(scope)

        for d in domains:
            if d.endswith(tlds):
                return d

        if len(domains) == 0:
            return default_value

        return domains[0]
