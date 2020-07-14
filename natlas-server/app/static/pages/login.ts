import 'particles.js';

import { particlesStatic } from '../conf/particles-static';
import { particlesActive } from '../conf/particles-active';
import { getReducedMotion } from '../util/media-queries';
import $ from 'jquery';

declare var particlesJS: any;

function setMotion(e: MediaQueryList | MediaQueryListEvent) {
    if (e.matches) {
        particlesJS('particles-js', particlesStatic);
    } else {
        particlesJS('particles-js', particlesActive);
    }
}

export function authFormSwitcher(): void {
    $("#login-button").click(function() {
        $("#login-button").addClass("active");
        $("#register-button").removeClass("active");
        $("#login-div").removeClass("d-none");
        $("#register-div").addClass("d-none");
    })
    $("#register-button").click(function() {
        $("#register-button").addClass("active");
        $("#login-button").removeClass("active");
        $("#login-div").addClass("d-none");
        $("#register-div").removeClass("d-none");
    })
}

export function registerParticleEvents(): void {
    if (document.getElementById('particles-js')) {
        const reducedMotion = getReducedMotion();
        reducedMotion.addListener(setMotion);
        setMotion(reducedMotion);
    }
}
