import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

interface Viewer3DProps {
    fileUpload: {
        id: number;
        filename_original: string;
        filename_stored: string;
        extension: string;
        disk: string;
    };
}

export default function Viewer3D({ fileUpload }: Viewer3DProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const sceneRef = useRef<{
        scene: THREE.Scene;
        camera: THREE.PerspectiveCamera;
        renderer: THREE.WebGLRenderer;
        controls: OrbitControls;
        animationId: number;
    } | null>(null);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        // Get container dimensions
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Setup scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        // Setup camera
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
        camera.position.set(100, 100, 100);

        // Setup renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // Setup controls
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Add lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        directionalLight.castShadow = true;
        scene.add(directionalLight);

        // Add grid
        const gridHelper = new THREE.GridHelper(200, 20);
        scene.add(gridHelper);

        // Add axes helper for debugging
        const axesHelper = new THREE.AxesHelper(50);
        scene.add(axesHelper);

        // Load the model based on file extension
        const fileUrl = `/3d/${fileUpload.id}/file`;
        console.log('Loading file from:', fileUrl);

        if (fileUpload.extension.toLowerCase() === 'stl') {
            const loader = new STLLoader();
            loader.load(
                fileUrl,
                (geometry: THREE.BufferGeometry) => {
                    console.log('STL loaded successfully');
                    setLoading(false);

                    const material = new THREE.MeshPhongMaterial({
                        color: 0x0077ff,
                        specular: 0x111111,
                        shininess: 200
                    });
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;

                    // Center the geometry
                    geometry.computeBoundingBox();
                    const boundingBox = geometry.boundingBox!;
                    const center = boundingBox.getCenter(new THREE.Vector3());
                    geometry.translate(-center.x, -center.y, -center.z);

                    // Position mesh on the grid
                    geometry.computeBoundingBox();
                    const box = new THREE.Box3().setFromObject(mesh);
                    const size = box.getSize(new THREE.Vector3());
                    mesh.position.y = size.y / 2;

                    console.log('Model size:', size);
                    console.log('Model center:', center);

                    scene.add(mesh);

                    // Adjust camera to fit the model
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const distance = maxDim * 2;
                    camera.position.set(distance, distance, distance);
                    camera.lookAt(0, 0, 0);
                    controls.target.set(0, 0, 0);
                    controls.update();
                },
                (progress) => {
                    const percentComplete = (progress.loaded / progress.total) * 100;
                    console.log('Loading progress:', percentComplete.toFixed(2) + '%');
                },
                (error) => {
                    console.error('Error loading STL:', error);
                    setError('Error al cargar el archivo STL: ' + error.message);
                    setLoading(false);
                }
            );
        } else {
            setError(`Formato de archivo no soportado: ${fileUpload.extension}`);
            setLoading(false);
        }

        // Animation loop
        const animate = () => {
            const animationId = requestAnimationFrame(animate);
            sceneRef.current!.animationId = animationId;
            controls.update();
            renderer.render(scene, camera);
        };

        // Store references
        sceneRef.current = { scene, camera, renderer, controls, animationId: 0 };

        animate();

        // Handle resize
        const handleResize = () => {
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };

        window.addEventListener('resize', handleResize);

        // Cleanup
        return () => {
            window.removeEventListener('resize', handleResize);
            if (sceneRef.current) {
                cancelAnimationFrame(sceneRef.current.animationId);
            }
            container.removeChild(renderer.domElement);
            renderer.dispose();
        };
    }, [fileUpload]);

    return (
        <div ref={containerRef} className="w-full h-full relative">
            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                    <div className="text-white bg-black/70 px-4 py-2 rounded">
                        Cargando modelo 3D...
                    </div>
                </div>
            )}
            {error && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                    <div className="text-red-500 bg-white px-4 py-2 rounded shadow">
                        {error}
                    </div>
                </div>
            )}
        </div>
    );
}
