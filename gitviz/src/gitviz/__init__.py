"""GitViz - Interactive Terminal UI Git History Visualizer."""

__version__ = "1.0.0"

from .models import Commit, Actor, Repository, Branch
from .parser import RepositoryLoader, CommitParser
from .graph import GraphLayout, ASCIIRenderer
from .ui import GitVizApp
