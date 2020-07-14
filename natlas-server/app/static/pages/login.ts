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

export function authFormSwitcher(): void {
    const loginBtn = document.querySelector('#login-button');
    const loginDiv = document.querySelector('#login-div');
    const regBtn = document.querySelector('#register-button');
    const regDiv = document.querySelector('#register-div');

    loginBtn.addEventListener('click', () => {
        loginBtn.classList.add('active');
        regBtn.classList.remove('active');
        loginDiv.classList.remove('d-none');
        regDiv.classList.add('d-none');
    });

    regBtn.addEventListener('click', () => {
        regBtn.classList.add('active');
        loginBtn.classList.remove('active');
        loginDiv.classList.add('d-none');
        regDiv.classList.remove('d-none');
    });
}

export function registerParticleEvents(): void {
    if (document.getElementById('particles-js')) {
        const reducedMotion = getReducedMotion();
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
