from core.knowledge_base.json_store import load_finding, save_finding
from core.knowledge_base.models import (
    AttackStep,
    ConfidenceGrade,
    Corroboration,
    CorroborationOutcome,
    Evidence,
    Finding,
    FindingStatus,
)


def make_full_finding() -> Finding:
    step = AttackStep(
        plugin="vsftpd_backdoor",
        action="trigger_backdoor",
        target="192.168.232.10",
        expected_predicate="listener_open_on_6200",
    )
    primary = Evidence(kind="shell_access", summary="listener observed", source="vsftpd_backdoor")
    corroboration = Corroboration(
        probe="rce_validation",
        outcome=CorroborationOutcome.SUPPORTS,
        evidence=Evidence(kind="rce_check", summary="nonce observed", source="rce_validation"),
        independent=True,
        rationale="separate session and nonce predicate",
    )
    finding = Finding(
        title="vsftpd 2.3.4 backdoor (CVE-2011-2523)",
        target="192.168.232.10",
        claim="Backdoored vsftpd spawns a root shell listener on port 6200",
        primary_evidence=primary,
        attack_chain=[step],
        confidence=ConfidenceGrade.CONFIRMED,
        status=FindingStatus.CONFIRMED,
        corroborations=[corroboration],
    )
    return finding


def test_round_trip_preserves_all_fields(tmp_path):
    original = make_full_finding()
    path = tmp_path / "finding.json"

    save_finding(original, path)
    restored = load_finding(path)

    assert restored.id == original.id
    assert restored.title == original.title
    assert restored.target == original.target
    assert restored.claim == original.claim
    assert restored.confidence == ConfidenceGrade.CONFIRMED
    assert restored.status == FindingStatus.CONFIRMED
    assert restored.created_at == original.created_at

    assert len(restored.attack_chain) == 1
    assert restored.attack_chain[0].plugin == "vsftpd_backdoor"
    assert restored.attack_chain[0].target == "192.168.232.10"
    assert restored.attack_chain[0].id == original.attack_chain[0].id

    assert len(restored.corroborations) == 1
    assert restored.corroborations[0].outcome is CorroborationOutcome.SUPPORTS
    assert restored.corroborations[0].independent is True


def test_round_trip_handles_no_corroborations_or_chain(tmp_path):
    finding = Finding(
        title="bare finding",
        target="10.0.0.1",
        claim="unverified claim",
        primary_evidence=Evidence(kind="x", summary="y", source="z"),
    )
    path = tmp_path / "bare.json"

    save_finding(finding, path)
    restored = load_finding(path)

    assert restored.attack_chain == []
    assert restored.corroborations == []
    assert restored.status == FindingStatus.OPEN
