#!/usr/bin/python3
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

import sys
import time
import subprocess

class Suspend():
	def __init__(self):
		pass

	def is_screensaver_active(self):
		output = subprocess.check_output([ "dbus-send", "--print-reply=literal", "--dest=org.mate.ScreenSaver", "/org/mate/ScreenSaver", "org.mate.ScreenSaver.GetActive" ])
		return b"boolean true" in output

	def lock_screensaver(self):
		subprocess.check_call([ "dbus-send", "--type=method_call", "--dest=org.mate.ScreenSaver", "/org/mate/ScreenSaver", "org.mate.ScreenSaver.Lock" ])

	def perform_suspend(self, verbose = True):
		if verbose:
			print("Suspending computer.", file = sys.stderr)
		self.lock_screensaver()
		subprocess.check_call([ "dbus-send", "--system", "--print-reply", "--dest=org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.Suspend", "boolean:true" ])
		time.sleep(10)

	def perform_suspend_if_screensaver_active(self):
		if self.is_screensaver_active():
			self.perform_suspend()

if __name__ == "__main__":
	susp = Suspend()
	yn = input("Suspend (y/n)? ")
	if yn == "y":
		t0 = time.time()
		print("Suspending!")
		susp.perform_suspend()
		t1 = time.time()
		print("Woke up: %.1f seconds in hibernation." % (t1 - t0))
		sys.exit(0)
	else:
		print("Not suspending.")

	while True:
		print("Screensaver:", susp.is_screensaver_active())
		time.sleep(1)
