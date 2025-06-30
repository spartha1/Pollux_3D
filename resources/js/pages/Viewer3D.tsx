import { useCallback, useEffect, useRef, useState, useLayoutEffect } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
// @ts-expect-error - Three.js examples don't have TypeScript declarations
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export type ViewTypeId = '2d' | 'wireframe' | '3d';

export interface ViewType {
    id: ViewTypeId;
    name: string;
    description: string;
}

export interface Preview {
    id: number;
    file_upload_id: number;
    image_path: string;
    render_type: ViewTypeId;
    created_at: string | null;
}

export interface FileUpload {
    id: number;
    filename_original: string;
    filename_stored: string;
    extension: string;
    disk: string;
    storage_path?: string;
}

export interface Viewer3DProps {
    fileUpload: FileUpload;
    previews?: Partial<Record<ViewTypeId, Preview>>;
    viewTypes: ViewType[];
}

export default function Viewer3D({ fileUpload, previews = {}, viewTypes }: Viewer3DProps) {
    const mountRef = useRef<HTMLDivElement>(null);
    const sceneRef = useRef<THREE.Scene | null>(null);
    const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
    const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
    const controlsRef = useRef<OrbitControls | null>(null);
    const frameRef = useRef<number | null>(null);
    const meshRef = useRef<THREE.Mesh | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const cleanupInProgressRef = useRef(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeView, setActiveView] = useState<ViewTypeId>(() => {
        const extension = fileUpload.extension.toLowerCase();
        if (extension === 'stl' && viewTypes.some(type => type.id === '3d')) {
            return '3d';
        }
        const availableTypes = Object.keys(previews) as ViewTypeId[];
        if (availableTypes.length > 0) {
            return availableTypes[0];
        }
        return viewTypes[0]?.id || '2d';
    });

    // Cleanup function
    const cleanup = useCallback(() => {
        // Prevent multiple cleanups
        if (cleanupInProgressRef.current) {
            return;
        }
        cleanupInProgressRef.current = true;

        // Stop animation frame first
        if (frameRef.current !== null) {
            cancelAnimationFrame(frameRef.current);
            frameRef.current = null;
        }

        // Store canvas reference if it exists
        if (rendererRef.current?.domElement && !canvasRef.current) {
            canvasRef.current = rendererRef.current.domElement;
        }

        // Dispose mesh and its resources
        if (meshRef.current) {
            if (meshRef.current.geometry) {
                meshRef.current.geometry.dispose();
            }
            if (meshRef.current.material) {
                if (Array.isArray(meshRef.current.material)) {
                    meshRef.current.material.forEach(m => m.dispose());
                } else {
                    meshRef.current.material.dispose();
                }
            }
            if (meshRef.current.parent) {
                meshRef.current.parent.remove(meshRef.current);
            }
            meshRef.current = null;
        }

        // Dispose scene objects
        if (sceneRef.current) {
            sceneRef.current.traverse((object) => {
                if (object instanceof THREE.Mesh) {
                    if (object.geometry) {
                        object.geometry.dispose();
                    }
                    if (object.material) {
                        if (Array.isArray(object.material)) {
                            object.material.forEach(m => m.dispose());
                        } else {
                            object.material.dispose();
                        }
                    }
                }
            });
            sceneRef.current = null;
        }

        // Dispose controls
        if (controlsRef.current) {
            controlsRef.current.dispose();
            controlsRef.current = null;
        }

        // Dispose renderer
        if (rendererRef.current) {
            rendererRef.current.dispose();
            rendererRef.current.setAnimationLoop(null);
            rendererRef.current = null;
        }

        // Safely remove canvas from DOM
        try {
            if (canvasRef.current && mountRef.current?.contains(canvasRef.current)) {
                mountRef.current.removeChild(canvasRef.current);
            }
        } catch (error) {
            console.warn('Error removing canvas:', error);
        }

        canvasRef.current = null;
        cleanupInProgressRef.current = false;
    }, []);

    // Initialize scene
    const initScene = useCallback(() => {
        if (!mountRef.current) return;

        const container = mountRef.current;
        const { clientWidth: width, clientHeight: height } = container;

        // Create scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);
        sceneRef.current = scene;

        // Create camera
        const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.set(100, 100, 100);
        cameraRef.current = camera;

        // Create renderer only if not exists
        if (!rendererRef.current) {
            const renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance'
            });
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            rendererRef.current = renderer;
            canvasRef.current = renderer.domElement;
        }

        // Only append canvas if it exists and container doesn't already have it
        if (canvasRef.current && !container.contains(canvasRef.current)) {
            container.appendChild(canvasRef.current);
        }

        // Create controls
        const controls = new OrbitControls(cameraRef.current, canvasRef.current);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controlsRef.current = controls;

        // Add lights
        const ambientLight = new THREE.AmbientLight(0x404040);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(1, 1, 1);
        directionalLight.castShadow = true;
        scene.add(directionalLight);

        // Add grid and axes
        const gridHelper = new THREE.GridHelper(200, 20);
        scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(50);
        scene.add(axesHelper);

        // Handle resize
        const handleResize = () => {
            if (!container || !rendererRef.current || !cameraRef.current) return;
            const { clientWidth: width, clientHeight: height } = container;
            cameraRef.current.aspect = width / height;
            cameraRef.current.updateProjectionMatrix();
            rendererRef.current.setSize(width, height);
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    // Animation loop
    const animate = useCallback(() => {
        if (!rendererRef.current || !sceneRef.current || !cameraRef.current || !controlsRef.current) return;

        controlsRef.current.update();
        rendererRef.current.render(sceneRef.current, cameraRef.current);
        frameRef.current = requestAnimationFrame(animate);
    }, []);

    // Load STL model
    const loadSTL = useCallback(() => {
        if (!sceneRef.current || !cameraRef.current || !controlsRef.current) return;

        const scene = sceneRef.current;
        const camera = cameraRef.current;
        const controls = controlsRef.current;

        setLoading(true);
        setError(null);

        console.log('Loading STL file...');
        const fileUrl = `/3d/${fileUpload.id}/download`;
        console.log('STL file URL:', fileUrl);

        const loader = new STLLoader();
        loader.load(
            fileUrl,
            (geometry) => {
                console.log('STL loaded successfully');
                setLoading(false);

                // Remove existing mesh if any
                if (meshRef.current) {
                    scene.remove(meshRef.current);
                    meshRef.current.geometry.dispose();
                    if (meshRef.current.material) {
                        if (Array.isArray(meshRef.current.material)) {
                            meshRef.current.material.forEach(m => m.dispose());
                        } else {
                            meshRef.current.material.dispose();
                        }
                    }
                }

                const material = new THREE.MeshPhongMaterial({
                    color: 0x0077ff,
                    specular: 0x111111,
                    shininess: 200,
                    side: THREE.DoubleSide
                });

                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                meshRef.current = mesh;

                // Center geometry
                geometry.computeBoundingBox();
                const boundingBox = geometry.boundingBox!;
                const center = boundingBox.getCenter(new THREE.Vector3());
                mesh.position.set(-center.x, -center.y, -center.z);

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
    }, [fileUpload.id]);

    // Initialize Three.js scene
    useLayoutEffect(() => {
        // Run init only for 3D STL view
        if (activeView === '3d' && fileUpload.extension.toLowerCase() === 'stl') {
            // Clear any previous cleanup state
            cleanupInProgressRef.current = false;

            // Initialize scene and get resize cleanup
            const cleanupResize = initScene();

            // Load STL model
            loadSTL();

            // Start animation loop
            animate();

            // Return cleanup function
            return () => {
                try {
                    // First stop the resize listener
                    if (cleanupResize) cleanupResize();

                    // Then perform Three.js cleanup
                    cleanup();
                } catch (error) {
                    console.warn('Error during cleanup:', error);
                }
            };
        }
    }, [activeView, fileUpload.extension, fileUpload.id, initScene, loadSTL, animate, cleanup]);

    // Helper function to get preview URL
    const getPreviewUrl = useCallback((viewType: ViewTypeId): string | null => {
        const preview = previews[viewType];
        if (!preview) return null;

        if (viewType === '2d' || viewType === 'wireframe') {
            return preview.image_path;
        }

        if (viewType === '3d' && fileUpload.extension.toLowerCase() !== 'stl') {
            return preview.image_path;
        }

        return null;
    }, [previews, fileUpload.extension]);

    // Ensure viewTypes is defined
    if (!viewTypes?.length) {
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
                        {activeView === '3d' && fileUpload.extension.toLowerCase() === 'stl' ? (
                            <div ref={mountRef} className="w-full h-[600px] bg-gray-100 relative">
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
