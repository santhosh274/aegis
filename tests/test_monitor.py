from core.monitor.scanner_manager import ScannerManager


def test_monitor_normalizes_tool_records():
    records = ScannerManager().normalize("10.0.0.5", "fixture", [{"kind": "service", "value": "ssh/22"}])
    assert records[0].target == "10.0.0.5"
    assert records[0].value == "ssh/22"
