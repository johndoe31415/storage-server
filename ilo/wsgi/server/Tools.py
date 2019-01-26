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
import functools

class cache_result():
	def __init__(self, timeout = None):
		self._timeout = timeout
		self._last_value = None
		self._last_update = None
		self._decoree = None

	def _execute(self, *args, **kwargs):
		now = time.time()
		refresh = (self._last_update is None) or ((self._timeout is not None) and (now - self._last_update > self._timeout))
		if refresh:
			self._last_value = self._decoree(*args, **kwargs)
			self._last_update = now
		return self._last_value

	def __call__(self, decoree):
		self._decoree = decoree

		@functools.wraps(self._decoree)
		def execute(*args, **kwargs):
			return self._execute(*args, **kwargs)
		return execute


class Tools():
	@classmethod
	def fmt_time(cls, secs):
		return "%.0f" % (secs)


if __name__ == "__main__":
	class TestClass():
		def __init__(self):
			self._count = 0

		@property
		@cacheresult()
		def foo(self):
			self._count += 1
			print("exec foo")
			return "foo %d" % (self._count)

		@cacheresult(2)
		def bar(self, i = 1):
			self._count += i
			print("exec bar")
			return "bar %d" % (self._count)

	tc = TestClass()
	print(tc.foo)
	print(tc.bar(10))
	time.sleep(1)
	print(tc.foo)
	print(tc.bar())
	time.sleep(1)
	print(tc.foo)
	print(tc.bar())
