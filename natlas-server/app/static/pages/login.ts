import 'particles.js';

import { particlesStatic } from '../conf/particles-static';
import { particlesActive } from '../conf/particles-active';
import { getReducedMotion } from '../util/media-queries';

declare var particlesJS: any;

function setMotion(e: MediaQueryList | MediaQueryListEvent) {
    if (e.matches) {
        particlesJS('particles-js', particlesStatic);
    } else {
        particlesJS('particles-js', particlesActive);
    }
}

export function registerParticleEvents(): void {
    if (document.getElementById('particles-js')) {
        const reducedMotion = getReducedMotion();
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
