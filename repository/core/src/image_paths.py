"""Path-only development-image validation; import and validation never read pixels.

Do not resolve away a symlink before checking its original path components.
The caller remains responsible for image decoding/dimensions and read-time hashes.
"""
from __future__ import annotations

import os
from pathlib import Path
import stat

SEQUENCES = ("MOT20-01", "MOT20-02")
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _checked_lstat(path: Path):
    """Reject every symlink and Windows reparse point, including junctions."""
    try:
        result = path.lstat()
    except OSError as error:
        raise ValueError("Missing or inaccessible image path component: " + str(path)) from error
    attributes = getattr(result, "st_file_attributes", 0)
    if stat.S_ISLNK(result.st_mode) or attributes & _REPARSE_POINT:
        raise ValueError("Redirected image path component is prohibited: " + str(path))
    return result


def _unredirected(path: Path, *, directory: bool) -> Path:
    """Check original absolute components before and after canonical resolution."""
    components = list(reversed(path.parents)) + [path]
    for index, component in enumerate(components):
        result = _checked_lstat(component)
        is_last = index == len(components) - 1
        if (not is_last or directory) and not stat.S_ISDIR(result.st_mode):
            raise ValueError("Expected an image-directory component: " + str(component))
        if is_last and not directory and not stat.S_ISREG(result.st_mode):
            raise ValueError("Expected a regular image file: " + str(component))
    try:
        canonical = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError("Cannot resolve image path: " + str(path)) from error
    if canonical != path:
        raise ValueError("Canonical image path differs from requested path: " + str(path))
    # Recheck rather than trusting a prior directory/file metadata observation.
    for component in components:
        _checked_lstat(component)
    return canonical


def resolve_image_inputs(image_dir, sequence, frames):
    """Return ``(canonical_img1_directory, frame_paths)`` in requested frame order.

    Only MOT20-01/02's exact ``SEQUENCE/img1`` tail is accepted. Every original
    path component and every requested ``NNNNNN.jpg`` must exist without any
    symlink/junction/reparse redirection, even to a different frame in the same
    directory. No repair, frame substitution, sorting, pixel I/O or GT I/O occurs.

    This verifies path identity at the time of the call. It is not an atomic
    no-follow file opener and cannot authenticate the pixels or prevent a later
    filesystem mutation between validation and the caller's read.
    """
    if sequence not in SEQUENCES:
        raise ValueError("Only MOT20-01 and MOT20-02 image inputs are allowed")
    try:
        supplied = Path(image_dir)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid image directory path") from error
    if ".." in supplied.parts:
        raise ValueError("Parent traversal is not allowed for image inputs")
    if supplied.name != "img1" or supplied.parent.name != sequence:
        raise ValueError("Give exactly the selected development sequence/img1 directory")
    # abspath retains symlink/junction components; Path.resolve() here would not.
    absolute = Path(os.path.abspath(os.fspath(supplied)))
    canonical_dir = _unredirected(absolute, directory=True)
    if canonical_dir.name != "img1" or canonical_dir.parent.name != sequence:
        raise ValueError("Canonical directory does not identify the requested sequence")
    try:
        requested_frames = list(frames)
    except TypeError as error:
        raise ValueError("Frames must be an iterable of positive integer frame numbers") from error
    if not requested_frames or any(type(frame) is not int or frame <= 0 for frame in requested_frames):
        raise ValueError("Frames must be nonempty positive integers, not booleans or floats")
    paths = []
    for frame in requested_frames:
        filename = f"{frame:06d}.jpg"
        candidate = absolute / filename
        canonical = _unredirected(candidate, directory=False)
        if canonical.parent != canonical_dir or canonical.name != filename:
            raise ValueError("Resolved image is not the requested frame: " + filename)
        paths.append(canonical)
    return canonical_dir, paths
