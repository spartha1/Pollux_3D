import { useRef, useState, useLayoutEffect } from 'react';
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
    analysis_result?: {
        dimensions?: {
            x?: number;
            y?: number;
            z?: number;
            width?: number;
            height?: number;
            depth?: number;
        };
        volume?: number;
        area?: number;
        layers?: number;
        metadata?: {
            vertices?: number;
            faces?: number;
            triangles?: number;
            edges?: number;
            format?: string;
            file_size_bytes?: number;
            center_of_mass?: {
                x?: number;
                y?: number;
                z?: number;
            };
            bbox_min?: {
                x?: number;
                y?: number;
                z?: number;
            };
            bbox_max?: {
                x?: number;
                y?: number;
                z?: number;
            };
        };
        analysis_time_ms?: number;
    };
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
    const cleanupInProgressRef = useRef(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [canvasElement, setCanvasElement] = useState<HTMLCanvasElement | null>(null);
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
    const cleanup = () => {
        if (cleanupInProgressRef.current) return;
        cleanupInProgressRef.current = true;

        // Cancel animation frame
        if (frameRef.current !== null) {
            cancelAnimationFrame(frameRef.current);
            frameRef.current = null;
        }

        // Clean up mesh
        if (meshRef.current) {
            if (meshRef.current.parent) {
                meshRef.current.parent.remove(meshRef.current);
            }
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
            meshRef.current = null;
        }

        // Clean up controls
        if (controlsRef.current) {
            controlsRef.current.dispose();
            controlsRef.current = null;
        }

        // Clean up scene
        if (sceneRef.current) {
            sceneRef.current.traverse((object) => {
                if (object instanceof THREE.Mesh) {
                    if (object.geometry) object.geometry.dispose();
                    if (object.material) {
                        if (Array.isArray(object.material)) {
                            object.material.forEach(m => m.dispose());
                        } else {
                            object.material.dispose();
                        }
                    }
                }
            });
            sceneRef.current.clear();
            sceneRef.current = null;
        }

        // Clear canvas state when cleaning up
        setCanvasElement(null);

        cleanupInProgressRef.current = false;
    };

    // Initialize 3D scene
    const init3DScene = () => {
        if (!mountRef.current) return false;

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

        // Create or reuse renderer
        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance'
        });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        rendererRef.current = renderer;

        // Set canvas element in state to trigger React re-render
        setCanvasElement(renderer.domElement);

        // Create controls
        const controls = new OrbitControls(camera, renderer.domElement);
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

        // Add helpers
        const gridHelper = new THREE.GridHelper(200, 20);
        scene.add(gridHelper);

        const axesHelper = new THREE.AxesHelper(50);
        scene.add(axesHelper);

        return true;
    };

    // Load STL model
    const loadSTL = () => {
        if (!sceneRef.current) return;

        setLoading(true);
        setError(null);

        const fileUrl = `/3d/${fileUpload.id}/download`;
        const loader = new STLLoader();

        loader.load(
            fileUrl,
            (geometry) => {
                if (!sceneRef.current) {
                    geometry.dispose();
                    return;
                }

                try {
                    // Remove existing mesh
                    if (meshRef.current) {
                        sceneRef.current.remove(meshRef.current);
                        meshRef.current.geometry?.dispose();
                        if (Array.isArray(meshRef.current.material)) {
                            meshRef.current.material.forEach(m => m.dispose());
                        } else {
                            meshRef.current.material?.dispose();
                        }
                    }

                    // Create material based on view type
                    const material = activeView === 'wireframe'
                        ? new THREE.MeshBasicMaterial({ color: 0x0066cc, wireframe: true, transparent: true, opacity: 0.8 })
                        : new THREE.MeshLambertMaterial({ color: 0x0066cc });

                    // Create mesh
                    const mesh = new THREE.Mesh(geometry, material);
                    sceneRef.current.add(mesh);
                    meshRef.current = mesh;

                    // Center the model
                    geometry.computeBoundingBox();
                    const box = geometry.boundingBox!;
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());

                    const maxDim = Math.max(size.x, size.y, size.z);
                    const distance = maxDim * 2;

                    if (cameraRef.current && controlsRef.current) {
                        cameraRef.current.position.set(distance, distance, distance);
                        cameraRef.current.lookAt(center);
                        controlsRef.current.target.copy(center);
                        controlsRef.current.update();
                    }

                    setLoading(false);
                } catch (error) {
                    console.error('Error creating mesh:', error);
                    setError('Error loading 3D model');
                    setLoading(false);
                }
            },
            undefined,
            (error) => {
                console.error('Error loading STL:', error);
                setError('Failed to load 3D model');
                setLoading(false);
            }
        );
    };

    // Animation loop
    const animate = () => {
        if (!rendererRef.current || !sceneRef.current || !cameraRef.current || !controlsRef.current) return;

        controlsRef.current.update();
        rendererRef.current.render(sceneRef.current, cameraRef.current);
        frameRef.current = requestAnimationFrame(animate);
    };

    // Render 2D view
    const render2DView = () => {
        // Clean up 3D resources first
        cleanup();

        // Dispose the renderer to free WebGL context
        if (rendererRef.current) {
            rendererRef.current.dispose();
            rendererRef.current.setAnimationLoop(null);
            rendererRef.current = null;
        }

        // Clear the canvas state
        setCanvasElement(null);

        setLoading(false);
        setError(null);
    };

    // Handle resize
    const handleResize = () => {
        if (!mountRef.current || !cameraRef.current || !rendererRef.current) return;
        const { clientWidth: width, clientHeight: height } = mountRef.current;
        cameraRef.current.aspect = width / height;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(width, height);
    };

    // Main effect
    useLayoutEffect(() => {
        let resizeCleanup: (() => void) | undefined;

        if (activeView === '3d' || activeView === 'wireframe') {
            if (fileUpload.extension.toLowerCase() === 'stl') {
                // Clean up first
                cleanup();

                // For switching back from 2D to 3D, ensure renderer is recreated
                if (!rendererRef.current) {
                    // Renderer was disposed, we need to recreate it
                }

                // Initialize 3D scene
                if (init3DScene()) {
                    // Load model
                    loadSTL();

                    // Start animation
                    animate();

                    // Add resize listener
                    window.addEventListener('resize', handleResize);
                    resizeCleanup = () => window.removeEventListener('resize', handleResize);
                }
            }
        } else if (activeView === '2d') {
            // Clean up 3D and render 2D
            setLoading(true); // Set loading state for 2D
            render2DView();
        }

        return () => {
            if (resizeCleanup) resizeCleanup();
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeView, fileUpload.id, fileUpload.extension]);

    // Cleanup on unmount
    useLayoutEffect(() => {
        return () => {
            cleanup();

            // Dispose renderer on unmount
            if (rendererRef.current) {
                rendererRef.current.dispose();
                rendererRef.current.setAnimationLoop(null);
                rendererRef.current = null;
            }

            // Clear canvas state
            setCanvasElement(null);
        };
    }, []);

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
                        <div ref={mountRef} className="w-full h-[600px] bg-gray-100 relative">
                            {/* Render 3D canvas or 2D preview */}
                            {canvasElement && (
                                <div
                                    ref={(div) => {
                                        if (div && canvasElement && !div.contains(canvasElement)) {
                                            // Clear any existing content first
                                            div.innerHTML = '';
                                            div.appendChild(canvasElement);
                                        }
                                    }}
                                    className="w-full h-full"
                                />
                            )}

                            {/* 2D Preview for non-3D views */}
                            {!canvasElement && activeView === '2d' && (
                                <>
                                    {previews['2d'] ? (
                                        <img
                                            src={`/storage/${previews['2d'].image_path}`}
                                            alt="2D preview"
                                            className="w-full h-full object-contain"
                                            onLoad={() => {
                                                setLoading(false);
                                            }}
                                            onError={(e) => {
                                                console.error('Failed to load 2D preview:', e);
                                                setError('Failed to load 2D preview');
                                                setLoading(false);
                                            }}
                                        />
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-gray-500">
                                            <div className="text-center">
                                                <p>2D preview not available</p>
                                                <p className="text-sm">Generate a preview to see the 2D view</p>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}

                            {/* Loading overlay */}
                            {loading && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                    <div className="text-white bg-black/70 px-4 py-2 rounded">
                                        Loading {activeView} view...
                                    </div>
                                </div>
                            )}

                            {/* Error overlay */}
                            {error && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                                    <div className="text-white bg-black/70 px-4 py-2 rounded">
                                        {error}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* File Information */}
                    <div className="bg-white rounded-lg shadow p-4">
                        <h2 className="text-lg font-medium text-gray-900 mb-4">
                            File Information
                        </h2>
                        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Filename</dt>
                                <dd className="text-sm text-gray-900">{fileUpload.filename_original}</dd>
                            </div>
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Type</dt>
                                <dd className="text-sm text-gray-900">{fileUpload.extension.toUpperCase()}</dd>
                            </div>

                            {/* Dimensions */}
                            {fileUpload.analysis_result?.dimensions && (
                                <>
                                    {fileUpload.analysis_result.dimensions.width && (
                                        <div>
                                            <dt className="text-sm font-medium text-gray-500">Width</dt>
                                            <dd className="text-sm text-gray-900">{fileUpload.analysis_result.dimensions.width.toFixed(2)} mm</dd>
                                        </div>
                                    )}
                                    {fileUpload.analysis_result.dimensions.height && (
                                        <div>
                                            <dt className="text-sm font-medium text-gray-500">Height</dt>
                                            <dd className="text-sm text-gray-900">{fileUpload.analysis_result.dimensions.height.toFixed(2)} mm</dd>
                                        </div>
                                    )}
                                    {fileUpload.analysis_result.dimensions.depth && (
                                        <div>
                                            <dt className="text-sm font-medium text-gray-500">Depth</dt>
                                            <dd className="text-sm text-gray-900">{fileUpload.analysis_result.dimensions.depth.toFixed(2)} mm</dd>
                                        </div>
                                    )}
                                </>
                            )}

                            {/* Volume and Area */}
                            {fileUpload.analysis_result?.volume && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Volume</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.volume.toFixed(2)} mm³</dd>
                                </div>
                            )}
                            {fileUpload.analysis_result?.area && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Surface Area</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.area.toFixed(2)} mm²</dd>
                                </div>
                            )}

                            {/* Geometry Information */}
                            {fileUpload.analysis_result?.metadata?.vertices && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Vertices</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.metadata.vertices.toLocaleString()}</dd>
                                </div>
                            )}
                            {fileUpload.analysis_result?.metadata?.faces && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Faces</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.metadata.faces.toLocaleString()}</dd>
                                </div>
                            )}
                            {fileUpload.analysis_result?.metadata?.triangles && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Triangles</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.metadata.triangles.toLocaleString()}</dd>
                                </div>
                            )}

                            {/* File Format */}
                            {fileUpload.analysis_result?.metadata?.format && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Format</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.metadata.format}</dd>
                                </div>
                            )}

                            {/* Analysis Time */}
                            {fileUpload.analysis_result?.analysis_time_ms && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Analysis Time</dt>
                                    <dd className="text-sm text-gray-900">{fileUpload.analysis_result.analysis_time_ms} ms</dd>
                                </div>
                            )}

                            {/* File Size */}
                            {fileUpload.analysis_result?.metadata?.file_size_bytes && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">File Size</dt>
                                    <dd className="text-sm text-gray-900">
                                        {(fileUpload.analysis_result.metadata.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                                    </dd>
                                </div>
                            )}
                        </dl>

                        {/* Center of Mass Information */}
                        {fileUpload.analysis_result?.metadata?.center_of_mass && (
                            <div className="mt-6 pt-6 border-t border-gray-200">
                                <h3 className="text-md font-medium text-gray-900 mb-3">Center of Mass</h3>
                                <dl className="grid grid-cols-3 gap-4">
                                    <div>
                                        <dt className="text-sm font-medium text-gray-500">X</dt>
                                        <dd className="text-sm text-gray-900">
                                            {fileUpload.analysis_result.metadata.center_of_mass.x?.toFixed(2)} mm
                                        </dd>
                                    </div>
                                    <div>
                                        <dt className="text-sm font-medium text-gray-500">Y</dt>
                                        <dd className="text-sm text-gray-900">
                                            {fileUpload.analysis_result.metadata.center_of_mass.y?.toFixed(2)} mm
                                        </dd>
                                    </div>
                                    <div>
                                        <dt className="text-sm font-medium text-gray-500">Z</dt>
                                        <dd className="text-sm text-gray-900">
                                            {fileUpload.analysis_result.metadata.center_of_mass.z?.toFixed(2)} mm
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                        )}

                        {/* Bounding Box Information */}
                        {fileUpload.analysis_result?.metadata?.bbox_min && fileUpload.analysis_result?.metadata?.bbox_max && (
                            <div className="mt-6 pt-6 border-t border-gray-200">
                                <h3 className="text-md font-medium text-gray-900 mb-3">Bounding Box</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <h4 className="text-sm font-medium text-gray-700 mb-2">Minimum</h4>
                                        <dl className="grid grid-cols-3 gap-2">
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">X</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_min.x?.toFixed(2)}
                                                </dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">Y</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_min.y?.toFixed(2)}
                                                </dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">Z</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_min.z?.toFixed(2)}
                                                </dd>
                                            </div>
                                        </dl>
                                    </div>
                                    <div>
                                        <h4 className="text-sm font-medium text-gray-700 mb-2">Maximum</h4>
                                        <dl className="grid grid-cols-3 gap-2">
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">X</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_max.x?.toFixed(2)}
                                                </dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">Y</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_max.y?.toFixed(2)}
                                                </dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs font-medium text-gray-500">Z</dt>
                                                <dd className="text-xs text-gray-900">
                                                    {fileUpload.analysis_result.metadata.bbox_max.z?.toFixed(2)}
                                                </dd>
                                            </div>
                                        </dl>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
