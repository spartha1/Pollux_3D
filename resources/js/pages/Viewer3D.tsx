import { useCallback, useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

interface ViewType {
    id: '2d' | 'wireframe' | '3d';
    name: string;
    description: string;
}

interface Preview {
    id: number;
    file_upload_id: number;
    image_path: string;
    render_type: '2d' | 'wireframe' | '3d';
    created_at: string;
}

interface Viewer3DProps {
    fileUpload: {
        id: number;
        filename_original: string;
        filename_stored: string;
        extension: string;
        disk: string;
        storage_path: string;
    };
    previews: Record<string, Preview>;
    viewTypes: ViewType[];
}

export default function Viewer3D({ fileUpload, previews, viewTypes }: Viewer3DProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeView, setActiveView] = useState<'2d' | 'wireframe' | '3d'>(() => {
        // Initialize with '3d' for STL files, or first available preview type for others
        const extension = fileUpload.extension.toLowerCase();
        if (extension === 'stl') {
            return '3d';
        }
        // For other files, check if we have previews
        if (previews && Object.keys(previews).length > 0) {
            return Object.keys(previews)[0] as '2d' | 'wireframe' | '3d';
        }
        return '2d';
    });

    const getPreviewUrl = useCallback((type: string) => {
        const preview = previews[type];
        if (!preview) return null;
        return `/storage/${preview.image_path}`;
    }, [previews]);

    const render3DView = useCallback(() => {
        if (!containerRef.current || activeView !== '3d') return;

        console.log('Initializing 3D viewer with file:', fileUpload);

        const container = containerRef.current;
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
        container.innerHTML = '';
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

        // Add grid and axes
        const gridHelper = new THREE.GridHelper(200, 20);
        scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(50);
        scene.add(axesHelper);

        // Load the model based on file extension
        const extension = fileUpload.extension.toLowerCase();

        if (extension === 'stl') {
            console.log('Loading STL file...');
            const fileUrl = `/storage/${fileUpload.storage_path}`;
            console.log('STL file URL:', fileUrl);

            const loader = new STLLoader();
            loader.load(
                fileUrl,
                (geometry) => {
                    console.log('STL loaded successfully');
                    setLoading(false);

                    const material = new THREE.MeshPhongMaterial({
                        color: 0x0077ff,
                        specular: 0x111111,
                        shininess: 200,
                        side: THREE.DoubleSide
                    });
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;

                    // Center the geometry
                    geometry.computeBoundingBox();
                    const boundingBox = geometry.boundingBox!;
                    const center = boundingBox.getCenter(new THREE.Vector3());
                    mesh.position.set(-center.x, -center.y, -center.z);

                    // Add to scene
                    scene.add(mesh);

                    // Adjust camera
                    const box = new THREE.Box3().setFromObject(mesh);
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const fov = camera.fov * (Math.PI / 180);
                    const cameraDistance = Math.abs(maxDim / Math.sin(fov / 2)) * 1.5;

                    camera.position.set(cameraDistance, cameraDistance, cameraDistance);
                    camera.lookAt(0, 0, 0);
                    controls.target.set(0, 0, 0);
                    controls.update();

                    renderer.render(scene, camera);
                },
                (xhr) => {
                    console.log('Loading progress:', (xhr.loaded / xhr.total) * 100 + '%');
                },
                (error) => {
                    console.error('Error loading STL:', error);
                    setError('Error loading STL file: ' + error.message);
                    setLoading(false);
                }
            );
        } else if (extension === 'step' || extension === 'stp') {
            setLoading(false);
            // For STEP files, show the preview image if available
            const preview = previews['3d'];
            if (!preview) {
                setError('No 3D preview available for this STEP file');
            }
        }

        // Animation loop
        const animate = () => {
            const animationId = requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
            return animationId;
        };

        const animationId = animate();

        // Cleanup function
        return () => {
            cancelAnimationFrame(animationId);
            renderer.dispose();
            scene.clear();
        };
    }, [fileUpload, activeView, previews]);

    useEffect(() => {
        const cleanup = render3DView();
        return () => cleanup?.();
    }, [render3DView]);

    // Ensure viewTypes is defined and has content
    if (!viewTypes || !Array.isArray(viewTypes)) {
        return (
            <div className="py-6 relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-white p-4 rounded-lg shadow">
                        <p className="text-red-500">Error: View types not properly configured</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="py-6 relative">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col space-y-4">
                    {/* View Type Selector */}
                    <div className="flex space-x-4 bg-white p-4 rounded-lg shadow">
                        {viewTypes.map((type) => (
                            <button
                                key={type.id}
                                onClick={() => setActiveView(type.id)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    activeView === type.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                                title={type.description}
                            >
                                {type.name}
                            </button>
                        ))}
                    </div>

                    {/* Preview Display */}
                    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                        {activeView === '3d' ? (
                            <div ref={containerRef} className="w-full h-[600px] bg-gray-100 relative">
                                {loading && (
                                    <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                        <div className="text-white bg-black/70 px-4 py-2 rounded">
                                            Loading 3D model...
                                        </div>
                                    </div>
                                )}
                                {error && (
                                    <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                        <div className="text-white bg-black/70 px-4 py-2 rounded">
                                            {error}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="aspect-w-16 aspect-h-9">
                                {(() => {
                                    const url = getPreviewUrl(activeView);
                                    return url ? (
                                        <img
                                            src={url}
                                            alt={`${activeView} view`}
                                            className="object-contain w-full h-full"
                                        />
                                    ) : (
                                        <div className="flex items-center justify-center h-full">
                                            <span className="text-gray-500">
                                                No preview available for {activeView} view
                                            </span>
                                        </div>
                                    );
                                })()}
                            </div>
                        )}
                    </div>

                    {/* File Information */}
                    <div className="bg-white rounded-lg shadow p-4">
                        <h2 className="text-lg font-medium text-gray-900 mb-2">
                            File Information
                        </h2>
                        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <div>
                                <dt className="text-sm font-medium text-gray-500">
                                    Filename
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                    {fileUpload.filename_original}
                                </dd>
                            </div>
                            <div>
                                <dt className="text-sm font-medium text-gray-500">
                                    Available Views
                                </dt>
                                <dd className="mt-1 text-sm text-gray-900">
                                    {Object.keys(previews).length} views
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
            </div>
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
