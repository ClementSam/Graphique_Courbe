import numpy as np

from IO_dossier.import_utils import import_curves_from_csv, TimeMode, suggest_dtype
from core.models import DataType


def test_import_curves_from_csv(tmp_path):
    csv_content = "x,a,b\n0,1,2\n1,3,4\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path))
    assert len(curves) == 2
    assert curves[0].name == "a"
    assert np.array_equal(curves[0].x, np.array([0,1]))
    assert np.array_equal(curves[0].y, np.array([1,3]))
    assert curves[1].name == "b"


def test_import_curves_from_csv_with_non_numeric(tmp_path):
    """Values that are not numeric should be converted to NaN."""
    csv_content = "x,a\n0,1\nfoo,3\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path))

    assert len(curves) == 1
    assert np.isnan(curves[0].x[1])
    assert curves[0].y[1] == 3


def test_import_curves_from_csv_custom_separator(tmp_path):
    csv_content = "x;a;b\n0;1;2\n1;3;4\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path), sep=";")

    assert len(curves) == 2
    assert curves[0].name == "a"
    assert np.array_equal(curves[0].x, np.array([0, 1]))
    assert np.array_equal(curves[0].y, np.array([1, 3]))


def test_import_curves_from_csv_decimal_comma(tmp_path):
    csv_content = "x;a;b\n0,5;1,2;2,2\n1,5;3,3;4,4\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path), sep=";")

    assert len(curves) == 2
    assert np.allclose(curves[0].x, np.array([0.5, 1.5]))
    assert np.allclose(curves[0].y, np.array([1.2, 3.3]))


def test_import_curves_with_index_mode(tmp_path):
    csv_content = "a,b\n1,2\n3,4\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path), mode=TimeMode.INDEX)

    assert len(curves) == 2
    assert np.array_equal(curves[0].x, np.array([0, 1]))


def test_import_curves_timestamp_relative(tmp_path):
    csv_content = "t,a\n2025-06-07 T08:38:59,1\n2025-06-07 T08:39:00,2\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path), mode=TimeMode.TIMESTAMP_RELATIVE)

    assert np.array_equal(curves[0].x, np.array([0.0, 1.0]))


def test_import_curves_timestamp_absolute(tmp_path):
    csv_content = "t,a\n2025-06-07 T08:38:59,1\n2025-06-07 T08:39:00,2\n"
    path = tmp_path / "data.csv"
    path.write_text(csv_content)

    curves = import_curves_from_csv(str(path), mode=TimeMode.TIMESTAMP_ABSOLUTE)

    assert curves[0].x[1] - curves[0].x[0] == 1.0



def test_suggest_dtype_integer_range():
    arr = [0, 10, 255]
    assert suggest_dtype(arr) == DataType.UINT8
    arr = [0, 50000]
    assert suggest_dtype(arr) == DataType.UINT16
    arr = [0, 70000, 4294967295]
    assert suggest_dtype(arr) == DataType.UINT32
    arr = [-1, 0]
    assert suggest_dtype(arr) == DataType.FLOAT64
