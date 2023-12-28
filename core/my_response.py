from enum import Enum


class ResponseState(Enum):
    SUCCESS = 0
    WARNING = 1
    FAILURE = 2

class SimpleResponse:
    def __init__(self, state:ResponseState, content:str = None, data = None) -> None:
        self.state = state
        self.content = content
        self.data = data

    def __nonzero__(self):
        return self.state == ResponseState.SUCCESS