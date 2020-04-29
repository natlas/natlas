type StatusUpdateResult = {
	completed_cycles: number;
	cycle_start_time: string;
	effective_scope_size: number;
	natlas_start_time: string;
	scans_this_cycle: number;
	avg_cycle_duration: string;
};

function updateStatus(): void {
	fetch('/api/status', {
		credentials: 'same-origin'
	})
	.then((response) => {
		return response.json();
	})
	.then((data: StatusUpdateResult) => {
		const progbar = document.getElementById("cycle_status");
		const progbg = document.getElementById("cycle_status_overlay");
		const width = (data.scans_this_cycle / data.effective_scope_size) * 100;
		progbar.setAttribute('aria-valuenow', width.toString());
		progbar.setAttribute('style', `width:${width}%;`);
		const entries = Object.entries(data);
		for (const [key, val] of entries) {
			document.getElementById(key).innerText = val.toString();
		}
		progbg.innerText = Math.round(width)+"%";
	});
}

export function initializeStatusUpdates(): void {
	if (document.getElementById("cycle_status")) {
		updateStatus();
		setInterval(updateStatus, 30000);
	}
}