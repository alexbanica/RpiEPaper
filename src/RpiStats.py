import logging
import time
import os

RPI_TIME_FORMAT = "%H:%M"
RPI_STATS_PYTHON_COMMAND = "PYTHONPATH=/mnt/data/ePaperHat/src python3 -c 'from RpiStats import RpiStats; print(RpiStats())'"

class RpiStats:
    def __init__(self):
        pass

    def get_current_time(self) -> str:
        try:
            return time.strftime(RPI_TIME_FORMAT, time.localtime())
        except Exception as e:
            logging.debug(f"Error retrieving current time: {e}")
            return "N/A"

    def get_hostname(self) -> str:
        """
        Returns the hostname of the device.
    
        Returns:
            str: The hostname of the device.
        """
        try:
            return os.uname().nodename
        except Exception as e:
            logging.error(f"Error retrieving hostname: {e}")
            return "Unknown"

    def is_fan_on(self) -> bool:
        """
        Checks if the Raspberry Pi fan is currently on or off.
    
        Returns:
            bool: True if the fan is on, False otherwise.
        """
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

    def get_ram_usage(self) -> tuple:
        """
        Reads the Raspberry Pi's RAM usage.
    
        Returns:
            tuple: (used_ram_MB, total_ram_MB), both in megabytes (MB).
        """
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

    def get_ram_usage_percentage(self) -> float:
        """
        Calculates the Raspberry Pi's memory usage percentage.
    
        Returns:
            float: Memory usage as a percentage of total RAM.
        """
        try:
            used_ram, total_ram = self.get_ram_usage()
            if total_ram > 0:
                return round((used_ram / total_ram) * 100, 1)
            return 0.0
        except Exception as e:
            logging.debug(f"Error calculating memory usage percentage: {e}")
            return 0.0

    def get_cpu_usage_percentage(self) -> float:
        """
        Calculates the current CPU usage percentage.
    
        Returns:
            float: CPU usage in percentage.
        """
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

    def get_used_disk_percentage(self) -> float:
        """
        Retrieves the percentage of used disk space.
        
        Returns:
            float: Percentage of disk space used.
        """
        try:
            statvfs = os.statvfs('/')
            # Calculate total and available disk space in bytes
            total_space = statvfs.f_blocks * statvfs.f_frsize
            free_space = statvfs.f_bfree * statvfs.f_frsize
            used_space_percentage = ((total_space - free_space) / total_space) * 100 if total_space > 0 else 0.0
            return round(used_space_percentage, 1)
        except Exception as e:
            logging.debug(f"Error retrieving disk space usage: {e}")
            return 0.0

    def is_cluster_hat_on(self) -> bool:
        return True

    def is_cluster_hat_fan_on(self) -> bool:
        return True

    def __str__(self) -> str:
        cpu_usage = self.get_cpu_usage_percentage()
        ram_usage = self.get_ram_usage_percentage()
        temperature = self.get_temperature()
        is_fan_on = self.is_fan_on()
        hdd_usage = self.get_used_disk_percentage()
        hostname = self.get_hostname().upper()

        return  f"{hostname} - C: {cpu_usage:3.0f}% R: {ram_usage:3.0f}% H: {hdd_usage:3.0f}% T: {temperature:4.1f}°C {'(F)' if is_fan_on else ''}"
