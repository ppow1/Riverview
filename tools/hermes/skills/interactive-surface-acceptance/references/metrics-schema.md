# Metrics JSON Schema

The optional evaluator accepts a JSON object with this shape:

```json
{
  "samples": [
    {
      "view": "resources",
      "action": "open-view",
      "ack_ms": 35,
      "shell_ms": 110,
      "usable_ms": 420,
      "hydrate_ms": 610,
      "memory_mb": 210,
      "js_heap_mb": 72,
      "dom_nodes": 1850
    }
  ],
  "cycles": [
    {
      "name": "navigation-loop",
      "memory_mb": [180, 194, 208, 221, 235],
      "dom_nodes": [1500, 1560, 1630, 1710, 1790]
    }
  ]
}
```

Fields may be omitted when unavailable.

The evaluator summarizes latency outliers and simple ratcheting-growth signals. It does not prove a memory leak; treat its leak flag as a reason for targeted profiling.
