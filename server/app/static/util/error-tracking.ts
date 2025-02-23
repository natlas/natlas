import { init, BrowserOptions } from '@sentry/browser';
import { thisVersion } from './version-check';

const metaTag: HTMLMetaElement = document.querySelector('meta[name="sentry-dsn"]');

if (metaTag) {
    const options: BrowserOptions = {
        dsn: metaTag.content,
        release: thisVersion()
    };
    init(options);
}
