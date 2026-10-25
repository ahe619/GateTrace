"""Verbatim frozen event_view of scripts/sota83d/event_view.py (no imports in the source).
Software notice in LICENSE_CODE.
"""


def event_view(output, frame):
    assert type(frame) is int and frame >= 0
    view = dict(output)
    if view.get('raw_detection_index', 'absent') is None:
        del view['raw_detection_index']
    view.update(frame=frame, source_frame=frame+1, time_s=frame/25)
    return view
