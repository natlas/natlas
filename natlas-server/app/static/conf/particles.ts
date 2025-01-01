import { IOptions } from '@tsparticles/engine';
import { RecursivePartial } from '@tsparticles/engine';

export function particlesConfig(active: boolean): RecursivePartial<IOptions> {

    return {
        'fpsLimit': 60,
        'particles': {
            'number': {
                'value': 200,
                'density': {
                    'enable': true
                }
            },
            'color': {
                'value': '#ed1e79'
            },
            'stroke': {
                'width': 0,
                'color': '#ed1e79'
            },
            'shape': {
                'type': 'triangle'
            },
            'opacity': {
                'value': {
                    min: 0.1,
                    max: 0.33
                },
                'animation': {
                    'enable': false,
                    'mode': 'random',
                    'speed': 1,
                    'sync': false
                }
            },
            'size': {
                'value': {
                    min: 0.1,
                    max: 3
                },
                'animation': {
                    'enable': false,
                    'speed': {
                        min: 40,
                        max: 40
                    },
                    'mode': 'random',
                    'sync': false
                }
            },
            'links': {
                'enable': true,
                'distance': 150,
                'color': '#ed1e79',
                'opacity': 0.4,
                'width': 1
            },
            'move': {
                'enable': active,
                'speed': 1,
                'direction': 'none',
                'random': false,
                'straight': false,
                'outModes': {
                    'default': 'out'
                },
                'attract': {
                    'enable': false,
                    'rotate': {
                        'x': 600,
                        'y': 1200
                    }
                }
            }
        },
        'interactivity': {
            'detectOn': 'canvas',
            'events': {
                'onHover': {
                    'enable': active,
                    'mode': 'repulse'
                },
                'onClick': {
                    'enable': active,
                    'mode': 'push'
                },
                'resize': {
                    delay: 1,
                    enable: true
                }
            },
            'modes': {
                'grab': {
                    'distance': 400,
                    'links': {
                        'opacity': 1
                    }
                },
                'bubble': {
                    'distance': 400,
                    'size': 40,
                    'duration': 2
                },
                'repulse': {
                    'distance': 100,
                    'duration': 0.4
                },
                'push': {
                    'quantity': 4
                },
                'remove': {
                    'quantity': 2
                }
            }
        },
        'detectsRetina': true
    };
}
