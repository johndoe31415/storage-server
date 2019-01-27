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
import json
from flask import Flask, send_from_directory, jsonify, request
from .Controller import Controller
from .Tools import Tools

app = Flask(__name__, static_folder = None)
ctrlr = Controller(app)

@app.route("/action/<action>")
def action(action):
	ctrlr.action(action)
	return "OK"

@app.route("/static/<path:path>")
def xstatic(path):
	return send_from_directory(ctrlr.staticdir, path)

@app.route("/status")
def status():
	if os.path.isfile("/tmp/mock.json"):
		with open("/tmp/mock.json") as f:
			result = json.load(f)
	else:
		result = {
			"uptime":			ctrlr.uptime,
			"idletime":			ctrlr.idletime,
			"cpucount":			ctrlr.cpucount,
			"ip":				ctrlr.ip_info,
			"mdstat":			ctrlr.md_info,
			"df":				ctrlr.df_info,
			"quota":			ctrlr.quota_info,
			"user":				request.environ.get("SSL_CLIENT_S_DN_CN"),
			"monitor":			ctrlr.monitor_info,
			"netif":			ctrlr.netif_info,
			"disks":			ctrlr.disk_info,
		}
	return jsonify(result)

@app.route("/")
def index():
	template = ctrlr.template("index.html")
	return template.render(**{
		"t":			Tools,
		"config":		ctrlr.config,
	})

@app.route("/test")
def test():
	template = ctrlr.template("test.html")
	return template.render(**{
		"t":			Tools,
		"config":		ctrlr.config,
	})
