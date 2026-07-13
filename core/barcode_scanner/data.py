from pydantic import BaseModel, ConfigDict, Field

from libs.serial_port import SerialPortConfig


class ScannerParams(BaseModel):
    """Serial line settings and barcode suffix for a scanner emulator."""

    model_config = ConfigDict(strict=True)

    baud_rate: int = 9600
    bytesize: int = 8
    parity: str = 'N'
    stopbits: float = 1
    suffix: str = Field(default='\r\n')


class ScannerConfig(BaseModel):
    """Persisted configuration of one barcode scanner widget."""

    model_config = ConfigDict(strict=True)

    name: str
    port_name: str
    config: ScannerParams

    def to_serial_port_config(self) -> SerialPortConfig:
        """Build COM-port settings for ``ScannerEmul`` from this widget config.

        Returns:
            ``SerialPortConfig`` with ``port_name`` and line parameters from ``config``.
        """
        return SerialPortConfig(
            port_name=self.port_name,
            baud_rate=self.config.baud_rate,
            bytesize=self.config.bytesize,
            parity=self.config.parity,
            stopbits=self.config.stopbits,
            suffix=self.config.suffix,
        )
