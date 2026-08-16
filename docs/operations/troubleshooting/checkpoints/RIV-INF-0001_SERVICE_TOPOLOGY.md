# RIV-INF-0001: Service topology collision

This checkpoint covers duplicate service identities, host/port collisions, or
dependencies that are not represented in the bounded Riverview topology.

Recovery is to stop topology acceptance, identify the conflicting owner from
the accepted service configuration, correct the bounded map, and rerun the
collision and health checks. The topology must not infer physical rack,
cable, or power ownership.
