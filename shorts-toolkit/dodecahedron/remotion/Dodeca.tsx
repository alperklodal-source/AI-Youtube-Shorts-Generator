import React, { useMemo, useEffect } from "react";
import * as THREE from "three";
import { useThree } from "@react-three/fiber";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

// Build a hollow Roman dodecahedron: 12 bronze pentagonal plates, each with a
// circular hole of a different size, and a small knob on each of the 20 vertices.
function buildFaces() {
  const g = new THREE.DodecahedronGeometry(1, 0).toNonIndexed();
  const pos = g.getAttribute("position");
  const faces: { normal: THREE.Vector3; verts: THREE.Vector3[] }[] = [];
  for (let i = 0; i < pos.count; i += 3) {
    const a = new THREE.Vector3().fromBufferAttribute(pos, i);
    const b = new THREE.Vector3().fromBufferAttribute(pos, i + 1);
    const c = new THREE.Vector3().fromBufferAttribute(pos, i + 2);
    const n = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a)).normalize();
    let f = faces.find((x) => x.normal.dot(n) > 0.999);
    if (!f) { f = { normal: n, verts: [] }; faces.push(f); }
    for (const v of [a, b, c]) if (!f.verts.some((w) => w.distanceTo(v) < 1e-4)) f.verts.push(v);
  }
  return faces;
}

const HOLE_RATIOS = [0.12, 0.2, 0.28, 0.16, 0.34, 0.24, 0.1, 0.3, 0.18, 0.38, 0.22, 0.14];

export const DodecaMesh: React.FC<{ rotY: number; rotX: number; scale: number; glow: number }> = ({ rotY, rotX, scale, glow }) => {
  const { gl, scene } = useThree();
  useEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    (scene as any).environmentIntensity = 2.2;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.0;
  }, [gl, scene]);

  const { plates, knobs } = useMemo(() => {
    const faces = buildFaces();
    const plates: { geo: THREE.BufferGeometry; quat: THREE.Quaternion; pos: THREE.Vector3 }[] = [];
    const knobSet: THREE.Vector3[] = [];
    faces.forEach((f, idx) => {
      const center = f.verts.reduce((s, v) => s.add(v), new THREE.Vector3()).multiplyScalar(1 / f.verts.length);
      const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), f.normal);
      const inv = quat.clone().invert();
      const local = f.verts.map((v) => v.clone().sub(center).applyQuaternion(inv));
      local.sort((p, q) => Math.atan2(p.y, p.x) - Math.atan2(q.y, q.x));
      const shape = new THREE.Shape(local.map((p) => new THREE.Vector2(p.x, p.y)));
      const inR = local[0].length() * Math.cos(Math.PI / 5);
      const hole = new THREE.Path();
      hole.absarc(0, 0, inR * HOLE_RATIOS[idx] * 2.2, 0, Math.PI * 2, true);
      shape.holes.push(hole);
      const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.05, bevelEnabled: true, bevelThickness: 0.015, bevelSize: 0.015, bevelSegments: 2, curveSegments: 40 });
      geo.translate(0, 0, -0.05);
      plates.push({ geo, quat, pos: center });
      f.verts.forEach((v) => { if (!knobSet.some((w) => w.distanceTo(v) < 1e-4)) knobSet.push(v.clone()); });
    });
    return { plates, knobs: knobSet };
  }, []);

  const bronze = useMemo(() => new THREE.MeshStandardMaterial({ color: new THREE.Color("#a8743a"), metalness: 0.92, roughness: 0.38 }), []);
  const patina = useMemo(() => new THREE.MeshStandardMaterial({ color: new THREE.Color("#7d5a2c"), metalness: 0.85, roughness: 0.5 }), []);
  bronze.emissive = new THREE.Color("#ff9a3c");
  bronze.emissiveIntensity = glow * 0.12;

  return (
    <group rotation={[rotX, rotY, 0.25]} scale={scale}>
      {plates.map((p, i) => (
        <mesh key={i} geometry={p.geo} position={p.pos} quaternion={p.quat} material={bronze} />
      ))}
      {knobs.map((k, i) => (
        <mesh key={"k" + i} position={k.clone().multiplyScalar(1.07)} material={patina}>
          <sphereGeometry args={[0.085, 24, 24]} />
        </mesh>
      ))}
    </group>
  );
};
