"""Real Edge/CDP UI flow against the locally hosted API; no network mocks."""

import base64
import json
import time
from pathlib import Path
from urllib.request import urlopen

from websockets.sync.client import connect

from app.core.config import get_settings

with urlopen("http://127.0.0.1:9222/json", timeout=10) as response:
    pages = json.load(response)
page = next(p for p in pages if p.get("type") == "page")
connection = connect(page["webSocketDebuggerUrl"], open_timeout=10, legacy=True)
sequence = 0


def command(method, params=None):
    global sequence
    sequence += 1
    identifier = sequence
    connection.send(
        json.dumps({"id": identifier, "method": method, "params": params or {}})
    )
    while True:
        message = json.loads(connection.recv(timeout=30))
        if message.get("id") == identifier:
            if "error" in message:
                raise RuntimeError(f"CDP command failed: {method}")
            return message.get("result", {})


def evaluate(expression):
    result = command(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    if "exceptionDetails" in result:
        raise RuntimeError("Browser expression failed")
    return result.get("result", {}).get("value")


def wait(expression):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if evaluate(expression):
            return
        time.sleep(0.25)
    raise AssertionError("Browser condition did not become true")


def click(text, nav=False):
    selector = "nav button" if nav else "button"
    evaluate(
        f"Array.from(document.querySelectorAll({json.dumps(selector)})).find(b=>b.textContent.includes({json.dumps(text)})).click()"
    )


def key(value):
    evaluate("document.querySelector('input[type=password]').select()")
    command("Input.insertText", {"text": value})


def screenshot(name):
    result = command(
        "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}
    )
    Path("docs/screenshots").mkdir(parents=True, exist_ok=True)
    Path(f"docs/screenshots/{name}.png").write_bytes(base64.b64decode(result["data"]))


command("Page.navigate", {"url": "http://localhost:5173"})
wait("document.querySelector('h1')?.textContent==='Overview'")
wait("document.body.textContent.includes('90.0%')")
click("Pipelines", True)
wait("document.querySelector('input[type=password]')!==null")
key("invalid")
click("Run commerce pipeline")
wait("document.body.textContent.includes('Administrative API key required')")
key(get_settings().admin_api_key)
click("Run commerce pipeline")
wait("document.body.textContent.includes('Execution completed successfully')")
evaluate("document.querySelector('input[type=checkbox]').click()")
click("Run commerce pipeline")
wait("document.body.textContent.includes('Pipeline failed; consult incident history')")
click("Incidents", True)
wait(
    "Array.from(document.querySelectorAll('button')).some(b=>b.textContent.startsWith('Retry '))"
)
click("Retry ")
wait("document.body.textContent.includes('Execution completed successfully')")
wait("document.querySelector('tbody tr')?.textContent.includes('resolved')")
click("Data Quality", True)
wait("document.body.textContent.includes('Inspect quarantine')")
click("Inspect quarantine")
wait("document.body.textContent.includes('Quarantined originals')")
click("Datasets", True)
wait("document.body.textContent.includes('Atlas Data Operations')")
click("Analytics", True)
wait("document.body.textContent.includes('South')")
click("Overview", True)
wait("document.querySelector('path.recharts-area-curve')!==null")
screenshot("overview")
command(
    "Emulation.setDeviceMetricsOverride",
    {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
)
wait("document.documentElement.scrollWidth<=window.innerWidth")
screenshot("mobile-overview")
command("Page.bringToFront")
evaluate("document.querySelector('nav button').focus()")
command(
    "Input.dispatchKeyEvent",
    {
        "type": "keyDown",
        "key": "Tab",
        "code": "Tab",
        "windowsVirtualKeyCode": 9,
        "nativeVirtualKeyCode": 9,
    },
)
command(
    "Input.dispatchKeyEvent",
    {
        "type": "keyUp",
        "key": "Tab",
        "code": "Tab",
        "windowsVirtualKeyCode": 9,
        "nativeVirtualKeyCode": 9,
    },
)
assert evaluate(
    "['A','BUTTON','INPUT','SELECT'].includes(document.activeElement.tagName)"
)
command("Browser.close")
connection.close()
print(
    "Browser flow passed: auth error, pipeline, failure, incident retry, quarantine, catalog, analytics, chart, mobile and keyboard"
)
