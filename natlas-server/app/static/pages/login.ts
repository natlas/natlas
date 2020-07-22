import { tsParticles } from 'tsparticles';

import { particlesConfig } from '../conf/particles';
import { getReducedMotion } from '../util/media-queries';

function setMotion(e: MediaQueryList | MediaQueryListEvent) {
    tsParticles.init();

    if (e.matches) {
        tsParticles.load('tsparticles', particlesConfig(false));
    } else {
        tsParticles.load('tsparticles', particlesConfig(true));
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
    if (document.getElementById('tsparticles')) {
        const reducedMotion = getReducedMotion();
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
