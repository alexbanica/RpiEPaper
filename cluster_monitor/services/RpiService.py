#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
import shutil
import time
import os
import subprocess
import re

from cluster_monitor.dto import ClusterHatStatus, DiskUsageInfo

RPI_TIME_FORMAT = "%H:%M"

class RpiService:
    def __init__(self):
        pass

    def get_current_time(self) -> str:
        try:
            return time.strftime(RPI_TIME_FORMAT, time.localtime())
        except Exception as e:
            logging.debug(f"Error retrieving current time: {e}")
            return "N/A"

    def get_hostname(self) -> str:
        try:
            return os.uname().nodename
        except Exception as e:
            logging.error(f"Error retrieving hostname: {e}")
            return "Unknown"

    def is_wifi_enabled(self) -> bool:
        try:
            output = subprocess.check_output(['sudo', 'nmcli', 'radio', 'wifi'], text=True).strip()
            return output.lower() == 'enabled'
        except Exception as e:
            logging.debug(f"Error checking WiFi status: {e}")
            return False

    def _get_my_ip_address(self) -> str:
        try:
            output = subprocess.check_output(['ifconfig'], text=True)
            # Look for eth0 or wlan0 interface
            for interface in ['eth0', 'wlan0']:
                match = re.search(f'{interface}.*?inet\s+(\d+\.\d+\.\d+\.\d+)', output, re.DOTALL)
                if match:
                    return match.group(1)
            return "N/A"
        except Exception as e:
            logging.debug(f"Error retrieving IP address: {e}")
            return "N/A"

    def is_fan_on(self) -> bool:
        try:
            with open('/sys/devices/virtual/thermal/cooling_device0/cur_state', 'r') as fan_file:
                status = fan_file.read().strip()
                fan_file.close()
            return status == '1'  # Assuming '1' indicates the fan is on, and '0' indicates off
        except FileNotFoundError:
            logging.debug("Fan file for reading status not found.")
            return False
        except Exception as e:
            logging.debug(f"Error reading fan status: {e}")
            return False

    def get_temperature(self) -> float:
        """Reads the current temperature of the Raspberry Pi in Celsius."""
        try:
            # Read the temperature from Raspberry Pi's thermal zone
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp_file:
                temperature = int(temp_file.read()) / 1000.0  # Convert millidegree to Celsius
                temp_file.close()
            return temperature
        except FileNotFoundError:
            logging.debug("Unable to read Raspberry Pi temperature.")
            return "T:N/A"

    def _get_ram_usage(self) -> tuple:
        try:
            with open('/proc/meminfo', 'r') as mem_file:
                meminfo = mem_file.readlines()
                mem_file.close()

            # Extract MemTotal and MemAvailable from /proc/meminfo
            mem_total = int([line for line in meminfo if "MemTotal" in line][0].split()[1])  # kB
            mem_available = int([line for line in meminfo if "MemAvailable" in line][0].split()[1])  # kB

            # Calculate used RAM
            used_ram = mem_total - mem_available  # in kB

            # Convert to MB and return
            return (used_ram // 1024, mem_total // 1024)  # Convert kB to MB

        except Exception as e:
            logging.debug(f"Error reading RAM usage: {e}")
            return (0, 0)  # Default to 0 if there’s an error

    def _get_ram_usage_percentage(self) -> float:
        try:
            used_ram, total_ram = self._get_ram_usage()
            if total_ram > 0:
                return round((used_ram / total_ram) * 100, 1)
            return 0.0
        except Exception as e:
            logging.debug(f"Error calculating memory usage percentage: {e}")
            return 0.0

    def _get_cpu_usage_percentage(self) -> float:
        try:
            # Read initial CPU stats
            with open('/proc/stat', 'r') as stat_file:
                first_line = stat_file.readline()
                stat_file.close()
            cpu_stats_1 = list(map(int, first_line.split()[1:]))  # Skip the "cpu" keyword

            # Wait 100ms to calculate CPU usage over time
            time.sleep(0.1)

            # Read CPU stats again
            with open('/proc/stat', 'r') as stat_file:
                first_line = stat_file.readline()
            cpu_stats_2 = list(map(int, first_line.split()[1:]))

            # Calculate total work and total time differences
            idle_time_1, idle_time_2 = cpu_stats_1[3], cpu_stats_2[3]
            total_time_1, total_time_2 = sum(cpu_stats_1), sum(cpu_stats_2)

            work_time = (total_time_2 - total_time_1) - (idle_time_2 - idle_time_1)
            total_time = total_time_2 - total_time_1

            # Calculate CPU usage percentage
            cpu_usage = (work_time / total_time) * 100 if total_time > 0 else 0.0

            return round(cpu_usage, 1)  # Round to 2 decimal places

        except Exception as e:
            logging.debug(f"Error reading CPU usage: {e}")
            return 0.0  # Return 0% on error

    def __get_path_usage_info(self, path: str) -> DiskUsageInfo:
        try:
            # Get disk usage stats for the given path
            usage = shutil.disk_usage(path)

            total_size = usage.total  # Total space in bytes
            used_size = usage.used    # Used space in bytes
            free_size = usage.free    # Free space in bytes
            percentage_used = (used_size / total_size) * 100 if total_size > 0 else 0.0  # Calculate percentage used

            return DiskUsageInfo(
                path=path,
                total_size=total_size,
                used_size=used_size,
                free_size=free_size,
                used_percentage=round(percentage_used, 1)
            )
        except Exception as e:
            raise ValueError(f"Error retrieving disk space info for {path}: {e}")

    def _get_local_disk_usage(self) -> float:
        try:
            return self.__get_path_usage_info('/').used_percentage
        except Exception as e:
            logging.debug(f"Error retrieving disk space usage: {e}")
            return 0.0

    def _get_clusterhat_status(self) -> ClusterHatStatus:
        try:
            # Execute the command and decode the output to string
            output = subprocess.check_output(['clusterhat', 'status'], text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Failed to run clusterhat status: {e}')

        # Prepare storage for our keys of interest
        hat_alert = 0
        px_count = 1

        # Parse the output line by line
        for line in output.splitlines():
            # Remove potential whitespaces
            line = line.strip()
            if line.startswith('hat_alert:'):
                hat_alert = int(line.split(':')[1])
            match = re.match(r'p\d+:(\d+)', line)
            if match and match.group(1) == '1':
                px_count += 1

        return ClusterHatStatus(px_count > 1, hat_alert == 1, px_count)

    def get_cpu_architecture(self) -> str:
        try:
            return os.uname().machine
        except Exception as e:
            logging.debug(f"Error retrieving CPU architecture: {e}")
            return "unknown"

    def is_cluster_hat_on(self) -> bool:
        status = self._get_clusterhat_status()
        return status.is_on

    def get_disk_usages(self, disks: list[str] = ['/', '/mnt/data', '/mnt/ssd_data']) -> list[DiskUsageInfo]:
        disk_usage_info = []
        for disk in disks:
            try:
                disk_usage_info.append(self.__get_path_usage_info(disk))
            except ValueError as e:
                logging.warning(f"Error retrieving disk space info for {disk}: {e}")

        return disk_usage_info

    def render_cluster_hat_status(self) -> str:
        status = self._get_clusterhat_status()

        return f"C: {'Y' if status.is_on else 'N'} - N: {status.active_node_count}/5 - F: {'Y' if self.is_fan_on() else 'N'} - {self._get_my_ip_address()}"

    def render_stats(self) -> str:
        cpu_usage = self._get_cpu_usage_percentage()
        ram_usage = self._get_ram_usage_percentage()
        temperature = self.get_temperature()
        is_fan_on = self.is_fan_on()
        hdd_usage = self._get_local_disk_usage()
        hostname = self.get_hostname().upper()
        arch = self.get_cpu_architecture()

        return  f"{hostname} - C: {cpu_usage:3.0f}% M: {ram_usage:3.0f}% H: {hdd_usage:3.0f}% T: {temperature:4.1f}°C {'[F]' if is_fan_on else ''} - {arch}"
