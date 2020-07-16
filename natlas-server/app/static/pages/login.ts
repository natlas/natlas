import 'particles.js';

import { particlesConfig } from '../conf/particles';
import { getReducedMotion } from '../util/media-queries';

declare var particlesJS: any;

function setMotion(e: MediaQueryList | MediaQueryListEvent) {
    if (e.matches) {
        particlesJS('particles-js', particlesConfig(false));
    } else {
        particlesJS('particles-js', particlesConfig(true));
    }
}

export function authFormSwitcher(): void {
    const loginBtn = document.querySelector('#login-button');
    const loginDiv = document.querySelector('#login-div');
    const regBtn = document.querySelector('#register-button');
    const regDiv = document.querySelector('#register-div');

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            loginBtn.classList.add('active');
            regBtn.classList.remove('active');
            loginDiv.classList.remove('d-none');
            regDiv.classList.add('d-none');
        });
    }

    if (regBtn) {
        regBtn.addEventListener('click', () => {
            regBtn.classList.add('active');
            loginBtn.classList.remove('active');
            loginDiv.classList.add('d-none');
            regDiv.classList.remove('d-none');
        });
    }
}

export function registerParticleEvents(): void {
    if (document.getElementById('particles-js')) {
        const reducedMotion = getReducedMotion();
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
