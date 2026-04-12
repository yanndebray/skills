---
name: python-artifact
description: >
  Build browser-based Python artifacts using Pyodide (CPython compiled to WebAssembly).
  Use this skill whenever the user wants to run Python code in an artifact or web app,
  create an interactive Python REPL/playground, build a data science demo with numpy/pandas/scikit-learn/matplotlib
  that runs in the browser, or embed executable Python in an HTML or React artifact.
  Trigger on phrases like "Python in the browser", "run Python in artifact", "interactive Python",
  "Python playground", "Pyodide", or any request to make Python code runnable directly in the UI
  without a server. Also trigger when a data visualization or ML demo would benefit from
  live Python execution rather than static output.
---

# Python in Artifacts (Pyodide)

Run CPython 3.12 in browser artifacts via Pyodide (WebAssembly). No server needed.

## CDN

```
https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js
```

---

## Quickstart Pattern (React)

```jsx
import { useState, useRef, useEffect } from "react";

export default function PyRunner() {
  const [code, setCode] = useState('print("hello from Python!")');
  const [output, setOutput] = useState("");
  const [ready, setReady] = useState(false);
  const py = useRef(null);

  useEffect(() => {
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";
    s.onload = async () => {
      py.current = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
      });
      setReady(true);
    };
    document.head.appendChild(s);
  }, []);

  const run = async () => {
    py.current.runPython("import sys,io; sys.stdout=io.StringIO(); sys.stderr=io.StringIO()");
    try {
      await py.current.runPythonAsync(code);
      setOutput(py.current.runPython("sys.stdout.getvalue()") || "(no output)");
    } catch (e) {
      setOutput("Error: " + e.message);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const ta = e.target;
      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      setCode(code.substring(0, start) + "    " + code.substring(end));
      setTimeout(() => { ta.selectionStart = ta.selectionEnd = start + 4; }, 0);
    }
  };

  return (
    <div>
      <textarea value={code} onChange={e => setCode(e.target.value)}
        onKeyDown={handleKeyDown} rows={8} cols={60} />
      <br />
      <button onClick={run} disabled={!ready}>{ready ? "Run" : "Loading Python..."}</button>
      <pre>{output}</pre>
    </div>
  );
}
```

---

## Loading Pyodide (HTML artifact)

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>
<script>
async function init() {
  const pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
  });
  return pyodide;
}
</script>
```

---

## Running Code

```js
// Synchronous — simple expressions only
const result = pyodide.runPython(`2 + 2`);

// Async — always use for user code, imports, or package installs
const result = await pyodide.runPythonAsync(code);
```

**Rule**: Always use `runPythonAsync` for user-provided code or anything involving imports.

---

## Capturing stdout / stderr

Redirect **before** each run, read **after**:

```js
pyodide.runPython(`
import sys, io
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
`);

await pyodide.runPythonAsync(userCode);

const stdout = pyodide.runPython("sys.stdout.getvalue()");
const stderr = pyodide.runPython("sys.stderr.getvalue()");
```

---

## Installing Packages (micropip)

For pure-Python packages not bundled with Pyodide:

```js
await pyodide.loadPackage("micropip");
const micropip = pyodide.pyimport("micropip");
await micropip.install("some-pure-python-package");
```

**Note**: C-extension packages only work if pre-compiled for Pyodide. See built-in list below.

---

## Built-in Packages (no install needed)

numpy · scipy · pandas · matplotlib · scikit-learn · sympy · networkx · pillow · regex · pyyaml · sqlalchemy · beautifulsoup4 · html5lib · lxml · six · packaging · pyparsing

Full list: https://pyodide.org/en/stable/usage/packages-in-pyodide.html

---

## JS ↔ Python Data Exchange

```js
// JS → Python
pyodide.globals.set("my_data", [1, 2, 3]);
pyodide.runPython("print(my_data)");

// Python → JS
pyodide.runPython("result = [x**2 for x in range(10)]");
const result = pyodide.globals.get("result").toJs();
```

---

## Matplotlib (render as base64 image)

```python
import matplotlib.pyplot as plt
import io, base64

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
buf = io.BytesIO()
fig.savefig(buf, format="png")
buf.seek(0)
img_b64 = base64.b64encode(buf.read()).decode()
plt.close()
# Pass img_b64 to JS → set as <img src="data:image/png;base64,...">
```

In React, retrieve and display:
```js
const img = pyodide.globals.get("img_b64");
setPlotSrc(`data:image/png;base64,${img}`);
// <img src={plotSrc} />
```

---

## Key Gotchas & Rules

| # | Gotcha | Rule |
|---|--------|------|
| 1 | **~3–5s load time** | Always show a loading indicator; disable Run button until `ready` |
| 2 | **No filesystem persistence** | Files in Pyodide's virtual FS vanish on reload |
| 3 | **No threads** | `threading` is stubbed — use `asyncio` for concurrency |
| 4 | **No network** | `requests`/`urllib` don't work — use `pyodide.http.pyfetch()` |
| 5 | **C-extension packages** | Only pre-compiled Pyodide packages work; pure Python is fine via micropip |
| 6 | **Tab key in textarea** | Must intercept manually (see Tab handling pattern in quickstart) |

---

## Tab Key Handling (standalone)

```jsx
const handleKeyDown = (e) => {
  if (e.key === "Tab") {
    e.preventDefault();
    const ta = e.target;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    setCode(code.substring(0, start) + "    " + code.substring(end));
    setTimeout(() => { ta.selectionStart = ta.selectionEnd = start + 4; }, 0);
  }
};
```

---

## Checklist for Every Pyodide Artifact

- [ ] Script tag added via `useEffect` / `<script src="...">` pointing to CDN
- [ ] `loadPyodide({ indexURL: "..." })` called with explicit indexURL
- [ ] Loading state tracked; Run button disabled until ready
- [ ] stdout/stderr redirected before each run
- [ ] `runPythonAsync` used (not `runPython`) for user code
- [ ] Tab key intercepted in textarea
- [ ] Errors caught and displayed (not swallowed)
- [ ] `plt.close()` called after each matplotlib figure to free memory