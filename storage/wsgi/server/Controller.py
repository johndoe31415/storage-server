#	storage-server - Integrated remote backup solution
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of storage-server.
#
#	storage-server is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	storage-server is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with storage-server; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import os
import time
import re
import json
import subprocess
import mako.lookup
from .Tools import cache_result

class Controller():
	_IP_ADDR_RE = re.compile(r"\s+inet (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(?P<subnet>\d{1,2})")
	_QUOTA_RE = re.compile(r"^(?P<username>[a-zA-Z][a-zA-Z0-9]*)\s+--\s+(?P<used>\d+)\s+(?P<soft>\d+)\s+(?P<hard>\d+)\s+")

	def __init__(self, app):
		self._app = app
		self._config = None
		self._domain = None
		self._lookup = None
		self._last_netif = None

	@property
	def config(self):
		return self._config

	def set_config(self, config, domain):
		self._config = config
		self._domain = domain
		self._lookup = mako.lookup.TemplateLookup([ self._config["rootdir"] + "/" + self._domain + "/templates" ], strict_undefined = True, input_encoding = "utf-8")

	@property
	def staticdir(self):
		return self._config["rootdir"] + "/" + self._domain + "/docroot"

	@property
	@cache_result(60)
	def uptime_idletime(self):
		with open("/proc/uptime") as f:
			line = f.read().strip().split()
			(uptime, idletime) = (float(line[0]), float(line[1]))
			return (uptime, idletime)

	@property
	def uptime(self):
		return self.uptime_idletime[0]

	@property
	def idletime(self):
		return self.uptime_idletime[1]

	@property
	@cache_result()
	def cpucount(self):
		count = 0
		with open("/proc/cpuinfo") as f:
			for line in f:
				if line.startswith("processor"):
					count += 1
		return count

	@property
	@cache_result(2)
	def storage_online(self):
		try:
			subprocess.check_call([ "fping", "-c", "1", "-t", str(self._config["timeouts"]["storage_ping_timeout_millis"]), self._config["storage"]["ip"] ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
			online = True
		except subprocess.CalledProcessError:
			online = False
		return online

	def _get_raw_power_state(self):
		try:
			with open(self._config["ilo"]["files"]["gpio_in_power"]) as f:
				powered = (int(f.read().strip("\r\n")) != 0)
		except FileNotFoundError:
			return None
		return powered

	@property
	@cache_result(1)
	def storage_powered(self):
		return self._get_raw_power_state()

	@property
	@cache_result(30)
	def ip_info(self):
		raw_output = subprocess.check_output([ "ip", "addr", "show", "dev", self._config[self._domain]["interface"], "scope", "global" ]).decode("utf-8")
		parsed = self._IP_ADDR_RE.search(raw_output)
		if parsed:
			parsed = parsed.groupdict()
		return {
			"ifname":	self._config[self._domain]["interface"],
			"parsed":	parsed,
			"raw":		raw_output,
		}

	@property
	@cache_result(30)
	def md_info(self):
		with open("/proc/mdstat") as f:
			raw_output = f.read()
		return {
			"raw":		raw_output,
		}

	@property
	@cache_result(30)
	def df_info(self):
		try:
			stat = os.statvfs(self._config["storage"]["datamnt"])
			result = {
				"total":	stat.f_bsize * stat.f_blocks,
				"free":		stat.f_bsize * stat.f_bfree,
			}
			result["used"] = result["total"] - result["free"]
		except FileNotFoundError:
			result = None
		return result

	@property
	@cache_result(10)
	def netif_info(self):
		with open("/sys/class/net/%s/statistics/rx_bytes" % (self._config[self._domain]["interface"])) as f:
			rx_bytes = int(f.read().strip())
		with open("/sys/class/net/%s/statistics/tx_bytes" % (self._config[self._domain]["interface"])) as f:
			tx_bytes = int(f.read().strip())

		now = time.time()
		if self._last_netif is None:
			rx_speed = 0
			tx_speed = 0
		else:
			tdiff = now - self._last_netif[0]
			rx_speed = (rx_bytes - self._last_netif[1]) / tdiff
			tx_speed = (tx_bytes - self._last_netif[2]) / tdiff
		self._last_netif = (now, rx_bytes, tx_bytes)

		result = {
			"rx":		rx_bytes,
			"tx":		tx_bytes,
			"rx_speed":	rx_speed,
			"tx_speed":	tx_speed,
		}
		return result

	@property
	@cache_result(60)
	def quota_info(self):
		try:
			raw_output = subprocess.check_output([ "sudo", "-S", "/usr/sbin/repquota", self._config["storage"]["datamnt"] ], input = b"").decode("utf-8")
		except subprocess.CalledProcessError:
			return None
		quotas = { }
		search = False
		for line in raw_output.split("\n"):
			if line.startswith("------"):
				search = True
			elif search:
				match = self._QUOTA_RE.match(line)
				if match:
					match = match.groupdict()
					quotas[match["username"]] = {
						"hard":		int(match["hard"]) * 1024,
						"used":		int(match["used"]) * 1024,
					}
		return {
			"parsed":	quotas,
			"raw":		raw_output,
		}

	def _smartmon_info(self, disk):
		try:
			json_output = subprocess.check_output([ "sudo", "-S", "/usr/local/sbin/smartctl", "-a", "--json", disk ], input = b"")
		except subprocess.CalledProcessError:
			return None
		return json.loads(json_output.decode("utf-8"))

	@property
	@cache_result(86400)
	def disk_info(self):
		disks_info = [ ]
		for disk in self._config[self._domain]["disks"]:
			disk_info = {
				"name":		disk["name"],
				"extname":	disk["extname"],
				"dev":		os.path.realpath(disk["dev"]),
			}
			smart_info = self._smartmon_info(disk["dev"])
			if smart_info is not None:
				disk_info.update({
					"model":	smart_info["model_name"],
					"serial":	smart_info["serial_number"],
				})
				smart_info_per_name = { attribute["name"]: attribute for attribute in smart_info["ata_smart_attributes"]["table"] }
				disk_info["smart"] = [ ]

				discard_when_empty = set([ "Total_LBAs_Written", "Total_Host_GB_Written", "Total_LBAs_Read", "Total_Host_GB_Read" ])
				for expose in [ "Reallocated_Sector_Ct", "Power_On_Hours", "Power_Cycle_Count", "Temperature_Celsius", "Total_LBAs_Written", "Total_Host_GB_Written", "Total_LBAs_Read", "Total_Host_GB_Read" ]:
					value = smart_info_per_name.get(expose, { "raw": { } })["raw"].get("string")
					warn = False
					show_name = expose
					if value is None and (expose in discard_when_empty):
						continue

					if expose == "Reallocated_Sector_Ct":
						show_name = "Realloced"
						warn = int(value) != 0
					elif expose == "Power_On_Hours":
						show_name = "Hours"
						value = value.split()[0]
					elif expose == "Temperature_Celsius":
						show_name = "Temp °C"
						value = value.split()[0]
						warn = int(value) >= 50
					elif expose == "Total_LBAs_Written":
						show_name = "Written"
						value = int(value) * 512
					elif expose == "Total_LBAs_Read":
						show_name = "Read"
						value = int(value) * 512
					elif expose == "Total_Host_GB_Written":
						show_name = "Written"
						value = int(value) * 1024 * 1024 * 1024
					elif expose == "Total_Host_GB_Read":
						show_name = "Read"
						value = int(value) * 1024 * 1024 * 1024

					disk_info["smart"].append({
						"name":		show_name,
						"value":	value,
						"warn":		warn,
					})
			disks_info.append(disk_info)
		return disks_info

	@property
	@cache_result(30)
	def monitor_info(self):
		try:
			with open(self._config["ilo"]["files"]["monitor_file_temporary"]) as f:
				info = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			info = None
		return info

	def _press_button(self, filename, presstime):
		with open(filename, "w") as f:
			print("1", file = f)
		time.sleep(presstime)
		with open(filename, "w") as f:
			print("0", file = f)

	def _set_power(self, new_state):
		power = self._get_raw_power_state()
		if power != new_state:
			# Press power button briefly
			self._press_button(self._config["ilo"]["files"]["gpio_out_power"], 0.2)

	def action(self, action):
		if action == "turn_on":
			self._set_power(True)
		elif action == "turn_off":
			self._set_power(False)
		elif action == "reset":
			self._press_button(self._config["ilo"]["files"]["gpio_out_reset"], 0.2)
		else:
			raise Exception("Unknown action.")

	def template(self, name):
		return self._lookup.get_template(name)
