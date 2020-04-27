const updateURL = "https://api.github.com/repos/natlas/natlas/releases/latest";
export const LatestURL = "https://github.com/natlas/natlas/releases/latest";

// Not ideal. We should pack this into the bundle instead
export function thisVersion(): String {
	return document.getElementById('natlasVersion').innerText
}

function extractVersion(result: any) {
	return result.tag_name;
}

export function getLatestVersion(): Promise<String> {
	return fetch(updateURL)
		.then(response => response.json())
		.then(extractVersion);
}
