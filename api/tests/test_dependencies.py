from importlib.metadata import version


def _as_version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split(".")[:3])


def test_urllib3_includes_cve_fixes() -> None:
    assert _as_version_tuple(version("urllib3")) >= (2, 6, 3)


def test_python_multipart_includes_cve_fix() -> None:
    assert _as_version_tuple(version("python-multipart")) >= (0, 0, 26)
