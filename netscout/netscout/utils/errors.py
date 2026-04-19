class NetworkScoutError(Exception):
    pass


class PermissionError(NetworkScoutError):
    pass


class NetworkError(NetworkScoutError):
    pass


class InvalidSubnetError(NetworkScoutError):
    pass


class ScanTimeoutError(NetworkScoutError):
    pass
