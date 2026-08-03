# Verify phase

A remediation event does not close a finding. Verify first establishes replay controls
(target identity, reachability, and prerequisites), then replays the stored typed
attack chain. A reproduced chain reopens the finding. A decisive failed step with
controls established verifies closure. New post-change exposures produce a regression
verdict. Failed controls always mean `inconclusive`.
