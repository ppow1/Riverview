# Riverview GPU Expansion Milestone — Three Additional Tesla P100s

**Event date:** 2026-09-03  
**Status:** Purchased / awaiting shipment at time of capture  
**Purpose:** Preserve acquisition provenance and Riverview hardware timeline.

## Event

On 2026-09-03, an order for **three additional NVIDIA Tesla P100 16 GB HBM2 PCIe GPUs** was accepted and auto-paid. The captured purchase page shows:

- Quantity: **3**
- Order total: **US $225.75**
- Item: **NVIDIA Tesla P100 16 GB HBM2 PCI-e Graphics Video Card GPU**
- Part/model identifiers shown in listing: **699-2H400-0201-520 / PH400 / P100**
- Seller: **IMS Store / IMS**
- Listing condition: **Used — “Clean pulls from off-lease servers”**
- Listing price visible at capture: **US $78.95 or Best Offer**
- Listing states PCI Express 3.0 x16, 16 GB HBM2, and a 30-day IMS warranty.

These three cards are intended to join the existing Tesla P100 already being used in the Riverview / OCTO1 local-model experiments, bringing the planned installed P100 count to **four** after arrival, installation, and acceptance testing.

## Why this matters to Riverview

This purchase follows the 2026-09-02/03 Riverview-brain experiments that established a viable local cognition path using a Huihui Qwen3-VL 30B-A3B IQ3_XS GGUF on a single Tesla P100 at 65,536 context, including structured tool calls and persistent Hermes operation.

The added P100s are intended to support experiments in:

- multi-GPU model splitting;
- larger practical context / KV-cache budgets;
- deliberate VRAM operating headroom rather than “barely fits” allocations;
- persistent resident cognition sessions;
- larger or higher-quality local model candidates;
- parallel specialist/resident workloads.

This record is acquisition provenance only. Arrival, serial/board identity, hardware health, installation location, thermals, power, and acceptance-test results should be appended as separate dated events when the cards arrive.

## Evidence

- `evidence/order-confirmation-quantity-3-total-225.75.png` — purchase page showing quantity 3, order date, order total, and awaiting-shipment state.
- `evidence/listing-screenshot-78.95-best-offer.png` — listing view showing the physical P100 card, seller, listed price, condition, and title.
- `evidence/ebay-listing-tesla-p100-699-2H400-0201-520.pdf` — complete five-page eBay listing capture.
- `evidence/downloads-pdf-presence.png` — screenshot showing the downloaded PDF present in the Windows Downloads folder on 2026-09-03.

## Provenance / preservation rules

- Original evidence files are preserved without editing.
- The descriptive filenames in this archive are archive copies; hashes are recorded in `SHA256SUMS.txt`.
- Do not replace this event with later recollection. Append later shipment, arrival, installation, failure, return, or acceptance events to the hardware timeline.
