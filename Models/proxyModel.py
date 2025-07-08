from typing import Self
class ProxyModel:
    proxyAddress: str
    proxyPort: str
    proxyUser: str
    proxyPassword: str

    def __init__(self: Self, pAddress: str, pPort: str, pUser: str, pPassword: str):
        self.proxyAddress = pAddress
        self.proxyPort = pPort
        self.proxyUser = pUser
        self.proxyPassword = pPassword