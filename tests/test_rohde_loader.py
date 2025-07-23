import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from IO_dossier import curve_loader_factory as clf


def test_load_rohde_schwarz_bin(monkeypatch):
    def fake_read(path):
        y = np.array([[[1, 10]], [[2, 20]], [[3, 30]]], dtype=np.float32)
        x = np.array([0.0, 0.5, 1.0])
        return y, x, {}

    monkeypatch.setattr(clf, "RTxReadBin", fake_read)
    curves = clf.load_rohde_schwarz_bin("dummy")
    assert len(curves) == 2
    assert np.array_equal(curves[0].y, np.array([1, 2, 3], dtype=np.float32))
    assert np.array_equal(curves[1].y, np.array([10, 20, 30], dtype=np.float32))
    assert np.array_equal(curves[0].x, np.array([0.0, 0.5, 1.0]))
