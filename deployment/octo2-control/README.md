<!-- Version: 1.0.0 | Date: 2026-10-26 -->
# OCTOMINER2 OCTO Control source and deployment notes

The `server.py` and `instance_manager.py` files are the source snapshot retrieved
from the live OCTOMINER2 installation on 2026-10-26. Version 0.6.3 adds bounded
controls for the existing, systemd-managed Qwen 30B Vision workload. Runtime
credentials and mutable host configuration remain on OCTOMINER2.

The only initially allowlisted workload is `qwen30b-vision.service`. Its status
is read from systemd and `http://127.0.0.1:8080/health`. The start and stop
operations call only `systemctl start` and `systemctl stop` for that allowlisted
unit. Neither operation changes `UnitFileState`; the service stays enabled at
boot and retains its existing `Restart=on-failure` recovery behavior. New
selectable workloads can be added as explicit records in
`managed_services.MANAGED_WORKLOADS` after their unit, identity, and health
endpoint are known.

## Host inventory verified 2026-10-26

- OCTOMINER2: `192.168.1.162`, physical NIC MAC `00:e0:4c:53:9e:5e`.
- One NVIDIA GPU: Tesla P100 PCIe 16 GB, GPU 0, UUID
  `GPU-83125857-5cbe-b7b3-4861-479383b01613`.
- `qwen30b-vision.service`: enabled and active; Qwen 30B Vision on TCP 8080.
- The earlier RTX 3060 Ti plus two-P100 OCTOMINER2 inventory is superseded;
  those additional GPUs were moved to OCTOMINER1.

## Install from this source tree

Copy `server.py`, `instance_manager.py`, and `managed_services.py` to
`/opt/riverview-octo-control/`, preserving the existing `models.json`,
`control.token`, `state.json`, and `instances.json`. Before replacing files,
make timestamped backups. Run `python3 -m py_compile` on the three files, then
restart only `riverview-octo-control.service`. This controller restart does
not restart or stop `qwen30b-vision.service`.

Verify the dashboard contains **Managed Workloads**, then use the authenticated
`GET /api/v1/workloads` route to check running/readiness and boot-enabled state.
Do not verify the start/stop controls by invoking them against the live model
without explicit authorization; the local tests mock systemd and exercise both
actions without changing the running workload.

To roll back, restore the timestamped controller-file backups and restart only
`riverview-octo-control.service`. Do not restore or overwrite token, model,
deployment-state, or instance files as part of that rollback.
