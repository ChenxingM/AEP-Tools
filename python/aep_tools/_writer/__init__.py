"""Binary .aep writer — serialize chunk tree back to RIFX/RIFF format.

Supports modifying layer names and property values in-place on the chunk tree,
then writing the result to a new .aep file.
"""

from ._serialize import save_aep, serialize_chunk_tree
from ._navigate import (
    find_comp_chunklist, find_item_chunklist,
    find_layer_chunk, find_property_chunk,
)
from ._names import set_asset_path, set_comp_name, set_layer_name
from ._properties import (
    set_keyframe_ease, set_keyframe_interpolation,
    set_keyframe_time, set_keyframe_value,
    set_property_value,
)
from ._layer_fields import (
    set_layer_blend_mode, set_layer_flag, set_layer_label,
    set_layer_light_type, set_layer_preserve_transparency,
    set_layer_quality, set_layer_time_field, set_layer_track_matte,
)
from ._comp_fields import (
    set_comp_bgcolor, set_comp_dimensions, set_comp_display_start_time,
    set_comp_drop_frame, set_comp_duration, set_comp_flag,
    set_comp_framerate, set_comp_motion_blur_samples,
    set_comp_pixel_aspect, set_comp_shutter_angle, set_comp_shutter_phase,
    set_comp_work_area_end, set_comp_work_area_start,
)
from ._project_fields import (
    set_project_audio_sample_rate, set_project_bits_per_channel,
    set_project_compensate_scene_referred,
    set_project_linearize_working_space, set_project_working_gamma,
)

__all__ = [
    "save_aep", "serialize_chunk_tree",
    "find_comp_chunklist", "find_item_chunklist",
    "find_layer_chunk", "find_property_chunk",
    "set_asset_path", "set_comp_name", "set_layer_name",
    "set_keyframe_ease", "set_keyframe_interpolation",
    "set_keyframe_time", "set_keyframe_value",
    "set_property_value",
    "set_layer_blend_mode", "set_layer_flag", "set_layer_label",
    "set_layer_light_type", "set_layer_preserve_transparency",
    "set_layer_quality", "set_layer_time_field", "set_layer_track_matte",
    "set_comp_bgcolor", "set_comp_dimensions", "set_comp_display_start_time",
    "set_comp_drop_frame", "set_comp_duration", "set_comp_flag",
    "set_comp_framerate", "set_comp_motion_blur_samples",
    "set_comp_pixel_aspect", "set_comp_shutter_angle", "set_comp_shutter_phase",
    "set_comp_work_area_end", "set_comp_work_area_start",
    "set_project_audio_sample_rate", "set_project_bits_per_channel",
    "set_project_compensate_scene_referred",
    "set_project_linearize_working_space", "set_project_working_gamma",
]
