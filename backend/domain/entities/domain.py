import uuid


class Domain:
    def __init__(self, id: uuid.UUID, name: str):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Domain(id={self.id}, name={self.name})"
