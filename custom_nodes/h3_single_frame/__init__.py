"""Let MiniMax H3 render a SINGLE frame, without patching ComfyUI's own source.

H3 edits images by rendering one frame of R2V (see ~/h3edit). ComfyUI floors that in two
places -- `min=5` on the length widget, and align_frame_count(), which snaps anything below 5
back up to 5 -- so a naive `length=1` silently renders 5 frames, and the single-image VAE puts
grid artifacts on the result.

This used to be a patch applied to comfy_extras/nodes_minimax_h3.py, which every `git pull`
silently reverted. Rebinding the three module-level functions from a custom node instead means
the repo working tree stays clean and there is nothing for a pull to undo. The functions are
looked up on the module at call time, so rebinding after import takes effect.

Registers H3SingleFrameEnabled purely as a liveness marker: `/object_info/H3SingleFrameEnabled`
returning 200 proves the rebind ran in the RUNNING process, which is what `h3edit --doctor`
asks. It is not meant to be wired into a graph.
"""
from comfy_extras import nodes_minimax_h3 as h3

_FPS = 24
_AUDIO_LATENT_FPS = 40


def align_frame_count(n):
    if n <= 1:
        return 1
    while n % 17 != 5:
        n += 1
    return n


def video_latent_t(frame_count):
    if frame_count <= 1:
        return 1
    return 2 if frame_count <= 5 else ((frame_count - 5) // 17) * 5 + 2


def temporal_shape(length):
    frame_count = align_frame_count(max(1, length))
    duration = frame_count / _FPS
    return frame_count, video_latent_t(frame_count), round(duration * _AUDIO_LATENT_FPS)


h3.align_frame_count = align_frame_count
h3.video_latent_t = video_latent_t
h3.temporal_shape = temporal_shape

# NOT patched: the `min=5` on the length widget. /object_info still advertises it, but ComfyUI
# does not enforce widget minimums when a graph is submitted to /prompt -- a literal length=1 is
# accepted (measured). The floor only clamps the slider in the GUI. Two earlier attempts to relax
# it here were dead code that logged success while changing nothing.
print("[h3_single_frame] one-frame H3 enabled (align_frame_count / video_latent_t / temporal_shape)")


class H3SingleFrameEnabled:
    """Liveness marker for h3edit --doctor. Not for use in a graph."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "noop"
    CATEGORY = "MiniMaxH3"

    def noop(self):
        return ()


NODE_CLASS_MAPPINGS = {"H3SingleFrameEnabled": H3SingleFrameEnabled}
NODE_DISPLAY_NAME_MAPPINGS = {"H3SingleFrameEnabled": "H3 single-frame patch active"}
