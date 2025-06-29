from pyqtgraph import LinearRegionItem


class LinearRegion(LinearRegionItem):
    """Vertical linear region with fixed orientation."""

    def __init__(self, *args, **kwargs):
        kwargs.pop("orientation", None)
        super().__init__(*args, orientation="vertical", **kwargs)


class HLinearRegion(LinearRegionItem):
    """Horizontal linear region with fixed orientation."""

    def __init__(self, *args, **kwargs):
        kwargs.pop("orientation", None)
        super().__init__(*args, orientation="horizontal", **kwargs)

