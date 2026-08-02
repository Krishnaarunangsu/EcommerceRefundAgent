from src.agent.engine import Engine


class Car:
    def __init__(self):
        # Create an instance of Engine inside Car
        self.engine = Engine()

    def drive(self):
        # Call the Engine's method using the instance
        status = self.engine.start()
        print(f"Starting car: {status}")