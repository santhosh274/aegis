"""Runtime safety settings. Lab targets must be explicitly allowlisted."""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address, ip_network


@dataclass(frozen=True)
class ScopePolicy:
    allowed_networks: tuple[str, ...] = ()
    allowed_hosts: tuple[str, ...] = ()
    allowed_plugins: tuple[str, ...] = ()
    lab_mode: bool = True

    def permits_target(self, target: str) -> bool:
        if target in self.allowed_hosts:
            return True
        try:
            address = ip_address(target)
        except ValueError:
            return False
        return any(address in ip_network(network, strict=False) for network in self.allowed_networks)

    def permits_plugin(self, plugin: str) -> bool:
        return plugin in self.allowed_plugins
