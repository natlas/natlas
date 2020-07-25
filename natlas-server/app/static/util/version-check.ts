/* globals process */
import makeXhrCall from './xhr';

const updateURL = 'https://api.github.com/repos/natlas/natlas/releases/latest';
const downloadURL = 'https://github.com/natlas/natlas/releases/latest';

interface GithubReleases {
    tag_name: string;
}

class UpdateCheckResult {
    constructor(public isNewerAvailable: boolean, public downloadUrl: string, public version: string) {
    }
}

declare const NATLAS_VERSION: string;

export function thisVersion(): string {
    return NATLAS_VERSION;
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
        .then((latestVersion) => new UpdateCheckResult(latestVersion !== thisVersion(), downloadURL, latestVersion));
}
