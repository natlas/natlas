import makeXhrCall from './xhr';

const updateURL = "https://api.github.com/repos/natlas/natlas/releases/latest";
export const LatestURL = "https://github.com/natlas/natlas/releases/latest";

class GithubReleases {
	tag_name: string
};

// Not ideal. We should pack this into the bundle instead
export function thisVersion(): String {
	return document.getElementById('natlasVersion').innerText
}

function extractVersion(result: GithubReleases): String {
	return result.tag_name;
}

export function getLatestVersion(): Promise<String> {
	return makeXhrCall<GithubReleases>(updateURL)
		.then(extractVersion);
}
