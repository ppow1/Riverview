# Robotic Net Fabrication & Custom Outdoor Structures
## Executive Summary and Business Feasibility Proposal
**Date:** 2026-10-14  
**Status:** Concept / preliminary feasibility; not approved for implementation  
**Primary market:** Custom residential suspended treenets and indoor loft-style net floors  
**Repository classification:** Independent business idea, not Riverview product scope

### Executive decision
Investigate a service-first business that designs and installs custom woven rope-net floors, suspended walkways, platforms, and tunnels using an internally developed cable-traveling robotic weaving system. Own and operate the equipment rather than initially selling robots. The preliminary unit economics appear promising enough to justify a small proof-of-concept, but no structural safety, market demand, knot reliability, or profitability claims are validated.

### Customer offering and market
Target high-end residential yards with suitable trees, indoor high-ceiling open spaces, and eventually recreation properties. Offer site-specific geometric layouts, integrated platforms, connecting tunnels, optional screens and seasonal shade/rain coverings, and future accessory upgrades. Illustrative market positioning from prior discussion: custom handwoven installations may be quoted in a broad ~$50–$100 per square foot range; these are planning assumptions, not verified current bids or guaranteed realized prices. Customer acquisition, competition, insurance, permitting, and willingness-to-pay require validation.

### Baseline reference installation
- Circular 15-foot diameter net (large residential trampoline footprint): area pi*(7.5)^2 = 176.7 sq ft; perimeter 47.1 ft.
- Illustrative revenue: $8,836 at $50/sq ft; $13,254 at $75/sq ft; $17,671 at $100/sq ft.
- Initial geometric model: two-direction square grid, 4-inch spacing. Approximate straight rope length 2*A/s = 1,060 ft; 25% allowance for knots/routing/waste gives ~1,325 ft. This is *not* a validated pattern, knot allowance, or engineered mesh design.
- Example costing assumption: 5/16-inch polyester cord at $0.1483/ft gives ~$197 for the mesh. This is a **commodity rope costing placeholder**, not an approved life-safety material. Knot efficiency, dynamic load, creep, abrasion, UV exposure, strength after weathering, and mesh opening size require engineering and tests.
- Previous discussion compared 3, 4, 6, 8 inch spacings; smaller spacing increases cord and intersection count. Mesh geometry and knot topology may change lengths substantially.

### Illustrative project economics (not a quote)
| Item | Model amount |
|---|---:|
| Revenue at $75/sq ft | $13,250 |
| Woven cordage included within materials | ~$197 |
| All installation materials, including perimeter and anchor allowances | $1,350 |
| Labor: 2 workers x 2 days x 8h x $35 loaded | $1,120 |
| Engineering / inspection allowance | $1,000 |
| Travel, equipment and setup | $500 |
| Robot wear and maintenance | $200 |
| Contingency | $500 |
| **Modeled direct job cost** | **$4,670** |
| **Modeled contribution before overhead** | **$8,580 (64.8%)** |

At the same direct cost, $50/sq ft gives ~$4,166 contribution and $100/sq ft gives ~$13,001. These are *scenario arithmetic*, not forecast net profits. Exclusions include development labor, taxes, financing, insurance premiums, permitting, marketing, sales, warranty, legal review, robot downtime, overhead, and unforeseen structural work. Labor assumptions are illustrative; production equivalence to a two-person hand-weaving crew is unproven. Structural costs may exceed allowances, particularly for elevated or indoor retrofits.

### Robotic fabrication concept
A lightweight mobile carriage travels along one or two tensioned support cables, driven by onboard wheels or haul lines. A local Delta-type 3-axis manipulator positions an integrated rope-feed/knotting tool. A hook/loop/feed mechanism captures an existing strand, forms the knot, tensions it, verifies the result, and moves to the next intersection; **not** a humanoid robotic hand. Potentially 5–7 small actuators in the knot head. An ESP32-class controller manages motion, motors, sensors, interlocks, cameras, tension sensing, and DeWalt-compatible removable battery power. Laptop or local/cloud AI server handles site reconstruction, pattern generation, and higher-level scheduling. Aim for a light ~10–20 lb carriage but verify weight budget after motor, spool, and battery selection.

360-degree access about the travel axis could support enclosed cylindrical or polygonal tubes, not just horizontal floors. Candidate mechanisms include rotating the Delta assembly around a central spine or an alternative radial manipulator. Off-axis reach creates torque and suspension twist; movable counterbalance, potentially using battery mass, is a concept requiring mechanical analysis. Ensure carriage can exit completed geometry and avoid mesh/cable collisions.

For the illustrative 4-inch grid, roughly 1,500–1,600 intersections imply ~27–29 seconds per completed intersection if weaving takes 12 hours. This is a **target derived from assumptions**, not demonstrated robot throughput. The real knot pattern may have a different intersection count.

### Modular manufacturing architecture
Separate (1) cable-carriage/positioning chassis, (2) Delta or radial work mechanism, and (3) replaceable material-specific toolhead. Preserve common control, coordinates, camera sensing, project graph, and toolhead electrical/mechanical interface. Different robot sizes may support different material diameters and loads; diameter alone does not capture stiffness or bend-radius requirements.

Possible specialized heads:
- Rope feed, knot formation, tightening, verification.
- Wire spool feed, bending/wrapping/intersection joining; connection strength and fatigue must be qualified. Electric fence wire is a feedstock analogy, **not** an approved animal-enclosure specification.
- Cable lacing and secondary shape-retaining links.
- Mesh/panel fastening around planned reinforced accessory frames.

