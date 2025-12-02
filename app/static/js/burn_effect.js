import * as THREE from 'https://unpkg.com/three@0.128.0/build/three.module.js';

export function initBurnEffect(selector) {
    const container = document.querySelector(selector);
    if (!container) return;

    // Attempt to target the metric for alignment, fallback to container bottom
    const metricElement = container.querySelector('.insight-metric') || container;
    
    // Scene Setup
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    // Canvas setup
    const canvas = renderer.domElement;
    canvas.classList.add('burn-effect-canvas');
    
    // Insert as first child to sit behind content
    if (container.firstChild) {
        container.insertBefore(canvas, container.firstChild);
    } else {
        container.appendChild(canvas);
    }

    let width = canvas.offsetWidth;
    let height = canvas.offsetHeight;

    renderer.setSize(width, height, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // Entropy Smoke Shader
    // Uses Domain Warping FBM for that "flowing entropy" look
    const uniforms = {
        uTime: { value: 0 },
        uResolution: { value: new THREE.Vector2(width, height) },
        uColorStart: { value: new THREE.Color('#2a2a2a') }, // Dark grey
        uColorEnd: { value: new THREE.Color('#888888') },   // Lighter grey smoke
        uOriginOffset: { value: 0.0 }, // Vertical start position (0-1 UV)
        uSpeed: { value: 0.2 },
        uSpreadBase: { value: 0.25 },
        uExpansion: { value: 1.0 },
        uDensity: { value: 0.85 },
        uNoiseScale: { value: 1.0 },
        uFlowVector: { value: new THREE.Vector2(0.0, 1.0) } // Direction of flow
    };

    const vertexShader = `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `;

    const fragmentShader = `
        uniform float uTime;
        uniform vec2 uResolution;
        uniform vec3 uColorStart;
        uniform vec3 uColorEnd;
        uniform float uOriginOffset;
        uniform float uSpeed;
        uniform float uSpreadBase;
        uniform float uExpansion;
        uniform float uDensity;
        uniform float uNoiseScale;
        uniform vec2 uFlowVector;
        
        varying vec2 vUv;

        // Simplex 2D noise
        vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

        float snoise(vec2 v){
            const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                    -0.577350269189626, 0.024390243902439);
            vec2 i  = floor(v + dot(v, C.yy) );
            vec2 x0 = v -   i + dot(i, C.xx);
            vec2 i1;
            i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
            vec4 x12 = x0.xyxy + C.xxzz;
            x12.xy -= i1;
            i = mod(i, 289.0);
            vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
            + i.x + vec3(0.0, i1.x, 1.0 ));
            vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
            m = m*m ;
            m = m*m ;
            vec3 x = 2.0 * fract(p * C.www) - 1.0;
            vec3 h = abs(x) - 0.5;
            vec3 ox = floor(x + 0.5);
            vec3 a0 = x - ox;
            m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
            vec3 g;
            g.x  = a0.x  * x0.x  + h.x  * x0.y;
            g.yz = a0.yz * x12.xz + h.yz * x12.yw;
            g.yz = a0.yz * x12.xz + h.yz * x12.yw;
            return 130.0 * dot(m, g);
        }

        float fbm(vec2 st) {
            float value = 0.0;
            float amplitude = 0.5;
            for (int i = 0; i < 3; i++) {
                value += amplitude * snoise(st);
                st *= 2.0;
                amplitude *= 0.5;
            }
            return value;
        }

        void main() {
            vec2 st = gl_FragCoord.xy / uResolution.xy;
            st.x *= uResolution.x / uResolution.y;
            st *= uNoiseScale;
            
            // Adjust coordinate system to align with origin offset
            float yRel = vUv.y - uOriginOffset;
            
            // Time flows based on uFlowVector
            // We use uFlowVector to direct the 'time' scrolling
            float time = uTime * uSpeed;
            
            // Smoke Physics / Shape
            // Center alignment for masking
            float aspect = uResolution.x / uResolution.y;
            vec2 uv = vUv;
            uv.x *= aspect; 
            float uvCenter = 0.5 * aspect;
            
            // Expansion logic
            float spread = uSpreadBase + max(0.0, yRel * uExpansion);
            
            // Domain Warping
            // We offset the noise lookup by time * flowVector
            // The -time ensures standard "flow" direction is consistent with vector
            
            vec2 flow = uFlowVector * time;
            
            vec2 q = vec2(0.);
            q.x = fbm( st + flow * 0.5 ); 
            q.y = fbm( st + vec2(1.0)); // Keep y variation somewhat independent or sync? 
            // Ideally, q should warp along flow too.
            
            vec2 r = vec2(0.);
            r.x = fbm( st + 1.0*q + vec2(1.7,9.2) + 0.15*time );
            r.y = fbm( st + 1.0*q + vec2(8.3,2.8) + 0.126*time );

            // Main scroll
            float f = fbm(st + r - flow);

            // Masking
            float dist = abs(uv.x - uvCenter);
            float mask = smoothstep(spread, spread - 0.3, dist + f * 0.2);
            
            // Vertical Fade
            float fadeBottom = smoothstep(uOriginOffset - 0.05, uOriginOffset + 0.1, vUv.y);
            float fadeTop = smoothstep(1.0, 0.7, vUv.y);
            
            float alpha = f * mask * fadeBottom * fadeTop;
            alpha = smoothstep(0.05, 0.8, alpha) * uDensity;

            vec3 color = mix(uColorStart, uColorEnd, f * 1.5);
            
            gl_FragColor = vec4(color, alpha);
        }
    `;

    const material = new THREE.ShaderMaterial({
        uniforms: uniforms,
        vertexShader: vertexShader,
        fragmentShader: fragmentShader,
        transparent: true,
        depthWrite: false
    });

    const plane = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(plane, material);
    scene.add(mesh);

    const clock = new THREE.Clock();

    function updateOrigin() {
        if (!canvas) return;
        const canvasRect = canvas.getBoundingClientRect();
        
        // Determine origin Y based on metric element position
        let metricTop = canvasRect.top; 
        if (metricElement) {
            const metricRect = metricElement.getBoundingClientRect();
            metricTop = metricRect.top + (metricRect.height * 0.5);
        }
        
        const relativeYFromTop = (metricTop - canvasRect.top) / canvasRect.height;
        const uvY = 1.0 - relativeYFromTop;
        
        uniforms.uOriginOffset.value = uvY;
    }

    function animate() {
        requestAnimationFrame(animate);
        uniforms.uTime.value = clock.getElapsedTime();
        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        const rect = canvas.getBoundingClientRect();
        renderer.setSize(rect.width, rect.height, false);
        uniforms.uResolution.value.set(rect.width, rect.height);
        updateOrigin();
    });

    // Start
    animate();
    setTimeout(updateOrigin, 100);
    
    return {
        uniforms: uniforms,
        updateOrigin: updateOrigin,
        renderer: renderer,
        scene: scene,
        mesh: mesh
    };
}
