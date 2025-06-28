import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import GraphData


def test_satellite_dicts_are_instance_specific():
    g1 = GraphData("g1")
    g2 = GraphData("g2")

    g1.satellite_settings["left"].visible = True
    g1.satellite_content["right"] = "label"
    assert g2.satellite_settings["left"].visible is False
    assert g2.satellite_content["right"] is None
