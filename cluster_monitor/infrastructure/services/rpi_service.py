import logging
import math
import os
import re
import shutil
import subprocess
import threading
import time
from time import sleep
from typing import Optional, Union

from cluster_monitor.domain.entities import ClusterHatStatusEntity, DiskUsageInfoEntity
from cluster_monitor.domain.services import RpiServiceInterface

RPI_TIME_FORMAT = "%H:%M"
LOCAL_COMMAND_TIMEOUT_SECONDS = 10


def _run_local_command(command: list[str], *, capture_stderr: bool = True) -> subprocess.CompletedProcess:
    """Run a local command with bounded execution and deterministic pipe cleanup."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if capture_stderr else None,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=LOCAL_COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        finally:
            process.wait()
        raise
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


class RpiService(RpiServiceInterface):
    def __init__(self):
        self.cluster_hat_alert_enabled = False
        self.set_cluster_hat_alert(False)

    def get_current_time(self) -> str:
        try:
            return time.strftime(RPI_TIME_FORMAT, time.localtime())
        except Exception as error:
            logging.debug("Error retrieving current time: %s", error)
            return "N/A"

    def get_hostname(self) -> str:
        try:
            return os.uname().nodename
        except Exception as error:
            logging.error("Error retrieving hostname: %s", error)
            return "Unknown"

    def _get_my_ip_address(self) -> str:
        try:
            result = _run_local_command(["ifconfig"], capture_stderr=False)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, ["ifconfig"])
            output = result.stdout
            interface_blocks: dict[str, list[str]] = {}
            current_interface: Optional[str] = None
            for line in output.splitlines():
                # Support both modern `eth0: flags=...` and net-tools
                # `eth0      Link encap:...` headers. Address lines remain
                # associated with only the header that precedes them.
                # Include the full interface name so legacy alias headers such
                # as `eth0:1: flags=...` start their own block. Selection below
                # remains exact for eth0 and wlan0.
                header = re.match(r"^(\S+?)(?::\s*flags=|\s+Link encap:)", line)
                if header:
                    current_interface = header.group(1)
                    interface_blocks.setdefault(current_interface, []).append(line)
                elif current_interface is not None:
                    interface_blocks[current_interface].append(line)

            for interface in ["eth0", "wlan0"]:
                for block in interface_blocks.get(interface, []):
                    match = re.search(r"\binet\s+(?:addr:)?(\d{1,3}(?:\.\d{1,3}){3})\b", block)
                    if match:
                        return match.group(1)
            return "N/A"
        except Exception as error:
            logging.debug("Error retrieving IP address: %s", error)
            return "N/A"

    def is_fan_on(self) -> bool:
        try:
            with open("/sys/devices/virtual/thermal/cooling_device0/cur_state", "r", encoding="utf-8") as fan_file:
                return fan_file.read().strip() == "1"
        except Exception:
            return False

    def get_temperature(self) -> Union[float, str]:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as temp_file:
                return int(temp_file.read()) / 1000.0
        except Exception:
            return "T:N/A"

    def _get_ram_usage(self) -> tuple[int, int]:
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as mem_file:
                meminfo = mem_file.readlines()

            mem_total = int([line for line in meminfo if "MemTotal" in line][0].split()[1])
            mem_available = int([line for line in meminfo if "MemAvailable" in line][0].split()[1])
            used_ram = mem_total - mem_available
            return used_ram // 1024, mem_total // 1024
        except Exception:
            return 0, 0

    def _get_ram_usage_percentage(self) -> float:
        used_ram, total_ram = self._get_ram_usage()
        if total_ram <= 0:
            return 0.0
        return round((used_ram / total_ram) * 100, 1)

    def _get_cpu_usage_percentage(self) -> float:
        try:
            with open("/proc/stat", "r", encoding="utf-8") as stat_file:
                cpu_stats_1 = list(map(int, stat_file.readline().split()[1:]))
            time.sleep(0.1)
            with open("/proc/stat", "r", encoding="utf-8") as stat_file:
                cpu_stats_2 = list(map(int, stat_file.readline().split()[1:]))

            idle_time_1, idle_time_2 = cpu_stats_1[3], cpu_stats_2[3]
            total_time_1, total_time_2 = sum(cpu_stats_1), sum(cpu_stats_2)
            work_time = (total_time_2 - total_time_1) - (idle_time_2 - idle_time_1)
            total_time = total_time_2 - total_time_1
            cpu_usage = (work_time / total_time) * 100 if total_time > 0 else 0.0
            return round(cpu_usage, 1)
        except Exception:
            return 0.0

    def _get_path_usage_info(self, path: str) -> DiskUsageInfoEntity:
        usage = shutil.disk_usage(path)
        total_size = usage.total
        used_size = usage.used
        free_size = usage.free
        percentage_used = (used_size / total_size) * 100 if total_size > 0 else 0.0
        return DiskUsageInfoEntity(
            path=path,
            total_size=total_size,
            used_size=used_size,
            free_size=free_size,
            used_percentage=round(percentage_used, 1),
        )

    def _get_local_disk_usage(self) -> float:
        try:
            return self._get_path_usage_info("/").used_percentage
        except Exception:
            return 0.0

    def get_clusterhat_status(self) -> ClusterHatStatusEntity:
        try:
            result = _run_local_command(["clusterhat", "status"])
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            output = result.stdout

            hat_alert = 0
            px_count = 1
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("hat_alert:"):
                    hat_alert = int(line.split(":")[1])
                match = re.match(r"p\d+:(\d+)", line)
                if match and match.group(1) == "1":
                    px_count += 1

            return ClusterHatStatusEntity(is_on=px_count > 1, has_alert=hat_alert == 1, active_node_count=px_count)
        except Exception as error:
            logging.error("Unexpected error while retrieving ClusterHat status: %s", error)
            return ClusterHatStatusEntity(active_node_count=0, is_on=False, has_alert=False)

    def is_cluster_hat_on(self) -> bool:
        return self.get_clusterhat_status().is_on

    def get_disk_usages(self, disks: Optional[list[str]] = None) -> list[DiskUsageInfoEntity]:
        selected_disks = disks or ["/", "/mnt/data", "/mnt/ssd_data", "/mnt/hdd_data"]
        disk_usage_info: list[DiskUsageInfoEntity] = []
        for disk in selected_disks:
            try:
                disk_usage_info.append(self._get_path_usage_info(disk))
            except Exception as error:
                logging.warning("Error retrieving disk space info for %s: %s", disk, error)
        return disk_usage_info

    def render_cluster_hat_status(self) -> str:
        status = self.get_clusterhat_status()
        return (
            f"C: {'Y' if status.is_on else 'N'} - "
            f"N: {status.active_node_count}/5 - "
            f"F: {'Y' if self.is_fan_on() else 'N'} - {self._get_my_ip_address()}"
        )

    def render_stats(self) -> str:
        cpu_usage = self._get_cpu_usage_percentage()
        ram_usage = self._get_ram_usage_percentage()
        temperature = self.get_temperature()
        hdd_usage = self._get_local_disk_usage()
        hostname = self.get_hostname().upper()

        fan_suffix = " [F]" if self.is_fan_on() else ""
        if (
            isinstance(temperature, (int, float))
            and not isinstance(temperature, bool)
            and math.isfinite(temperature)
        ):
            temperature_field = f"T: {temperature:4.1f}°C"
        else:
            temperature_field = "T: N/A"
        return f"{hostname} - C: {cpu_usage:3.0f}% M: {ram_usage:3.0f}% H: {hdd_usage:3.0f}% {temperature_field}{fan_suffix}"

    def get_lines_from_file(self, filename: str, nr_lines: int = 10) -> list[str]:
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return [line.rstrip() for line in file.readlines()[-nr_lines:]]
        except Exception as error:
            logging.error("Error reading file %s: %s", filename, error)
            return []

    def is_healthy(self) -> bool:
        status = self.get_clusterhat_status()
        is_healthy = not status.is_on or status.active_node_count == 5
        if not is_healthy:
            logging.error("Clusterhat is not healthy. Status: %s", status)
        return is_healthy

    def restart_nodes(self, hostnames: list[str]) -> None:
        for hostname in hostnames:
            thread = threading.Thread(target=self._restart_node_by_hostname, daemon=True, kwargs={"hostname": hostname})
            thread.start()

    def _restart_node_by_hostname(self, hostname: str) -> None:
        try:
            result = _run_local_command(["clusterhat", "off", hostname])
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
            sleep(2)
            result = _run_local_command(["clusterhat", "on", hostname])
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
        except Exception as error:
            logging.error("Error restarting node %s: %s", hostname, error)

    def set_cluster_hat_alert(self, enable: bool) -> None:
        if self.cluster_hat_alert_enabled == enable:
            return

        status = "on" if enable else "off"
        try:
            result = _run_local_command(["clusterhat", "alert", status])
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, ["clusterhat", "alert", status])
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Failed to set clusterhat alert: {error}") from error
        self.cluster_hat_alert_enabled = enable

    def render_logs(self, lines: list[str]) -> list[str]:
        processed_lines: list[str] = []
        for line in lines:
            try:
                match = re.match(r"^.*?(\d{2}:\d{2}):\d{2},\d{3} \[(\w+)].*?: (.*)$", line)
                if not match:
                    continue

                event_time = match.group(1)
                log_level = match.group(2)[0]
                message = match.group(3)
                message = re.sub(r"\[?(?:Thread-\d+|MainThread).*\]?: ?", "", message)
                message = re.sub(r"\[Thread-\d+.*\]", "", message)
                processed_lines.append(f"{event_time} [{log_level}] {message}")
            except Exception as error:
                logging.error("Error processing line: %s. Error: %s", line, error)
        return processed_lines
