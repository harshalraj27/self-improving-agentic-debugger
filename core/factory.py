from core.runners.cpp_runner import CPPRunner
from core.runners.python_runner import PyRunner
from core.runners.base import AbstractRunner

class RunnerFactory(object):
    @staticmethod
    def get_runner(file_path: str) -> AbstractRunner:
        if(file_path.endswith(".py")):
            return PyRunner(file_path)
        elif(file_path.endswith(".cpp")):
            return CPPRunner(file_path)
        else:
            raise ValueError(f"Unsupported file extension for: {file_path}")