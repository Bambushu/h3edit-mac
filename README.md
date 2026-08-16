# h3edit — local instruction-based image editing on MiniMax H3

H3 is a video model. It edits images by rendering **one frame** of R2V through a VAE retrained
for single images. Technique from Patient_Ratio4177, r/StableDiffusion `1vo1ab3` (2026-08-14);
ported to the M5 and measured 2026-08-16. Full findings: `~/henkwolf/recipe.md` §8.

```sh
h3edit "$(cat edit.txt)" -r photo.jpg -r logo.png -o out.png --wait
h3edit --doctor
```

## Install

```sh
uv tool install --force -e ~/h3edit
```

Needs **ComfyUI-h3 running on :8288** with the single-frame custom node installed (see below).
`h3edit --doctor` checks both.

## Defaults, and why they are what they are

| flag | default | why |
|---|---|---|
| `--steps` | 8 | 6 rendered the subject TWICE. n=1, so a warning rather than a proven floor |
| `--mp` | 2.0 | see below — this also sizes the references |
| `--ref-size` | `match` | `max` pins refs to a 2048px short edge: ~10x slower, no better |
| `--ar` | `21:9` | pass the one matching your source |

**Megapixels is the reference-resolution dial.** `match` scales references to the *generation's*
pixel area, so `--mp 1.0` squashed a 1024px wordmark to ~650px tall before H3 saw it and the
result came back airbrushed, with a halo bleeding onto the paint. 2.0 is clean.

⚠ **The 1.0 MP local H3 cap is a VIDEO rule** — there every pixel is multiplied by 124 frames.
One frame does not inherit it.

Measured on the M5 (2208x960, 2 refs): **7m30s**. The same edit with `--ref-size max` took
**72m48s** for no quality gain — sampling was only 8:44 of that, the rest was reference encode.

## Judging the result

**Look at the edited region at 100%, never the full frame.** A render that looks clean at reel
size can have deformed letterforms and a soft halo. `~/henkwolf/decal_check.py` crops the region
and stacks it under the reference; the 4m41s run passed on the thumbnail and is an obvious fail
at 100%.

## Prompt grammar

Editing is **not** our video R2V grammar. Video needs `<Subject N>` or wardrobe bleeds from the
reference; editing wants the bare `<Picture N>` anchor, because the image *is* the anchor.

The device that stops bleed is an explicit **negative role assignment**:

> `<Picture 2>` is the wordmark reference and supplies nothing else. It does not supply a scene,
> a background, a colour scheme, or lighting.

Then an exhaustive preserve list, then a closing sentence naming the output form. Say **one** of
a thing explicitly — "the front and rear doors … spanning both together" was read as one mark
per door. 11 worked examples in `prompts/reference_prompts.txt`.

## What it is not

**A regeneration conditioned on the reference, not a masked edit.** Scene, lighting, shadow
direction and background carry; fine trim and edges get redrawn. Good for mockups, wrong if the
result must composite against the untouched original.

## The graph

`api_graph.json` is the frontend's own `graphToPrompt()` output, exported once — **never
hand-written**. Only that path serializes H3's autogrow reference inputs as dotted
`ref_images.ref_image_N` keys; a hand-assembled graph drops them with no error and the render
silently ignores every reference. `h3edit` sets values in it and refuses to queue if those keys
are missing.

It is the established local R2V workflow (`h3_image_edit_mac.json`, itself `gcn_setprobe.json`
plus five edits) with Ref2VA GGUF + turbo LoRA + ClipProj, Spectrum bypassed, `sa_solver`.

To change the graph: load it in the GUI, edit there, then

```sh
H3EDIT_CDP=9223 h3edit --export <tab-id>
```

## The single-frame custom node

ComfyUI floors frame count in **two** places — `min=5` on the length widget and
`align_frame_count()`, which snaps anything under 5 back up to 5. So a naive `length=1` silently
renders 5 frames.

`custom_nodes/h3_single_frame/` rebinds the three module-level functions at import. Install it by
symlinking, once, and **restart ComfyUI**:

```sh
ln -s ~/h3edit/custom_nodes/h3_single_frame ~/ComfyUI-h3/custom_nodes/h3_single_frame
```

**This is deliberately not a patch to ComfyUI's source.** It was one, and every `git pull`
reverted it silently. `custom_nodes/` is gitignored in the ComfyUI checkout, so an upstream
update cannot touch it and the working tree stays clean. `h3_single_frame_min1.patch` is kept
only as the historical record of the same change — **do not apply it**.

⚠ `/object_info` still reports `length min = 5` even when the rebind is live: schemas are
serialized at registration, before custom nodes load. That is why `--doctor` asks for the
`H3SingleFrameEnabled` marker node instead. It does not matter in practice — `h3edit` drives
length through a linked `ComfyMathExpression`, and ComfyUI validates a link's type, not its
range.

⚠ Rendering 5 frames and keeping frame 0 is **not** a substitute: grid artifacts under the image
VAE, blur under the video VAE.

## Why not the author's own recipe

His is CUDA-only three times over: the `smhfacct` fl2va/ref2va hybrid checkpoint is
`int8_convrot` (no MPS path), the encoder is `nvfp4_awq`, and he runs comfy-kitchen attention
— ~8s per image on a 5090. The M5 port swaps in Ref2VA GGUF + turbo LoRA + ClipProj, all already
proven locally. It gives up the hybrid, which grafts ref2va's `adaln_proj` blocks onto fl2va's
higher-fidelity body; no GGUF equivalent exists.
