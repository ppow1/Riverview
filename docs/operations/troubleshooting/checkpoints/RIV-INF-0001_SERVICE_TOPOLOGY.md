# RIV-INF-0001: Service topology collision

This checkpoint covers duplicate service identities, host/port collisions, or
dependencies that are not represented in the bounded Riverview topology.

Recovery is to stop topology acceptance, identify the conflicting owner from
the accepted service configuration, correct the bounded map, and rerun the
collision and health checks. The topology must not infer physical rack,
cable, or power ownership.

For Operator recovery, the owner is the installed `Riverview Runtime Supervisor`
task, which launches `riverview.runtime.supervisor` from the repository registry.
The supervisor owns Operator, Comms5 HTTP/transport, Relay, and the CME
component supervisor. A broad Estate runtime host is not a Riverview owner.
The former CME and Comms5 peer tasks must be disabled after migration. If the
unified owner or its registry is missing, classify the seam as
`missing-lifecycle-owner` and escalate; do not create an alternate scheduler,
rotate credentials, or start an unmanaged duplicate.
