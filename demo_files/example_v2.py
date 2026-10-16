"""A small file to use for the Time Capsule demo."""

APP_NAME = "Time Capsule"
VERSION = "1.1"


def greet(name):
    if not name.strip():
        raise ValueError("Name cannot be empty")
    return f"Hello, {name}! Welcome back."


if __name__ == "__main__":
    print(greet("Sai"))
