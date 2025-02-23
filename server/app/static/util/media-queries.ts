export function getReducedMotion(): MediaQueryList {
    return window.matchMedia('(prefers-reduced-motion: reduce)');
}

export function getDarkMode(): MediaQueryList {
    return window.matchMedia('(prefers-color-scheme: dark)');
}

export function getLightMode(): MediaQueryList {
    return window.matchMedia('(prefers-color-scheme: light)');
}
