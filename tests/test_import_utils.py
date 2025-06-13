import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from IO_dossier.import_utils import import_curves_from_csv


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


