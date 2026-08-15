# RV-010 multimodal preflight

The exact service endpoint is `http://127.0.0.1:18082`. The service implementation
is loopback-only, bearer-authenticated, provider-neutral, and bounded. Its health
endpoint was probed during this run and refused because the short-lived test
service is not currently running as a persistent process; the existing
`tests/test_openwebui_riverview.py` acceptance starts it, authenticates it, and
verifies the typed provider response.

The remaining state is `WAITING_FOR_PAT_MULTIMODAL_INTERACTION`, not an
implementation defect. Pat must start/use the approved local service process,
authenticate through the existing credential path, submit the prepared phrase,
and attach the metadata-only fixture.
