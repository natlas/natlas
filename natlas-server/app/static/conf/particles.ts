import { IOptions } from 'tsparticles/dist/Options/Interfaces/IOptions';
import { RecursivePartial } from 'tsparticles/dist/Types/RecursivePartial';

export function particlesConfig(active: boolean): RecursivePartial<IOptions> {

    return {
        'fpsLimit': 60,
        'particles': {
            'number': {
                'value': 100,
                'density': {
                    'enable': true,
                    'value_area': 500
                }
            },
            'color': {
                'value': '#ed1e79'
            },
            'shape': {
                'type': 'triangle',
                'stroke': {
                    'width': 0,
                    'color': '#ed1e79'
                }
            },
            'opacity': {
                'value': 0.33,
                'random': false,
                'anim': {
                    'enable': false,
                    'speed': 1,
                    'opacity_min': 0.1,
                    'sync': false
                }
            },
            'size': {
                'value': 3,
                'random': true,
                'anim': {
                    'enable': false,
                    'speed': 40,
                    'size_min': 0.1,
                    'sync': false
                }
            },
            'line_linked': {
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
                'out_mode': 'out',
                'bounce': false,
                'attract': {
                    'enable': false,
                    'rotateX': 600,
                    'rotateY': 1200
                }
            }
        },
        'interactivity': {
            'detect_on': 'canvas',
            'events': {
                'onhover': {
                    'enable': active,
                    'mode': 'repulse'
                },
                'onclick': {
                    'enable': active,
                    'mode': 'push'
                },
                'resize': true
            },
            'modes': {
                'grab': {
                    'distance': 400,
                    'line_linked': {
                        'opacity': 1
                    }
                },
                'bubble': {
                    'distance': 400,
                    'size': 40,
                    'duration': 2,
                    'opacity': 8
                },
                'repulse': {
                    'distance': 100,
                    'duration': 0.4
                },
                'push': {
                    'particles_nb': 4
                },
                'remove': {
                    'particles_nb': 2
                }
            }
        },
        'retina_detect': true
    };
}
