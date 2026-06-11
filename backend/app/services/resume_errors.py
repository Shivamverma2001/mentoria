class ResumeParseError(Exception):
    def __init__(self, message: str, code: str = "invalid_resume") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ResumeEmbeddingError(Exception):
    def __init__(self, message: str, code: str = "embedding_failed") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
