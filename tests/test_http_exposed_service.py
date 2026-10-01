import pytest

from core.knowledge_base.models import AttackStep
from plugins.corroboration.http_exposure_validation import HttpExposureCorroborator
from plugins.exploits.http_exposed_service import (
    HttpExposedServiceAdapter,
    HttpExposedServiceError,
)


def make_connector(pages: dict[tuple[int, str], bytes]):
    """Connector serving canned pages per (port, path); everything else refused."""

    def connector(target, port, path, timeout):
        key = (port, path)
        if key not in pages:
            raise ConnectionRefusedError(f"no service at {target}:{port}")
        return pages[key]

    return connector


DVWA_LOGIN = b"<html><title>Login :: Damn Vulnerable Web App (DVWA)</title></html>"
PHP_MYADMIN = b"<html><title>phpMyAdmin</title></html>"


def test_run_returns_evidence_for_matched_known_application():
    pages = {
        (80, "/dvwa/login.php"): DVWA_LOGIN,
        (80, "/phpmyadmin/index.php"): PHP_MYADMIN,
    }
    adapter = HttpExposedServiceAdapter(connector=make_connector(pages))
    step = AttackStep(
        plugin="http_exposed_service",
        action="fingerprint_web_services",
        target="192.168.232.10",
        expected_predicate="known_application_marker_present",
    )

    evidence = adapter.run(step)

    assert evidence.kind == "exposed_web_service"
    assert "DVWA" in evidence.summary
    assert "phpMyAdmin" in evidence.summary
    assert evidence.source == "http_exposed_service"


def test_run_raises_when_service_reachable_but_no_known_app():
    pages = {(80, "/dvwa/login.php"): b"<html>generic nginx page</html>"}
    adapter = HttpExposedServiceAdapter(connector=make_connector(pages))
    step = AttackStep(
        plugin="http_exposed_service",
        action="fingerprint_web_services",
        target="192.168.232.10",
        expected_predicate="known_application_marker_present",
    )

    with pytest.raises(HttpExposedServiceError, match="no known-vulnerable web application matched"):
        adapter.run(step)


def test_run_raises_when_no_http_endpoint_reachable():
    adapter = HttpExposedServiceAdapter(connector=make_connector({}))
    step = AttackStep(
        plugin="http_exposed_service",
        action="fingerprint_web_services",
        target="10.0.0.1",
        expected_predicate="known_application_marker_present",
    )

    with pytest.raises(HttpExposedServiceError, match="no HTTP endpoint reachable"):
        adapter.run(step)


def test_default_ports_include_https_and_probe_them():
    from plugins.exploits.http_exposed_service import DEFAULT_PORTS, TLS_PORTS

    assert 443 in DEFAULT_PORTS
    assert 8443 in DEFAULT_PORTS
    assert 443 in TLS_PORTS and 8443 in TLS_PORTS


def test_tls_context_disables_verification_for_lab_certs():
    from plugins.exploits.http_exposed_service import _tls_context

    ctx = _tls_context()
    assert ctx.check_hostname is False
    assert ctx.verify_mode.name == "CERT_NONE"


def test_run_probes_https_port_when_open():
    pages = {(443, "/phpmyadmin/index.php"): PHP_MYADMIN}
    adapter = HttpExposedServiceAdapter(connector=make_connector(pages))
    step = AttackStep(
        plugin="http_exposed_service",
        action="fingerprint_web_services",
        target="192.168.232.10",
        expected_predicate="known_application_marker_present",
    )

    evidence = adapter.run(step)

    assert "phpMyAdmin" in evidence.summary
    assert ":443" in evidence.summary


def test_corroborator_supports_on_independent_fetch():
    pages = {(80, "/phpmyadmin/index.php"): PHP_MYADMIN}
    probe = HttpExposureCorroborator(connector=make_connector(pages))
    from core.knowledge_base.models import Finding, Evidence

    finding = Finding(
        title="t", target="192.168.232.10", claim="c",
        primary_evidence=Evidence("primary", "s", "http_exposed_service"),
    )

    result = probe.corroborate(finding)

    assert result.probe == "http_exposure_validation"
    assert result.outcome.value == "supports"
    assert result.independent


def test_corroborator_contradicts_when_no_marker():
    pages = {(80, "/phpmyadmin/index.php"): b"<html>generic page</html>"}
    probe = HttpExposureCorroborator(connector=make_connector(pages))
    from core.knowledge_base.models import Finding, Evidence

    finding = Finding(
        title="t", target="192.168.232.10", claim="c",
        primary_evidence=Evidence("primary", "s", "http_exposed_service"),
    )

    result = probe.corroborate(finding)

    assert result.outcome.value == "contradicts"


def test_corroborator_ambiguous_when_unreachable():
    probe = HttpExposureCorroborator(connector=make_connector({}))
    from core.knowledge_base.models import Finding, Evidence

    finding = Finding(
        title="t", target="10.0.0.1", claim="c",
        primary_evidence=Evidence("primary", "s", "http_exposed_service"),
    )

    result = probe.corroborate(finding)

    assert result.outcome.value == "ambiguous"