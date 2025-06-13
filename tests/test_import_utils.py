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

