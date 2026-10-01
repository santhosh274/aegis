import pytest

from core.knowledge_base.models import AttackStep
from plugins.registry import (
    CORROBORATORS,
    EXPLOITS,
    EXPLOIT_META,
    choose_exploit,
    is_exploit,
    reproduce,
)

ALLOW_ALL = tuple(EXPLOIT_META.keys())


def test_registry_contains_all_exploit_adapters_with_complete_metadata():
    assert set(EXPLOITS) == set(EXPLOIT_META) == {"vsftpd_backdoor", "ssh_weak_credentials", "http_exposed_service"}
    for name, meta in EXPLOIT_META.items():
        for key in ("title", "claim", "action", "expected_predicate", "importance", "services", "attck"):
            assert key in meta, f"{name} missing {key}"
        assert len(meta["attck"]) == 2
        assert meta["attck"][0].startswith("T")


def test_each_exploit_has_technique_scoped_corroboration():
    for name in EXPLOIT_META:
        assert name in CORROBORATORS, f"{name} has no corroboration probe"
        assert CORROBORATORS[name]


def test_choose_exploit_returns_highest_importance_for_observed_service():
    # ftp present -> vsftpd (importance 90) beats ssh (80)
    chosen = choose_exploit(
        ["ftp/21 (vsftpd 2.3.4)", "ssh/22 (OpenSSH 4.7p1)", "http/80 (Apache httpd 2.2.8)"],
        ALLOW_ALL,
    )
    assert chosen == "vsftpd_backdoor"


def test_choose_exploit_matches_ssh_and_http_services():
    assert choose_exploit(["ssh/22 (OpenSSH 4.7p1)"], ALLOW_ALL) == "ssh_weak_credentials"
    assert choose_exploit(["http/80 (Apache httpd 2.2.8)"], ALLOW_ALL) == "http_exposed_service"
    assert choose_exploit(["http/8180 (Apache Tomcat)"], ALLOW_ALL) == "http_exposed_service"


def test_choose_exploit_matches_nuclei_web_findings():
    # nuclei template names leak http apps; http_exposed_service picks them up
    chosen = choose_exploit(["[high] phpMyAdmin default login @ http://192.168.52.139/" ], ALLOW_ALL)
    assert chosen == "http_exposed_service"


def test_choose_exploit_returns_none_without_matching_observation():
    assert choose_exploit(["telnet/23"], ALLOW_ALL) is None


def test_choose_exploit_respects_allowlist():
    allow_only_vsftpd = ("vsftpd_backdoor",)
    # ssh observed but ssh_weak_credentials not allowlisted -> nothing eligible
    assert choose_exploit(["ssh/22 (OpenSSH 4.7p1)"], allow_only_vsftpd) is None
    assert choose_exploit(["ftp/21 (vsftpd 2.3.4)"], allow_only_vsftpd) == "vsftpd_backdoor"


def test_is_exploit_and_reproduce_unknown_plugin():
    assert is_exploit("ssh_weak_credentials")
    assert not is_exploit("nmap_scanner")
    step = AttackStep(plugin="does_not_exist", action="x", target="192.168.52.139", expected_predicate="p")
    assert reproduce(step) is False


def test_reproduce_dispatches_via_registered_adapter(monkeypatch):
    observed: list[str] = []

    class StubAdapter:
        name = "stub_exploit"

        def run(self, step):
            observed.append(step.plugin)
            if step.parameters.get("fail"):
                raise RuntimeError("boom")
            return None

    monkeypatch.setitem(EXPLOITS, "stub_exploit", StubAdapter())
    step = AttackStep(plugin="stub_exploit", action="x", target="192.168.52.139", expected_predicate="p")
    assert reproduce(step) is True
    assert observed == ["stub_exploit"]

    step = AttackStep(plugin="stub_exploit", action="x", target="192.168.52.139", expected_predicate="p", parameters={"fail": True})
    assert reproduce(step) is False