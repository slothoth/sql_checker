class GraphModel:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def to_dict(self):
        return {"nodes": self.nodes, "edges": self.edges}

    def from_dict(self, data):
        self.nodes = data.get("nodes", [])
        self.edges = data.get("edges", [])