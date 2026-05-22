from charts.bar import HBarChart, VBarChart
from charts.line import LineChart
from charts.scatter import ScatterChart
from charts.sparkline import sparkline

CHART_TYPES = {
    "bar": VBarChart,
    "hbar": HBarChart,
    "line": LineChart,
    "scatter": ScatterChart,
}
