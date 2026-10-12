"""Discover the Raspberry Pi header GPIO controller and select gpiozero's backend.

This adapter deliberately imports gpiozero and lgpio only when initialization is
requested. Discovery reads chip and line metadata; it never claims GPIO lines.
"""

from __future__ import annotations

import logging
import os
import stat
from dataclasses import dataclass
from typing import Optional


_LOGGER = logging.getLogger(__name__)
_REQUIRED_OFFSETS = (5, 6, 13, 17, 18, 19, 24, 25)


@dataclass(frozen=True)
class GpioControllerMetadata:
    """Immutable identity and verified header-line mapping for one GPIO chip."""

    device: str
    index: int
    label: str
    lines: tuple[tuple[int, str], ...]


class RaspberryPiGpioService:
    """Select an explicit lgpio factory for the supported Raspberry Pi path."""

    @staticmethod
    def _fail(message: str, cause: Optional[Exception] = None) -> None:
        _LOGGER.error("Raspberry Pi GPIO initialization failed: %s", message)
        error = RuntimeError(message)
        if cause is None:
            raise error
        raise error from cause

    @staticmethod
    def _is_raspberry_pi() -> bool:
        """Use the vendor's Raspberry marker; generic ARM systems are not enough."""
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
                contents = cpuinfo.read()
        except OSError as exc:
            RaspberryPiGpioService._fail(
                f"cannot identify the platform from /proc/cpuinfo: {exc}", exc
            )
        return "Raspberry" in contents

    @staticmethod
    def _chip_index(device: str) -> Optional[int]:
        suffix = device.removeprefix("/dev/gpiochip")
        if not suffix or not suffix.isdecimal():
            return None
        return int(suffix)

    def discover_controller(self) -> GpioControllerMetadata:
        """Find the sole chip with all required BCM names at matching offsets."""
        try:
            import lgpio
        except Exception as exc:
            self._fail(
                "lgpio metadata support is unavailable; install the Raspberry Pi "
                f"requirements including lgpio: {exc}",
                exc,
            )

        candidates: list[tuple[int, str]] = []
        diagnostics: list[str] = []
        failures: list[str] = []
        try:
            with os.scandir("/dev") as entries:
                device_entries = [
                    entry
                    for entry in entries
                    if entry.name.startswith("gpiochip")
                ]
        except OSError as exc:
            self._fail(f"cannot enumerate /dev GPIO devices: {exc}", exc)

        for entry in device_entries:
            path = os.path.join("/dev", entry.name)
            index = self._chip_index(path)
            if index is None:
                diagnostics.append(f"{path}: ignored non-numeric device name")
                continue
            try:
                mode = entry.stat().st_mode
            except OSError as exc:
                failures.append(f"{path}: cannot inspect device entry: {exc}")
                continue
            if not stat.S_ISCHR(mode):
                diagnostics.append(f"{path}: ignored non-character entry")
                continue
            candidates.append((index, path))

        matches: list[GpioControllerMetadata] = []
        for index, path in sorted(candidates):
            handle = None
            identity = f"{path} (chip {index})"
            try:
                opened_handle = lgpio.gpiochip_open(index)
                if opened_handle < 0:
                    raise RuntimeError(
                        f"chip open returned error handle {opened_handle}"
                    )
                handle = opened_handle
                chip_info = lgpio.gpio_get_chip_info(handle)
                if chip_info[0] < 0:
                    raise RuntimeError(
                        f"chip metadata query returned error status {chip_info[0]}"
                    )
                _status, line_count, _name, label = chip_info
                identity += f", label {label!r}, {line_count} lines"
                if line_count < max(_REQUIRED_OFFSETS) + 1:
                    diagnostics.append(f"{identity}: nonmatch, too few lines")
                    continue

                verified: list[tuple[int, str]] = []
                for offset in _REQUIRED_OFFSETS:
                    line_info = lgpio.gpio_get_line_info(handle, offset)
                    if line_info[0] < 0:
                        raise RuntimeError(
                            f"line metadata query for offset {offset} returned "
                            f"error status {line_info[0]}"
                        )
                    line_name = line_info[3]
                    verified.append((offset, line_name))
                if all(name == f"GPIO{offset}" for offset, name in verified):
                    matches.append(
                        GpioControllerMetadata(
                            device=path,
                            index=index,
                            label=label,
                            lines=tuple(verified),
                        )
                    )
                    diagnostics.append(f"{identity}: exact required mapping")
                else:
                    details = ", ".join(
                        f"{offset}={name!r}" for offset, name in verified
                    )
                    diagnostics.append(f"{identity}: nonmatch, observed {details}")
            except Exception as exc:
                failures.append(f"{identity}: metadata/open query failed: {exc}")
            finally:
                if handle is not None:
                    try:
                        close_status = lgpio.gpiochip_close(handle)
                        if close_status < 0:
                            failures.append(
                                f"{identity}: metadata handle close returned "
                                f"error status {close_status}"
                            )
                    except Exception as exc:
                        failures.append(f"{identity}: could not close metadata handle: {exc}")

        inspected = "; ".join(diagnostics + failures) or (
            "no numeric GPIO character devices found"
        )
        if failures:
            self._fail(
                "discovery is inconclusive; refusing to select a partial result. "
                f"Inspected devices: {inspected}"
            )
        if not matches:
            self._fail(
                "no controller exposes the required exact BCM line names and offsets "
                f"({_REQUIRED_OFFSETS}). Inspected devices: {inspected}"
            )
        if len(matches) != 1:
            self._fail(
                f"multiple controllers match the required header mapping: "
                f"{', '.join(f'{item.device} ({item.label})' for item in matches)}. "
                f"Inspected devices: {inspected}"
            )
        return matches[0]

    def configure_factory(self, result: GpioControllerMetadata):
        """Install or reuse gpiozero's process-lifetime factory for this chip."""
        configured_backend = os.environ.get("GPIOZERO_PIN_FACTORY")
        if configured_backend is not None and configured_backend != "lgpio":
            self._fail(
                "GPIOZERO_PIN_FACTORY is explicitly set to "
                f"{configured_backend!r}; Raspberry Pi ePaper requires 'lgpio'. "
                "Unset the variable or set it to 'lgpio'."
            )

        try:
            from gpiozero import Device
            from gpiozero.pins.lgpio import LGPIOFactory
        except Exception as exc:
            self._fail(
                "gpiozero/lgpio backend is unavailable; install the Raspberry Pi "
                f"requirements including lgpio: {exc}",
                exc,
            )

        current_factory = Device.pin_factory
        if current_factory is not None:
            if isinstance(current_factory, LGPIOFactory) and getattr(
                current_factory, "chip", None
            ) == result.index:
                _LOGGER.info(
                    "Using GPIO controller %s (chip %s, label %s) "
                    "with existing lgpio factory",
                    result.device,
                    result.index,
                    result.label,
                )
                return current_factory
            current_type = type(current_factory).__name__
            current_chip = getattr(current_factory, "chip", "unknown")
            self._fail(
                "gpiozero already has an incompatible pin factory "
                f"({current_type}, chip {current_chip}); required LGPIOFactory "
                f"for {result.device} (chip {result.index})."
            )

        _LOGGER.info(
            "Selected GPIO controller %s (chip %s, label %s) with lgpio backend",
            result.device,
            result.index,
            result.label,
        )
        try:
            factory = LGPIOFactory(chip=result.index)
            Device.pin_factory = factory
        except Exception as exc:
            self._fail(
                f"could not open selected controller {result.device} (chip {result.index}) "
                f"with LGPIOFactory: {exc}",
                exc,
            )
        return factory

    def initialize_for_epaper(self):
        """Configure Raspberry Pi hardware before importing Waveshare modules."""
        if not self._is_raspberry_pi():
            return None
        result = self.discover_controller()
        return self.configure_factory(result)
