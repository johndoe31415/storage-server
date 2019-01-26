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

import time
import re
import subprocess
import mako.lookup
from .Tools import cache_result

class Controller():
	_IP_ADDR_RE = re.compile(r"\s+inet (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(?P<subnet>\d{1,2})")

	def __init__(self, app):
		self._app = app
		self._config = None
		self._domain = None
		self._lookup = None

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