### Hybrid construction and accessories
Multi-pass workflow: install primary load-bearing cable/rope skeleton; add engineered secondary connections to control geometry; robotically weave selected cordage regions; then attach premade mesh, screening, doors, windows, hatches, platforms, junctions, or shade/rain panels. Some accessories may be 3D printed, others bought or fabricated conventionally. Use standardized interfaces and a parametric component graph that encodes geometry, material, intended load role, fasteners, and fabrication sequence. Design openings and reinforced attachment points *before* weaving. Do not rely on ordinary printed parts or nonstructural wire ties as primary life-safety connectors.

Optional canopy systems include manually installed panels and retractable fabric running along guide wires, similar to greenhouse shade curtains. Shade mesh differs from waterproof roofing; roof slope, drainage, wind uplift, stowage, and added load matter. Retrofitting upgrades requires reserving structural capacity at initial design.

### Other potential applications (future, not initial product)
- Custom chicken tunnels/fowl runs and catios: property-scanned routes and enclosed connections. Predator-resistant appropriately selected welded hardware cloth may be required rather than rope or ordinary chicken wire.
- Aviaries, garden enclosures, shade structures.
- Elevated deer-hunting blinds with bottom access hatch, removable camouflage, rain/wind panels, and insulated seasonal barriers. Safe access, fall protection, ventilation and heater safety require specific design.
- Larger suspended recreational nets, enclosed 360-degree tunnels, multi-platform branching networks, and modular windows/doors/chutes.

### Tree and indoor anchoring
Explore broad load-rated polyester webbing (lower wet stretch than nylon) around suitable trees with replaceable protective sleeves, rather than permanent tree drilling where avoidable. Split inner tubes are an inexpensive *experiment*, not a qualified UV-resistant or tree-friendly final solution; rubber may degrade, trap moisture, or abrade bark. The sleeve does not make exposed webbing UV-resistant. Trees and root systems, strap pressure, geometry, pretension, movement, growth, and inspection intervals must be evaluated by qualified professionals. Indoor structural members require equivalent engineering verification. Anchor reactions can be much larger than the supported vertical load for shallow cable sag.

### Robot hardware budget (preliminary, unsourced allowances)
| Subsystem | Estimate |
|---|---:|
| Carriage/frame/wheels/bearings | $250 |
| Travel motors/pulleys | $220 |
| Delta motors/arms/joints | $350 |
| 360-degree rotation/counterbalance | $200 |
| Knotting head actuators/guides | $450 |
| Spool/feed/tension | $180 |
| Controllers/drivers/wiring | $160 |
| Cameras/lighting/sensors | $130 |
| Battery interface/power | $150 |
| Test suspension cables/tensioners | $250 |
| Printed parts/fasteners/miscellaneous | $210 |
| **Subtotal** | **$2,550** |
| 25% contingency | $638 |
| **Total** | **~$3,188** |

Bench knotting-head prototype: ~$300–$800; complete experimental robot: ~$2,500–$3,500; more robust field prototype: ~$4,000–$5,000. These exclude engineering time, destructive testing, certification, and professionally engineered site rigging. A $10,000 robot material allowance seems higher than the initial hobby/experimental component model, but cost escalation remains possible.

### Safety and gating unknowns
No proposed mesh, knot, tree attachment, platform, or robot is presently qualified to carry people. Required work includes design loads and dynamic loading; safety factors appropriate to relevant codes and standards; rope material qualification; knot strength retention and slippage; fatigue/abrasion/UV; redundant fall protection; perimeter restraint; anchors and tree health; installation access; emergency rescue; insurance and permitting. Engineering review and representative destructive/proof tests must precede human use or sales. There is no basis yet to assert a 2–3x safety margin.

### Proposed validation sequence
1. Document a specific rope and knot topology and measure rope consumed per knot, strength retention, and slip under representative tension.
2. Build a stationary knotting head for ~$300–$800; demonstrate 100 consecutive correctly formed knots with recorded time, tension, and failure rate.
3. Make a small non-human-rated net sample and perform instrumented load/destructive testing; revise spacing and material cost.
4. Build a short-span carriage/Delta test rig and prove repeatable reach, 360-degree constraints, feed reliability, and recovery from jams.
5. Construct a larger ground-level non-occupiable demonstrator; measure real labor, consumables, setup, cycle time, maintenance, and scrap.
6. Obtain structural, tree/anchor, regulatory, and insurance review before any occupied elevated prototype.
7. Interview prospective residential customers and obtain comparable installer quotes; revise unit economics and go/no-go.

### Initial go/no-go criteria
Proceed beyond bench phase only if the knotter consistently completes the chosen knot, measured knot strength and slip are suitable for engineering evaluation, realistic cycle time approaches the commercial target, the carriage weight/power envelope is achievable, and revised job margins remain attractive after complete installation and business costs. Do not spend on a full field robot merely because the theoretical rope cost is low.

### Governance and next steps
This is an **idea archive and executive proposal**, not authorization to change Riverview's operational roadmap, deploy software, or spend funds. Keep future feasibility revisions, test logs, supplier quotes, structural analyses, and commercial evidence adjacent to this proposal. Link any later implementation work through an explicitly approved project/work order. Search for the earlier Estate “You've Got Mail” / “EWE” sheep-mascot mailbox idea remains unresolved; avoid asserting a verified folder association until found.
