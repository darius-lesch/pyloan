import os
import json
import datetime as dt
from decimal import Decimal

class SnapshotHelper:
    def __init__(self, snapshot_dir='tests/snapshots'):
        self.snapshot_dir = snapshot_dir
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

    def _get_snapshot_path(self, test_name):
        filename = f"{test_name}.json"
        return os.path.join(self.snapshot_dir, filename)

    def _serialize_data(self, data):
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return str(obj)
                if isinstance(obj, dt.datetime):
                    return obj.isoformat()
                return super().default(obj)

        return json.dumps(data, indent=2, cls=CustomEncoder)

    def compare(self, test_name, generated_data):
        snapshot_path = self._get_snapshot_path(test_name)
        serialized_data = self._serialize_data(generated_data)

        if os.environ.get('UPDATE_SNAPSHOTS') == '1':
            with open(snapshot_path, 'w') as f:
                f.write(serialized_data)
            return True, f"Snapshot for '{test_name}' updated."

        if not os.path.exists(snapshot_path):
            with open(snapshot_path, 'w') as f:
                f.write(serialized_data)
            raise AssertionError(f"Snapshot for '{test_name}' did not exist. A new one has been created. Please review it and run the tests again.")

        with open(snapshot_path, 'r') as f:
            snapshot_data = f.read()

        if snapshot_data != serialized_data:
            diff = f"--- Snapshot\n+++ Generated\n"
            # A simple diff-like output
            snapshot_lines = snapshot_data.splitlines()
            generated_lines = serialized_data.splitlines()
            for i in range(max(len(snapshot_lines), len(generated_lines))):
                s_line = snapshot_lines[i] if i < len(snapshot_lines) else ""
                g_line = generated_lines[i] if i < len(generated_lines) else ""
                if s_line != g_line:
                    diff += f"- {s_line}\n+ {g_line}\n"

            raise AssertionError(f"Snapshot for '{test_name}' does not match the generated data.\n\nDiff:\n{diff}")

        return True, f"Snapshot for '{test_name}' matches."
