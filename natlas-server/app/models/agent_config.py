from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase
from app.models.dict_serializable import DictSerializable


class AgentConfig(NatlasBase, DictSerializable):
    __tablename__ = "agent_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    versionDetection: Mapped[bool] = mapped_column(
        default=True
    )  # Enable Version Detection (-sV)
    osDetection: Mapped[bool] = mapped_column(default=True)  # Enable OS Detection (-O)
    enableScripts: Mapped[bool] = mapped_column(
        default=True
    )  # Enable Nmap Scripting Engine (loads all AgentScripts)
    onlyOpens: Mapped[bool] = mapped_column(
        default=True
    )  # Only report open ports (--open)
    scanTimeout: Mapped[int] = mapped_column(
        default=60
    )  # SIGKILL nmap if it's running longer than this
    webScreenshots: Mapped[bool] = mapped_column(
        default=True
    )  # Attempt to take web screenshots (aquatone)
    vncScreenshots: Mapped[bool] = mapped_column(
        default=True
    )  # Attempt to take VNC screenshots (xvfb+vncsnapshot)
    webScreenshotTimeout: Mapped[int] = mapped_column(
        default=60
    )  # aquatone process timeout in seconds
    vncScreenshotTimeout: Mapped[int] = mapped_column(
        default=60
    )  # vnc process timeout in seconds
    scriptTimeout: Mapped[int] = mapped_column(default=60)  # --script-timeout (s)
    hostTimeout: Mapped[int] = mapped_column(default=600)  # --host-timeout (s)
    osScanLimit: Mapped[bool] = mapped_column(default=True)  # --osscan-limit
    noPing: Mapped[bool] = mapped_column(default=False)  # -Pn
    udpScan: Mapped[bool] = mapped_column(default=False)  # -sSU
