class ProxyModel:
    proxyAddress: str
    proxyPort: int
    proxyUser: str
    proxyPassword: str

    def __init__(self, pAddress, pPort, pUser, pPassword):
        self.proxyAddress = pAddress
        self.proxyPort = pPort
        self.proxyUser = pUser
        self.proxyPassword = pPassword