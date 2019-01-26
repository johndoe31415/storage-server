function format_time(secs) {
	const days = (secs / 86400) | 0;
	const hours = (secs % 86400 / 3600) | 0;
	const minutes = (secs % 86400 % 3600 / 60) | 0;
	return sprintf("%dd %02d:%02d h:m", days, hours, minutes);
}

function format_cpu(uptime, idletime, cpucount) {
	const idle_ratio = (idletime / cpucount) / uptime;
	const busy_ratio = 1 - idle_ratio;
	return sprintf("%.1f%%", 100 * busy_ratio);
}

function format_timet(timet) {
	const datetime = new Date(timet * 1000);
	return datetime.toLocaleString();
}

function format_space(bytes) {
	if (bytes < 1e3) {
		return sprintf("%.0f B", bytes);
	} else if (bytes < 1e4) {
		return sprintf("%.2f kB", bytes / 1e3);
	} else if (bytes < 1e5) {
		return sprintf("%.1f kB", bytes / 1e3);
	} else if (bytes < 1e6) {
		return sprintf("%.0f kB", bytes / 1e3);
	} else if (bytes < 1e7) {
		return sprintf("%.2f MB", bytes / 1e6);
	} else if (bytes < 1e8) {
		return sprintf("%.1f MB", bytes / 1e6);
	} else if (bytes < 1e9) {
		return sprintf("%.0f MB", bytes / 1e6);
	} else if (bytes < 1e10) {
		return sprintf("%.2f GB", bytes / 1e9);
	} else if (bytes < 1e11) {
		return sprintf("%.1f GB", bytes / 1e9);
	} else if (bytes < 1e12) {
		return sprintf("%.0f GB", bytes / 1e9);
	} else if (bytes < 1e13) {
		return sprintf("%.2f TB", bytes / 1e12);
	} else if (bytes < 1e14) {
		return sprintf("%.1f TB", bytes / 1e12);
	} else {
		return sprintf("%.0f TB", bytes / 1e12);
	}
}
