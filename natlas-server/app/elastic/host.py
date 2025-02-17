from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

from elasticsearch_dsl import Document, InnerDoc, Ip, Keyword


class Service(InnerDoc):
    name: str = Keyword()
    product: str = Keyword()
    version: str = Keyword()
    ostype: str = Keyword()
    conf: int
    cpelist: str
    method: str
    extrainfo: str
    tunnel: str = Keyword()


class Script(InnerDoc):
    output: str


class SSLIssuer(InnerDoc):
    commonName: str = Keyword()
    countryName: str = Keyword()
    organizationName: str = Keyword()


class SSLPubkey(InnerDoc):
    bits: int
    key_type: str = Keyword(attr="type")


class SSLSubject(InnerDoc):
    altNames: list[str] = Keyword()
    commonName: str = Keyword()


class SSL(InnerDoc):
    issuer: SSLIssuer
    md5: str = Keyword()
    notAfter: datetime
    notBefore: datetime
    pem: str
    pubkey: SSLPubkey
    sha1: str = Keyword()
    sig_alg: str = Keyword()


class Port(InnerDoc):
    number: int
    protocol: str = Keyword()
    state: str = Keyword()
    reason: str
    banner: str
    service: Service
    scripts: list[Script]
    ssl: SSL


class Screenshot(InnerDoc):
    host: str = Keyword()
    port: int
    service: str = Keyword()
    full_hash: str = Keyword(attr="hash")
    thumb_hash: str = Keyword()


class Host(Document):
    ctime: datetime
    agent: str = Keyword()
    agent_version: str = Keyword()
    scan_reason: str = Keyword()
    scan_start: datetime
    scan_stop: datetime
    elapsed: int
    tags: list[str] = Keyword()
    port_count: int
    port_str: str
    is_up: bool
    ip: IPv4Address | IPv6Address = Ip()
    scan_id: str = Keyword()
    nmap_data: str
    xml_data: str
    gnmap_data: str

    class Index:
        name = "nmap"


class HostHistory(Host):
    """
    HostHistory is a dual-write where we id on the scan id rather than the IP address
    This lets us keep one "current" index for most operations but then access historical
    data pretty easily.
    """

    class Index:
        name = "nmap_history"
