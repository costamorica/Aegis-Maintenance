from aegis_maintenance.detect import SystemDetector
from aegis_maintenance.backends.registry import BackendRegistry
from aegis_maintenance.domain.context import ExecutionContext


class Bootstrap:
    def initialize(self):
        detector = SystemDetector()
        system_context = detector.detect()
        backend = BackendRegistry().select_backend(system_context)
        return ExecutionContext(system_context=system_context, backend=backend)
