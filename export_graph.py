#!/usr/bin/env python3
"""Re-export api_graph.json from a live ComfyUI tab via CDP.

The frontend's graphToPrompt() is the ONLY thing that serializes H3's autogrow reference inputs
as dotted `ref_images.ref_image_N` keys. Hand-assembled graphs drop them without an error and
the render silently ignores every reference. So the graph is exported, never written.

Load the edit workflow in the GUI first, wire it how you want, then:

    H3EDIT_CDP=9223 h3edit --export <tab-id>
"""
import json, os, time

import websocket


def export(tab, dest):
    cdp = os.environ.get("H3EDIT_CDP", "9223")
    ws = websocket.create_connection(f"ws://localhost:{cdp}/devtools/page/{tab}",
                                     timeout=120, suppress_origin=True)
    n = [0]

    def js(expr):
        n[0] += 1
        ws.send(json.dumps({"id": n[0], "method": "Runtime.evaluate", "params": {
            "expression": expr, "returnByValue": True, "replMode": True}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == n[0]:
                res = r.get("result", {})
                if "exceptionDetails" in res:
                    raise RuntimeError(json.dumps(res["exceptionDetails"])[:400])
                return res.get("result", {}).get("value")

    # graphToPrompt's output does not survive returnByValue directly -- stringify it onto a
    # global and read that back, the same shape the proven local driver uses.
    js("window.__G__=null; (async()=>{const p=await window.app.graphToPrompt();"
       " window.__G__=JSON.stringify(p.output);})(); 'go'")
    raw = None
    for _ in range(60):
        time.sleep(0.5)
        raw = js("window.__G__")
        if raw:
            break
    if not raw:
        raise SystemExit("graphToPrompt never returned; is the workflow loaded in that tab?")

    g = json.loads(raw)
    r2v = next((v for v in g.values() if "ReferenceToVideo" in v["class_type"]), None)
    if r2v is None:
        raise SystemExit("no MiniMaxH3ReferenceToVideo in that graph")
    refs = [k for k in r2v["inputs"] if k.startswith("ref_images.")]
    if not refs:
        raise SystemExit("exported graph has no dotted ref_images keys -- refusing to save it")
    # An output node that is not the image save writes files nobody asked for (the Motion Context
    # latent chain, a video). Keep the graph to what an image edit needs.
    for nid in [k for k, v in g.items() if v["class_type"].endswith("SaveLatent")]:
        del g[nid]
    json.dump(g, open(dest, "w"), indent=1)
    print(f"{dest}: {len(g)} nodes, refs {refs}")
    ws.close()
