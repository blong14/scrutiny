from io import StringIO
from typing import List

import matplotlib.pyplot as plt
import networkx as nx


class DirectedGraph(StringIO):
    class Node(tuple):
        pass

    class Edge(tuple):
        pass

    model = nx.MultiDiGraph
    connectionstyle: str = "arc3, rad = 0.1"

    def __init__(self, *args, **kwargs):
        self.frmt = kwargs.pop("frmt", "svg")
        self.nodes: List[DirectedGraph.Node] = kwargs.pop("nodes", [])
        self.edges: List[DirectedGraph.Edge] = kwargs.pop("edges", [])
        self.G = self.model()
        super().__init__(*args, **kwargs)
        self.post_init()

    def post_init(self):
        self.G.add_nodes_from(self.nodes)
        self.G.add_edges_from(self.edges)

    def _render(self):
        fig = plt.figure(figsize=(4, 4))
        nx.draw(
            self.G,
            nx.get_node_attributes(self.G, "pos"),
            connectionstyle=self.connectionstyle,
        )
        fig.savefig(self, format=self.frmt)

    def getvalue(self) -> str:
        self._render()
        self.seek(0)
        return super().getvalue()
