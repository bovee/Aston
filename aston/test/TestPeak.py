import pytest
import numpy as np
from aston.trace.Trace import AstonSeries
from aston.peaks.Peak import Peak, PeakComponent


@pytest.fixture(params=['box'])
def peak(request):
    peak_name = request.param
    if peak_name == 'box':
        info = {}
        trace = AstonSeries(np.arange(10), np.ones(10), name=1)
        baseline = AstonSeries([0, 9], [0, 0], name=1)

    return Peak(peak_name, components=PeakComponent(info, trace, baseline))


def test_area(peak):
    assert peak.area() == peak.area(1)
