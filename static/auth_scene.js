import * as THREE from './vendor/three/three.module.js';

const canvas = document.querySelector('#authBookScene');
const fallbackBook = document.querySelector('#authBookFallback');
const panel = document.querySelector('#authStoryPanel');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' });
} catch {
  canvas.hidden = true;
  if (fallbackBook) fallbackBook.hidden = false;
}

let sceneActive = true;
let updateSceneLoop = () => {};
export function setActive(active) {
  sceneActive = Boolean(active);
  updateSceneLoop();
}

if (renderer) {
  if (fallbackBook) fallbackBook.hidden = true;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 60);
  camera.position.set(0, 0, 10);
  scene.add(new THREE.AmbientLight(0xffe7d4, 2.1));
  const keyLight = new THREE.DirectionalLight(0xffc6a3, 3.2);
  keyLight.position.set(-3, 4, 6);
  scene.add(keyLight);
  const rimLight = new THREE.DirectionalLight(0xe84037, 2.4);
  rimLight.position.set(4, -2, 3);
  scene.add(rimLight);

  function pageTexture(side) {
    const surface = document.createElement('canvas');
    surface.width = 512;
    surface.height = 680;
    const ctx = surface.getContext('2d');
    ctx.fillStyle = '#f1e8d7';
    ctx.fillRect(0, 0, 512, 680);
    ctx.fillStyle = 'rgba(177, 83, 65, .1)';
    ctx.fillRect(0, 0, 512, 680);
    ctx.strokeStyle = '#3e3030';
    ctx.lineWidth = 5;
    ctx.strokeRect(32, 32, 448, 616);
    if (side === 'left') {
      ctx.fillStyle = '#262731';
      ctx.fillRect(50, 50, 412, 300);
      ctx.fillStyle = '#b94035';
      ctx.beginPath();
      ctx.arc(290, 150, 75, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#181a22';
      for (let i = 0; i < 9; i++) {
        const x = 50 + i * 51;
        const h = 55 + (i * 37) % 100;
        ctx.fillRect(x, 350 - h, 37, h);
      }
      ctx.strokeRect(50, 370, 190, 258);
      ctx.strokeRect(255, 370, 207, 258);
      ctx.fillStyle = '#453b39';
      ctx.font = '38px serif';
      ctx.fillText('物語', 85, 470);
      ctx.fillText('読む', 285, 560);
      ctx.strokeStyle = '#8b7d71';
      ctx.beginPath();
      ctx.moveTo(80, 528); ctx.lineTo(205, 528);
      ctx.moveTo(80, 552); ctx.lineTo(186, 552);
      ctx.stroke();
    } else {
      ctx.strokeRect(50, 50, 412, 385);
      ctx.fillStyle = '#2a2930';
      ctx.fillRect(61, 61, 390, 363);
      ctx.fillStyle = '#c7473c';
      ctx.beginPath();
      ctx.arc(328, 160, 83, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#171820';
      ctx.beginPath();
      ctx.moveTo(105, 415); ctx.lineTo(232, 225); ctx.lineTo(310, 415);
      ctx.fill();
      ctx.strokeStyle = '#484344';
      ctx.strokeRect(50, 451, 412, 177);
      ctx.fillStyle = '#484344';
      for (let i = 0; i < 5; i++) ctx.fillRect(75, 479 + i * 28, 320 - i * 23, 7);
      ctx.fillStyle = '#b63d35';
      ctx.fillRect(75, 600, 120, 8);
    }
    const texture = new THREE.CanvasTexture(surface);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
    return texture;
  }

  function frontCoverTexture() {
    const surface = document.createElement('canvas');
    surface.width = 512;
    surface.height = 680;
    const ctx = surface.getContext('2d');
    const texture = new THREE.CanvasTexture(surface);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = Math.min(renderer.capabilities.getMaxAnisotropy(), 8);
    texture.wrapS = THREE.RepeatWrapping;
    texture.repeat.x = -1;
    texture.offset.x = 1;
    const logo = new Image();
    function paint() {
      ctx.fillStyle = '#17141c';
      ctx.fillRect(0, 0, 512, 680);
      const glow = ctx.createRadialGradient(256, 235, 35, 256, 235, 300);
      glow.addColorStop(0, 'rgba(173, 36, 39, .32)');
      glow.addColorStop(1, 'rgba(18, 14, 23, 0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, 512, 680);
      ctx.strokeStyle = '#b63c36';
      ctx.lineWidth = 10;
      ctx.strokeRect(23, 23, 466, 634);
      ctx.strokeStyle = '#9a5549';
      ctx.lineWidth = 2;
      ctx.strokeRect(39, 39, 434, 602);
      if (logo.complete && logo.naturalWidth) ctx.drawImage(logo, 116, 105, 280, 280);
      ctx.textAlign = 'center';
      ctx.font = '800 66px Manrope, sans-serif';
      ctx.fillStyle = '#f5eee4';
      ctx.fillText('YOMU', 256, 476);
      ctx.fillStyle = '#d7433b';
      ctx.fillText('SEKAI', 256, 550);
      ctx.fillStyle = '#a9978b';
      ctx.font = '27px Georgia, serif';
      ctx.fillText('物語を、もっと近くに。', 256, 605);
      texture.needsUpdate = true;
    }
    logo.onload = paint;
    logo.src = '/static/assets/auth/yomu-logo.png';
    paint();
    return texture;
  }

  const book = new THREE.Group();
  const bookSurface = new THREE.Group();
  book.add(bookSurface);
  scene.add(book);
  const coverMaterial = new THREE.MeshStandardMaterial({ color: 0x33171b, roughness: 0.78, metalness: 0.08 });
  const pageEdge = new THREE.MeshStandardMaterial({ color: 0xe7ddc9, roughness: 0.96 });
  const redEdge = new THREE.MeshStandardMaterial({ color: 0xa02e29, roughness: 0.7, metalness: 0.08 });
  const rightHalf = new THREE.Group();
  bookSurface.add(rightHalf);
  for (const side of [-1, 1]) {
    const half = side === 1 ? rightHalf : bookSurface;
    const cover = new THREE.Mesh(new THREE.BoxGeometry(1.6, 2.08, 0.07), coverMaterial);
    cover.position.set(side * 0.79, 0, -0.16);
    cover.rotation.y = side === 1 ? 0 : 0.12;
    half.add(cover);
    const edge = new THREE.Mesh(new THREE.BoxGeometry(1.53, 2.01, 0.08), redEdge);
    edge.position.set(side * 0.77, 0, -0.09);
    half.add(edge);
    for (let i = 0; i < 5; i++) {
      const sheet = new THREE.Mesh(new THREE.BoxGeometry(1.48 - i * 0.009, 1.96 - i * 0.009, 0.017), pageEdge);
      sheet.position.set(side * 0.75, 0, -0.03 + i * 0.021);
      sheet.rotation.y = side * -0.075;
      half.add(sheet);
    }
    const illustration = new THREE.Mesh(
      new THREE.PlaneGeometry(1.46, 1.94),
      new THREE.MeshStandardMaterial({ map: pageTexture(side === -1 ? 'left' : 'right'), roughness: 1, side: THREE.DoubleSide })
    );
    illustration.position.set(side * 0.75, 0, 0.093);
    illustration.rotation.y = side * -0.075;
    half.add(illustration);
  }
  const spine = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 2.1, 12), redEdge);
  spine.position.z = 0.03;
  bookSurface.add(spine);

  // A face impressa fica no verso da metade direita, que fecha sobre a esquerda.
  const coverArt = new THREE.Mesh(
    new THREE.PlaneGeometry(1.52, 2.02),
    new THREE.MeshBasicMaterial({ map: frontCoverTexture(), side: THREE.DoubleSide })
  );
  coverArt.position.set(0.79, 0, -0.28);
  rightHalf.add(coverArt);

  function glyphTexture(character) {
    const surface = document.createElement('canvas');
    surface.width = 128;
    surface.height = 128;
    const ctx = surface.getContext('2d');
    ctx.clearRect(0, 0, 128, 128);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = '#d84c3e';
    ctx.shadowBlur = 16;
    ctx.font = '96px "Yu Mincho", "Noto Serif JP", serif';
    ctx.fillStyle = '#ffe4ca';
    ctx.fillText(character, 64, 66);
    const texture = new THREE.CanvasTexture(surface);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }

  const glyphs = [];
  const characters = [...'物語世界読夢光旅月心頁想'];
  for (const [index, character] of characters.entries()) {
    const material = new THREE.MeshBasicMaterial({
      map: glyphTexture(character), transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false
    });
    const size = 0.25 + (index % 3) * 0.055;
    const glyph = new THREE.Mesh(new THREE.PlaneGeometry(size, size), material);
    glyph.userData = { x: ((index * 1.37) % 3.8) - 1.9, phase: index / characters.length, drift: index * 1.3 };
    book.add(glyph);
    glyphs.push(glyph);
  }

  const startedAt = performance.now();
  function resize() {
    const { width, height } = panel.getBoundingClientRect();
    if (!width || !height) return;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    const viewHeight = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.position.z;
    const viewWidth = viewHeight * camera.aspect;
    const mobile = width < 600;
    book.position.set(mobile ? -viewWidth * 0.09 : -viewWidth * 0.19, -viewHeight * (mobile ? 0.32 : 0.27), 0);
    book.scale.setScalar(mobile ? (width < 450 ? 0.73 : 0.82) : Math.min(1.1, width / 700));
    render(startedAt);
  }

  let pointerX = 0;
  let pointerY = 0;
  panel.addEventListener('pointermove', event => {
    const rect = panel.getBoundingClientRect();
    pointerX = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    pointerY = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
  }, { passive: true });
  panel.addEventListener('pointerleave', () => { pointerX = 0; pointerY = 0; });

  function render(time) {
    const t = Math.max(0, (time - startedAt) * 0.001);
    bookSurface.rotation.set(-0.16 + Math.sin(t * 0.46) * 0.025 - pointerY * 0.035, -0.06 + Math.sin(t * 0.31) * 0.075 + pointerX * 0.13, -0.12 + Math.sin(t * 0.35) * 0.025);
    bookSurface.position.y = Math.sin(t * 0.72) * 0.055;
    const phase = t % 11;
    const ease = value => value * value * (3 - 2 * value);
    const closed = phase < 3 ? 0 : phase < 5 ? ease((phase - 3) / 2) : phase < 8 ? 1 : phase < 10 ? 1 - ease((phase - 8) / 2) : 0;
    rightHalf.rotation.y = -Math.PI * closed;
    for (const glyph of glyphs) {
      const rise = (t * 0.12 + glyph.userData.phase) % 1;
      glyph.position.set(glyph.userData.x + Math.sin(t * 0.55 + glyph.userData.drift) * 0.1, 0.2 + rise * 1.8, 0.35 + (glyph.userData.phase % 0.4));
      glyph.rotation.set(0, Math.sin(t * 0.4 + glyph.userData.drift) * 0.27, Math.sin(t * 0.6 + glyph.userData.drift) * 0.14);
      glyph.material.opacity = Math.sin(Math.PI * rise) * (1 - closed * 0.62) * 0.88;
    }
    renderer.render(scene, camera);
  }

  const observer = new ResizeObserver(resize);
  observer.observe(panel);
  resize();
  updateSceneLoop = () => {
    if (reducedMotion) {
      renderer.setAnimationLoop(null);
      if (sceneActive) render(performance.now());
      return;
    }
    renderer.setAnimationLoop(sceneActive ? time => { if (!document.hidden) render(time); } : null);
    if (sceneActive) resize();
  };
  updateSceneLoop();
}
