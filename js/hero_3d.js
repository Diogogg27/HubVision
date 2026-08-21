// HubVision - HERO 3D: logo com efeito de pedaços voando

(function () {
  if (!window.THREE) return;

  var container = document.getElementById('three-container');
  if (!container) return;

  var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(10, container.clientWidth / container.clientHeight, 1, 10000);
  camera.position.set(0, 0, 1400);

  var root = { renderer: renderer, scene: scene, camera: camera };

  // === Cria a malha da logo com pedaços voando ===
  var logoH = 200;
  var logoW = logoH * (766 / 394); // proporção da imagem
  var segments = 18;

  var geometry = new THREE.PlaneGeometry(logoW, logoH, segments, segments);
  geometry = geometry.toNonIndexed();
  geometry.computeVertexNormals();

  var posAttr = geometry.attributes.position;
  var faceCount = posAttr.count / 3;

  var aDelay = new Float32Array(posAttr.count);
  var aDuration = new Float32Array(posAttr.count);
  var aInit = new Float32Array(posAttr.count * 3);
  var aCtrl0 = new Float32Array(posAttr.count * 3);
  var aCtrl1 = new Float32Array(posAttr.count * 3);

  var maxDelay = 0;

  for (var f = 0; f < faceCount; f++) {
    var i0 = f * 3, i1 = i0 + 1, i2 = i0 + 2;
    var v0 = new THREE.Vector3(posAttr.array[i0 * 3], posAttr.array[i0 * 3 + 1], posAttr.array[i0 * 3 + 2]);
    var v1 = new THREE.Vector3(posAttr.array[i1 * 3], posAttr.array[i1 * 3 + 1], posAttr.array[i1 * 3 + 2]);
    var v2 = new THREE.Vector3(posAttr.array[i2 * 3], posAttr.array[i2 * 3 + 1], posAttr.array[i2 * 3 + 2]);

    var centroid = new THREE.Vector3().addVectors(v0, v1).add(v2).multiplyScalar(1 / 3);
    var dirX = centroid.x > 0 ? 1 : -1;
    var dirY = centroid.y > 0 ? 1 : -1;

    var delay = centroid.length() * THREE.MathUtils.randFloat(0.04, 0.08);
    var duration = THREE.MathUtils.randFloat(1.2, 2.2);
    maxDelay = Math.max(maxDelay, delay);

    var c0x = THREE.MathUtils.randFloat(0, 250) * dirX;
    var c0y = THREE.MathUtils.randFloat(300, 700) * dirY;
    var c0z = THREE.MathUtils.randFloat(-50, 50);
    var c1x = THREE.MathUtils.randFloat(80, 350) * dirX;
    var c1y = THREE.MathUtils.randFloat(0, 200) * dirY;
    var c1z = THREE.MathUtils.randFloat(-50, 50);

    for (var v = 0; v < 3; v++) {
      var vi = f * 3 + v;
      var base = vi * 3;
      aDelay[vi] = delay + Math.random() * 0.3;
      aDuration[vi] = duration;
      aInit[base]     = v0.x + THREE.MathUtils.randFloat(0, 300) * dirX;
      aInit[base + 1] = v0.y + THREE.MathUtils.randFloat(150, 500) * dirY;
      aInit[base + 2] = v0.z + THREE.MathUtils.randFloat(-150, 150);
      aCtrl0[base]     = c0x; aCtrl0[base + 1] = c0y; aCtrl0[base + 2] = c0z;
      aCtrl1[base]     = c1x; aCtrl1[base + 1] = c1y; aCtrl1[base + 2] = c1z;
    }
  }

  var animationDuration = maxDelay + 4 + 1;

  geometry.setAttribute('aDelay', new THREE.BufferAttribute(aDelay, 1));
  geometry.setAttribute('aDuration', new THREE.BufferAttribute(aDuration, 1));
  geometry.setAttribute('aInit', new THREE.BufferAttribute(aInit, 3));
  geometry.setAttribute('aCtrl0', new THREE.BufferAttribute(aCtrl0, 3));
  geometry.setAttribute('aCtrl1', new THREE.BufferAttribute(aCtrl1, 3));

  // Tenta carregar textura, usa cor sólida se falhar
  var useTexture = false;
  var texture = null;

  var material = new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    transparent: true,
    uniforms: {
      uTime: { value: 0 },
      uUseTexture: { value: 0 },
      uTexture: { value: null }
    },
    vertexShader: [
      'uniform float uTime;',
      'attribute float aDelay;',
      'attribute float aDuration;',
      'attribute vec3 aInit;',
      'attribute vec3 aCtrl0;',
      'attribute vec3 aCtrl1;',
      'varying vec2 vUv;',
      'varying vec3 vPos;',
      'vec3 cubicBezier(vec3 p0, vec3 c0, vec3 c1, vec3 p1, float t) {',
      '  float u = 1.0 - t;',
      '  float tt = t * t;',
      '  float uu = u * u;',
      '  return (uu * u) * p0 + 3.0 * (uu * t) * c0 + 3.0 * (u * tt) * c1 + (tt * t) * p1;',
      '}',
      'void main() {',
      '  float tDelay = aDelay;',
      '  float tDuration = aDuration;',
      '  float tTime = clamp(uTime - tDelay, 0.0, tDuration);',
      '  float tProgress = tTime / tDuration;',
      '  vec3 tPosition = cubicBezier(aInit, aCtrl0, aCtrl1, position, tProgress);',
      '  vUv = uv;',
      '  vPos = tPosition;',
      '  gl_Position = projectionMatrix * modelViewMatrix * vec4(tPosition, 1.0);',
      '}'
    ].join('\n'),
    fragmentShader: [
      'uniform sampler2D uTexture;',
      'uniform float uUseTexture;',
      'varying vec2 vUv;',
      'varying vec3 vPos;',
      'void main() {',
      '  if (uUseTexture > 0.5) {',
      '    vec4 texColor = texture2D(uTexture, vUv);',
      '    if (texColor.a < 0.01) discard;',
      '    gl_FragColor = texColor;',
      '  } else {',
      '    vec3 cyan = vec3(0.0, 0.53, 0.75);',
      '    vec3 white = vec3(0.7, 0.95, 1.0);',
      '    float edge = abs(dot(normalize(vPos), vec3(0.0, 0.0, 1.0)));',
      '    vec3 color = mix(white, cyan, edge);',
      '    gl_FragColor = vec4(color, 0.9);',
      '  }',
      '}'
    ].join('\n')
  });

  var mesh = new THREE.Mesh(geometry, material);
  mesh.frustumCulled = false;
  scene.add(mesh);

  var _progress = 0;
  Object.defineProperty(mesh, 'animationProgress', {
    get: function () { return _progress; },
    set: function (v) {
      _progress = v;
      mesh.material.uniforms.uTime.value = animationDuration * v;
    }
  });

  // Tenta carregar textura via data URL (funciona em file://)
  if (window.LOGO_DATA_URL) {
    var img = new Image();
    img.onload = function () {
      texture = new THREE.Texture(img);
      texture.needsUpdate = true;
      texture.minFilter = THREE.LinearFilter;
      mesh.material.uniforms.uTexture.value = texture;
      mesh.material.uniforms.uUseTexture.value = 1;
    };
    img.src = window.LOGO_DATA_URL;
  }

  // Anima
  TweenMax.fromTo(mesh, 3.5,
    { animationProgress: 0 },
    { animationProgress: 1, ease: Power2.easeInOut }
  );

  // === Loop de render ===
  function tick() {
    requestAnimationFrame(tick);
    root.renderer.render(root.scene, root.camera);
  }
  tick();

  function resize() {
    var w = container.clientWidth, h = container.clientHeight;
    if (w === 0 || h === 0) return;
    root.camera.aspect = w / h;
    root.camera.updateProjectionMatrix();
    root.renderer.setSize(w, h);
  }
  window.addEventListener('resize', resize);
  resize();
})();
