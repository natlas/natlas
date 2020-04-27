import makeXhrCall from './xhr';

const updateURL = "https://api.github.com/repos/natlas/natlas/releases/latest";
const downloadUrl = "https://github.com/natlas/natlas/releases/latest";

type GithubReleases = {
	tag_name: string
};

class UpdateCheckResult {
	constructor(private isNewerAvailable: boolean, private downloadUrl: string, private version: string) {
	}
};

// Not ideal. We should pack this into the bundle instead
function thisVersion(): string {
	return document.getElementById('natlasVersion').innerText
}

function extractVersion(result: GithubReleases): string {
	return result.tag_name;
}

function getLatestVersion(): Promise<string> {
	return makeXhrCall<GithubReleases>(updateURL)
		.then(extractVersion);
}

export function isNewerVersionAvailable(): Promise<UpdateCheckResult> {
	return getLatestVersion()
		.then(latestVersion => new UpdateCheckResult(latestVersion != thisVersion(), downloadUrl, latestVersion));
}