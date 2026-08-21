"""Riverview unified runtime lifecycle control.

The supervisor module is intentionally loaded lazily so ``python -m
riverview.runtime.supervisor`` does not import itself before runpy executes it.
"""

__all__ = ["RuntimeSupervisor", "ServiceRegistry"]

def __getattr__(name: str):
    if name in __all__:
        from .supervisor import RuntimeSupervisor, ServiceRegistry
        return {"RuntimeSupervisor": RuntimeSupervisor, "ServiceRegistry": ServiceRegistry}[name]
    raise AttributeError(name)
