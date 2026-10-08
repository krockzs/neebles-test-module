"""Close of module-owned GUI must terminate this Open runtime IPC session."""
import ast
from pathlib import Path
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Child:
    def __init__(self, closed=True):
        self.closed = closed
    def poll(self):
        return 0 if self.closed else None
    def terminate(self):
        raise AssertionError("Closed UI must not be terminated twice")

class Stream:
    def __init__(self):
        self.closed = False
    def connect(self, path):
        self.path = path
    def close(self):
        self.closed = True

class TestGuiCloseEndsRuntimeSession(unittest.TestCase):
    def main_with_fake_session(self, child, on_poll=None):
        source = (ROOT / "runtime.py").read_text(encoding="utf-8")
        tree = ast.parse(source, filename="runtime.py")
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"]
        self.assertEqual(len(nodes), 1)
        isolated = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
        seen = []
        stream = Stream()
        cycles = [0]
        def next_message(_stream):
            cycles[0] += 1
            if on_poll is not None:
                on_poll(cycles[0])
            self.assertLess(cycles[0], 4, "Runtime did not release IPC after UI close")
            return None
        def validate_identity(reply, session_id):
            self.assertEqual(reply["module"], "test-module")
            self.assertEqual(reply["session_id"], session_id)
        namespace = {
            "STOP": False,
            "UI_PROCESS": None,
            "MODULE": "test-module",
            "PROTOCOL": 1,
            "os": types.SimpleNamespace(environ={"NEEBLES_MODULE": "test-module"}),
            "uuid": types.SimpleNamespace(uuid4=lambda: "session-gate143"),
            "stop_handler": lambda *_: None,
            "declared_endpoints": lambda: [],
            "signal": types.SimpleNamespace(signal=lambda *_:None, SIGTERM=15, SIGINT=2),
            "socket": types.SimpleNamespace(socket=lambda *_: stream, AF_UNIX=1, SOCK_STREAM=1),
            "SOCKET_PATH": "/fake/modules.sock",
            "requested_intent": lambda: "open",
            "write_message": lambda _stream, message: seen.append(message),
            "read_message": lambda _stream: {
                "type": "registered", "module": "test-module",
                "session_id": "session-gate143", "protocol": 1},
            "validate_identity": validate_identity,
            "subscribe": lambda *_: None,
            "launch_ui": lambda: child,
            "push_ui_message": lambda *_: None,
            "settings_get": lambda *_: "false",
            "next_runtime_message": next_message,
            "drain_ui_requests": lambda *_: None,
            "handle_control_message": lambda *_: False,
            "subprocess": types.SimpleNamespace(TimeoutExpired=TimeoutError),
        }
        exec(compile(isolated, "runtime.py/gate145-isolated-main", "exec"), namespace)
        namespace["main"]()
        self.assertTrue(stream.closed)
        unregister = [m for m in seen if m.get("type") == "unregister"]
        self.assertEqual(len(unregister), 1)
        self.assertEqual(unregister[0]["module"], "test-module")
        self.assertEqual(unregister[0]["session_id"], "session-gate143")
        self.assertEqual(unregister[0]["reason"], "runtime_exit")
        self.assertEqual(seen[0]["type"], "register")
        return cycles[0]

    def test_closed_ui_unregistered_without_spurious_ipc_cycle(self):
        self.assertEqual(self.main_with_fake_session(Child(closed=True)), 0)

    def test_ui_exits_after_running_then_unregisters(self):
        child = Child(closed=False)
        def on_poll(cycle):
            if cycle == 1:
                child.closed = True
        self.assertEqual(self.main_with_fake_session(child, on_poll), 1)

if __name__ == "__main__":
    unittest.main()
