import 'particles.js';

import { particlesStatic } from '../conf/particles-static';
import { particlesActive } from '../conf/particles-active';

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
        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
