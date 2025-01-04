from typing import Literal

from pydantic import BaseModel


class AquatonePage(BaseModel):
    """
    I definitely don't know everything that's in this. But I know what we need to parse, so...
    """

    hasScreenshot: bool
    url: str
    hostname: str
    screenshotPath: str


class AquatoneScreenshot(BaseModel):
    host: str
    port: int
    service: str
    data: str


class AquatoneSessionStats(BaseModel):
    screenshotSuccessful: int


class AquatoneSession(BaseModel):
    pages: dict[str, AquatonePage]
    stats: AquatoneSessionStats


class VNCScreenshot(BaseModel):
    host: str
    port: int
    service: Literal["VNC"] = "VNC"
    data: str
