class TaskRegistry:
    def __init__(self):
        self.handlers = {}

    def register(self, name: str):
        def decorator(function):
            self.handlers[name] = function
            return function
        return decorator
    def get(self, name: str):
        if name not in self.handlers:
            raise ValueError(f"Unkown task: {name}")
        return self.handlers[name]

registry = TaskRegistry()