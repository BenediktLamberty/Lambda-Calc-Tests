import os

def read_from_file(path: str) -> str:
    # print(os.getcwd())
    try:
        with open(path, "r") as file:
            return file.read()
    except IOError:
        with open(f"{lambdaInterpreter}inputs/{path}.lm", "r") as file:
            return file.read()

print(os.listdir(os.getcwd()))
print(read_from_file("bools"))