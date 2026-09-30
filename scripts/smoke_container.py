"""Exercise the production image under Kubernetes-compatible restrictions."""

import json
import subprocess
import sys
import time
import urllib.request


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True, stderr=subprocess.STDOUT).strip()


image = sys.argv[1]
config = json.loads(docker("image", "inspect", image))[0]["Config"]
assert config["User"] == "10001:10001", config["User"]
container = docker(
    "run", "--detach", "--read-only", "--cap-drop=ALL",
    "--security-opt=no-new-privileges", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
    "--publish", "127.0.0.1::5000", image,
)
try:
    port = docker("port", container, "5000/tcp").split(":")[-1]
    url = f"http://127.0.0.1:{port}"
    for attempt in range(30):
        try:
            with urllib.request.urlopen(url + "/healthz", timeout=2) as response:
                assert response.status == 200
                assert json.load(response) == {"status": "ok"}
            break
        except (OSError, TimeoutError):
            time.sleep(1)
    else:
        raise RuntimeError("Container did not become ready")
    with urllib.request.urlopen(url, timeout=2) as response:
        assert response.read() == b"Hello World!"
    with urllib.request.urlopen(url + "/error", timeout=2) as response:
        assert response.status == 200
        assert "error" in json.load(response)
    assert docker("exec", container, "id", "-u") == "10001"
    docker("exec", container, "python", "-c",
           "import importlib.util; assert importlib.util.find_spec('pipenv') is None; "
           "assert importlib.util.find_spec('pip_audit') is None; assert importlib.util.find_spec('pip') is None")
    healthcheck = config["Healthcheck"]["Test"]
    assert healthcheck[0] == "CMD-SHELL"
    docker("exec", container, "sh", "-c", healthcheck[1])
    docker("stop", "--time", "25", container)
    state = json.loads(docker("inspect", container))[0]["State"]
    assert state["ExitCode"] == 0, state
    logs = docker("logs", container)
    assert "Control server error" not in logs, logs
    print("Startup, probes, demo response, non-root, read-only filesystem, and SIGTERM passed")
finally:
    print(docker("logs", container))
    docker("rm", "--force", container)
