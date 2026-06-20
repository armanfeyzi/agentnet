class RateLimitExceeded(Exception):
    def __init__(self, detail: str, retry_after: int) -> None:
        self.detail = detail
        self.retry_after = max(1, retry_after)
        super().__init__(detail)
