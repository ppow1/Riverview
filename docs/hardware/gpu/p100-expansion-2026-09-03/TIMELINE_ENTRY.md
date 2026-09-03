## 2026-09-03 — Three additional Tesla P100 16 GB GPUs purchased

A purchase for **three NVIDIA Tesla P100 16 GB HBM2 PCIe cards** was accepted and auto-paid for **US $225.75 total**. The listing identifies the cards as **Tesla P100 / PH400 / 699-2H400-0201-520**, used clean pulls from off-lease servers, sold by IMS Store. At the time of capture, the order was awaiting shipment.

This changes the planned Riverview GPU pool from one installed P100 to **four P100s total after successful arrival and acceptance**, adding 48 GB of P100 HBM2 capacity for a planned aggregate of 64 GB across the four P100 cards. The immediate research relevance is multi-GPU model splitting, larger KV/context budgets, persistent Hermes/resident sessions, and maintaining real VRAM headroom rather than operating at the single-P100 ~16 GB limit.

**Evidence:** see `docs/hardware/gpu/p100-expansion-2026-09-03/evidence/`.
