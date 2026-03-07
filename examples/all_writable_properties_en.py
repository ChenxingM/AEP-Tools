"""Complete example showing all writable properties in aep_tools.

Usage:
    python examples/all_writable_properties_en.py input.aep output.aep
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import (
    Project, CompItem, Layer, AVLayer, LightLayer,
    BlendingMode, TrackMatteType, LayerQuality, KeyframeInterpolationType,
)


def main():
    if len(sys.argv) < 3:
        print("Usage: python examples/all_writable_properties_en.py input.aep output.aep")
        sys.exit(1)

    proj = Project.open(sys.argv[1])  # open .aep file, returns Project object

    # ================================================================
    # 1. Project-level properties (project settings)
    # ================================================================

    proj.bits_per_channel = 16          # color depth: 8, 16, or 32
    proj.working_gamma = 2.2            # working gamma value
    proj.linearize_working_space = True # linearize working color space
    proj.compensate_scene_referred = False  # compensate for scene-referred profiles
    proj.audio_sample_rate = 48000.0    # audio sample rate (Hz)

    # ================================================================
    # 2. CompItem-level properties (composition settings)
    # ================================================================

    comp = proj.comp(1)  # get comp by 1-based index; also proj.comp("Comp Name")

    # --- Basic properties ---
    comp.name = "My Composition"        # composition name
    comp.width = 1920                   # width (pixels)
    comp.height = 1080                  # height (pixels)
    comp.frame_rate = 30.0              # frame rate (fps)
    comp.duration = 10.0                # duration (seconds)
    comp.bg_color = [0, 0, 0]           # background color [R, G, B] 0-255
    comp.pixel_aspect = 1.0             # pixel aspect ratio
    comp.display_start_time = 0.0       # display start time (seconds)

    # --- Work area ---
    comp.work_area_start = 1.0          # work area start (seconds)
    comp.work_area_duration = 5.0       # work area duration (seconds)

    # --- Comp switches ---
    comp.draft3d = False                # draft 3D mode
    comp.motion_blur = True             # enable motion blur
    comp.frame_blending = True          # enable frame blending
    comp.hide_shy_layers = False        # hide shy layers
    comp.preserve_nested_resolution = True   # preserve nested comp resolution
    comp.preserve_nested_frame_rate = False  # preserve nested comp frame rate
    comp.drop_frame = False             # drop frame timecode

    # --- Shutter / motion blur parameters ---
    comp.shutter_angle = 180            # shutter angle (degrees)
    comp.shutter_phase = -90            # shutter phase (degrees)
    comp.motion_blur_samples_per_frame = 16      # motion blur samples per frame
    comp.motion_blur_adaptive_sample_limit = 128 # adaptive sample limit

    # ================================================================
    # 3. Layer-level properties (layer settings)
    # ================================================================

    layer = comp.layer(1)  # get layer by 1-based index; also comp.layer("Layer Name")

    # --- Name ---
    layer.name = "My Layer"             # layer name

    # --- Visibility switches ---
    layer.enabled = True                # visible (eye icon)
    layer.solo = False                  # solo
    layer.shy = False                   # shy
    layer.locked = False                # locked

    # --- Layer type switches ---
    layer.three_d_layer = True          # 3D layer (note: False->True requires 3-component properties)
    layer.guide_layer = False           # guide layer
    layer.adjustment_layer = False      # adjustment layer
    layer.null_layer = False            # null object layer
    layer.environment_layer = False     # environment layer

    # --- Render switches ---
    layer.effects_active = True         # effects enabled
    layer.motion_blur = True            # motion blur
    layer.collapse_transformation = False  # collapse transformations / continuously rasterize
    layer.auto_orient = False           # auto-orient
    layer.sampling_quality = True       # bicubic sampling
    layer.frame_blending = True         # frame blending
    layer.frame_blending_type = 1       # frame blending type: 0=Frame Mix, 1=Pixel Motion
    layer.audio_enabled = True          # audio enabled
    layer.preserve_transparency = False # preserve transparency

    # --- Blending / matte / quality ---
    layer.blending_mode = BlendingMode.NORMAL       # blending mode (enum or int)
    layer.track_matte_type = TrackMatteType.NONE    # track matte type
    layer.quality = LayerQuality.BEST               # quality: WIREFRAME=0, DRAFT=1, BEST=2
    layer.label = 1                                 # label color index (0-16)

    # --- Timing ---
    layer.in_point = 0.0                # in point (seconds)
    layer.out_point = 10.0              # out point (seconds)
    layer.start_time = 0.0              # start time (seconds)
    layer.stretch = 1.0                 # time stretch (1.0 = 100%)

    # --- LightLayer only ---
    for lyr in comp.layers:
        if isinstance(lyr, LightLayer):
            lyr.light_type = 2          # light type: 0=Parallel, 1=Spot, 2=Point, 3=Ambient
            break

    # ================================================================
    # 4. Property-level (property values / keyframes)
    # ================================================================

    # --- Static property values ---
    if layer.position is not None:
        layer.position.value = [960.0, 540.0, 0.0]  # position [X, Y, Z]
    if layer.scale is not None:
        layer.scale.value = [1.0, 1.0, 1.0]         # scale [X, Y, Z] (1.0 = 100%)
    if layer.rotation is not None:
        layer.rotation.value = 0.0                   # Z rotation (degrees)
    if layer.opacity is not None:
        layer.opacity.value = 1.0                    # opacity (0.0-1.0)
    if layer.anchor_point is not None:
        layer.anchor_point.value = [960.0, 540.0, 0.0]  # anchor point

    # When dimensions are separated:
    if layer.position_x is not None:
        layer.position_x.value = 960.0               # X position
    if layer.position_y is not None:
        layer.position_y.value = 540.0               # Y position
    if layer.position_z is not None:
        layer.position_z.value = 0.0                 # Z position

    # 3D rotation:
    if layer.rotation_x is not None:
        layer.rotation_x.value = 0.0                 # X rotation
    if layer.rotation_y is not None:
        layer.rotation_y.value = 0.0                 # Y rotation

    # Access any property via match name path:
    # layer.property("ADBE Transform Group").property("ADBE Opacity").value = 0.5

    # --- Keyframe values ---
    prop = layer.position  # pick a property with keyframes
    if prop is not None and prop.num_keys > 0:
        # Set value by index (1-based)
        prop.set_value_at_key(1, [100.0, 200.0, 0.0])

        # Set value by time (finds nearest keyframe)
        prop.set_value_at_time(2.0, [500.0, 300.0, 0.0])

        # Set interpolation type
        prop.set_interpolation_type_at_key(
            1,
            in_type=KeyframeInterpolationType.BEZIER,   # in: LINEAR=1, BEZIER=2, HOLD=3
            out_type=KeyframeInterpolationType.BEZIER,   # out
        )

        # Set temporal ease
        prop.set_temporal_ease_at_key(
            1,
            in_ease=[{"speed": 0.0, "influence": 16.67}],   # incoming ease
            out_ease=[{"speed": 100.0, "influence": 33.33}], # outgoing ease
        )

    # ================================================================
    # 5. FootageItem (footage file path)
    # ================================================================

    for i in range(1, proj.num_items + 1):
        item = proj.item(i)
        if hasattr(item, 'file') and item.file is not None:
            item.file = "/new/path/to/footage.mov"  # change footage file path
            break

    # ================================================================
    # 6. Save
    # ================================================================

    proj.save(sys.argv[2])  # save as new file; proj.save() overwrites original
    print(f"Saved: {sys.argv[2]}")


if __name__ == "__main__":
    main()
