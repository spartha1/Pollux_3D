import { Head, useForm } from '@inertiajs/react';
import { useState, useEffect, useCallback, useMemo } from 'react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import Viewer3D, { type ViewType, type Preview, type ViewTypeId } from '@/pages/Viewer3D';
import {
    FileIcon,
    DownloadIcon,
    RefreshCwIcon,
    TrashIcon,
    BoxIcon,
    RulerIcon,
    LayersIcon,
    ActivityIcon,
    AlertCircle,
    ScissorsIcon,
    DrillIcon,
    WrenchIcon,
    SlidersIcon,
    GaugeIcon,
    CogIcon
} from 'lucide-react';

// Define types for the file upload data
interface FileAnalysisResult {
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
    manufacturing?: {
        cutting_perimeters?: number;
        cutting_length_mm?: number;
        bend_orientations?: number;
        holes_detected?: number;
        work_planes?: {
            xy_faces?: number;
            xz_faces?: number;
            yz_faces?: number;
            dominant_plane?: string;
        };
        complexity?: {
            surface_complexity?: string;
            fabrication_difficulty?: string;
        };
        material_efficiency?: number;
        weight_estimates?: {
            [material: string]: {
                name: string;
                type: string;
                weight_grams: number;
                weight_kg: number;
                density: number;
                estimated_cost_usd: number;
                cost_per_kg: number;
            };
        };
    };
    metadata?: {
        faces?: number;
        edges?: number;
        vertices?: number;
        surfaces?: number;
        curves?: number;
        shells?: number;
        solids?: number;
        center_of_mass?: {
            x: number;
            y: number;
            z: number;
        };
        triangles?: number;  // Para STL
        point_count?: number;
        bbox_min?: { x: number; y: number; z: number };
        bbox_max?: { x: number; y: number; z: number };
        file_size_kb?: number;
        total_entities?: number;
        entity_types?: Record<string, number>;
        file_name?: string;
        description?: string;
        schema?: string;
        warning?: string;
        analysis_complete?: boolean;
        format?: string;  // Formato del archivo (BINARY, ASCII, etc.)
        debug_info?: {
            file_size_bytes: number;
            content_length: number;
            has_header: boolean;
            has_data_section: boolean;
            first_100_chars?: string;
        };
        // STEP-specific metadata
        solidworks_info?: {
            sw_version?: string;
            sw_partno?: string;
            sw_rev?: string;
            sw_author?: string;
            sw_created?: string;
            sw_modified?: string;
            sw_material?: string;
        };
        general?: {
            file_description?: string;
            file_name?: string;
            file_schema?: string;
            timestamp?: string;
            units?: string;
        };
        components?: string[];
        materials?: string[];
        assembly?: boolean;
        assembly_components?: number;
    };
    analysis_time_ms?: number;
    // STEP-specific fields
    file_info?: {
        file_size_mb?: number;
        file_type?: string;
        file_extension?: string;
        encoding?: string;
        first_lines?: string[];
        modified_date?: string;
        created_date?: string;
        absolute_path?: string;
        exists?: boolean;
    };
    weldment_info?: {
        weldment_detected?: boolean;
        weld_beads?: number;
        weld_fillets?: number;
        weld_grooves?: number;
        members?: string[];
        gussets?: number;
        end_caps?: number;
        trim_extend?: number;
    };
    structure_info?: {
        is_assembly?: boolean;
        components?: Array<{
            id: string;
            name: string;
        }>;
        weldment_features?: Array<{
            feature: string;
            count: number;
        }>;
        entity_counts?: Record<string, number>;
        materials?: string[];
    };
    coordinate_bounds?: {
        x?: { min: number; max: number };
        y?: { min: number; max: number };
        z?: { min: number; max: number };
        units?: string;
        approximate_dimensions?: {
            width: number;
            height: number;
            depth: number;
        };
        coordinate_points_analyzed?: number;
    };
    solidworks_specific?: {
        export_options?: {
            suggested: string;
            avoid: string;
        };
        weldment_handling?: {
            tip: string;
            common_issues: string[];
        };
    };
    status?: string;
    error?: string;
    suggestions?: string[];
    read_status?: string;
    transfer_roots?: boolean | number;
    analysis_complete?: boolean;
    geometric_analysis?: boolean;
    file_validity?: string;
}

interface FileError {
    error_message: string;
    stack_trace?: string;
}

interface FileUpload {
    id: number;
    filename_original: string;
    filename_stored: string;
    extension: string;
    mime_type: string;
    size: number;
    status: string;
    created_at: string;
    uploadedAt: string | null;
    processedAt: string | null;
    processed_at?: string;
    analysis_result?: FileAnalysisResult;
    errors?: FileError[];
    disk: string;
    storage_path?: string;
    metadata: {
        dimensions?: {
            x?: number;
            y?: number;
            z?: number;
            width?: number;
            height?: number;
            depth?: number;
        };
        vertices?: number;
        faces?: number;
        triangles?: number;
        volume?: number;
        area?: number;
        fileSize?: number;
        uploadDate?: string;
        processDate?: string;
        analysisTime?: number;
    };
}

interface Props {
    fileUpload: FileUpload;
}

export default function Show({ fileUpload }: Props) {
    const [previews, setPreviews] = useState<Partial<Record<string, Preview>>>({});
    const [loadingPreviews, setLoadingPreviews] = useState(false);
    const [generatingPreviews, setGeneratingPreviews] = useState<Set<string>>(new Set());
    const [failedPreviews, setFailedPreviews] = useState<Set<string>>(new Set());
    const [autoGenerationComplete, setAutoGenerationComplete] = useState(false);

    const breadcrumbs: BreadcrumbItem[] = [
        {
            title: 'Dashboard',
            href: '/dashboard',
        },
        {
            title: 'Modelos 3D',
            href: '/3d',
        },
        {
            title: fileUpload.filename_original,
            href: `/3d/${fileUpload.id}`,
        },
    ];

    // Define available view types
    const viewTypes: ViewType[] = useMemo(() => [
        {
            id: '3d',
            name: '3D',
            description: 'Vista 3D interactiva del modelo'
        },
        {
            id: '2d',
            name: '2D Technical',
            description: 'Vista 2D técnica del modelo'
        },
        {
            id: 'wireframe',
            name: 'Wireframe 3D',
            description: 'Vista 3D en modo wireframe'
        },
        {
            id: 'wireframe_2d',
            name: 'Wireframe 2D',
            description: 'Vista 2D en modo wireframe'
        }
    ], []);

    const { delete: destroy, processing } = useForm();
    const { post: analyze, processing: analyzing } = useForm();

    // Fetch previews on component mount
    useEffect(() => {
        const fetchPreviews = async () => {
            setLoadingPreviews(true);
            try {
                const response = await fetch(`/3d/${fileUpload.id}/preview`);
                if (response.ok) {
                    const data = await response.json();
                    const previewsMap: Partial<Record<string, Preview>> = {};
                    data.previews.forEach((preview: {
                        id: number;
                        file_upload_id: number;
                        image_path: string;
                        render_type: ViewTypeId;
                        created_at: string;
                    }) => {
                        previewsMap[preview.render_type] = {
                            id: preview.id,
                            file_upload_id: preview.file_upload_id,
                            image_path: preview.image_path,
                            render_type: preview.render_type,
                            created_at: preview.created_at
                        };
                    });
                    setPreviews(previewsMap);
                }
            } catch (error) {
                console.error('Failed to fetch previews:', error);
            } finally {
                setLoadingPreviews(false);
            }
        };

        fetchPreviews();
    }, [fileUpload.id]);

    const handleDelete = () => {
        if (confirm('¿Estás seguro de que quieres eliminar este archivo?')) {
            destroy(`/3d/${fileUpload.id}`);
        }
    };

    const handleAnalyze = () => {
        const route = (fileUpload.status === 'analyzed' || fileUpload.status === 'processed')
            ? `/3d/${fileUpload.id}/reanalyze`
            : `/3d/${fileUpload.id}/analyze`;

        analyze(route, {
            onSuccess: () => {
                // Recargar la página para mostrar los nuevos datos de análisis
                window.location.reload();
            }
        });
    };

    const result = fileUpload.analysis_result;
    const errors = fileUpload.errors || [];

    // Check if file is a 3D model that can be viewed
    const isViewable3D = ['stl', 'obj', '3mf'].includes(fileUpload.extension.toLowerCase());
    const isSTEPFile = ['step', 'stp'].includes(fileUpload.extension.toLowerCase());

    // Generate preview for a specific render type
    const generatePreview = useCallback(async (renderType: ViewTypeId) => {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            console.log(`Generating ${renderType} preview with CSRF token:`, csrfToken ? 'Present' : 'Missing');

            const response = await fetch(`/3d/${fileUpload.id}/preview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': csrfToken
                },
                body: JSON.stringify({
                    render_type: renderType
                })
            });

            if (response.ok) {
                const data = await response.json();
                const newPreview = data.preview;

                setPreviews(prev => ({
                    ...prev,
                    [renderType]: {
                        id: newPreview.id,
                        file_upload_id: newPreview.file_upload_id,
                        image_path: newPreview.image_path,
                        render_type: newPreview.render_type,
                        created_at: newPreview.created_at
                    }
                }));

                return newPreview;
            } else {
                const errorData = await response.text();
                console.error(`Preview generation failed for ${renderType}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    body: errorData
                });
                throw new Error(`Failed to generate ${renderType} preview: ${response.status} ${response.statusText}`);
            }
        } catch (error) {
            console.error(`Error generating ${renderType} preview:`, error);
            throw error;
        }
    }, [fileUpload.id]);

    // Auto-generate missing previews
    useEffect(() => {
        const autoGeneratePreviews = async () => {
            // Skip if auto-generation is already complete for this file
            if (autoGenerationComplete) {
                return;
            }

            // Skip auto-generation for STEP files as they don't support 3D previews yet
            if (isSTEPFile) {
                setAutoGenerationComplete(true);
                return;
            }

            const viewTypesToGenerate = viewTypes.filter(viewType =>
                !previews[viewType.id] &&
                viewType.id !== '3d' &&
                !generatingPreviews.has(viewType.id) &&
                !failedPreviews.has(viewType.id)
            );

            // Don't run if there's nothing to generate
            if (viewTypesToGenerate.length === 0) {
                setAutoGenerationComplete(true);
                return;
            }

            for (const viewType of viewTypesToGenerate) {
                try {
                    setGeneratingPreviews(prev => new Set(prev).add(viewType.id));
                    console.log(`Auto-generating ${viewType.id} preview...`);
                    await generatePreview(viewType.id);
                    setGeneratingPreviews(prev => {
                        const newSet = new Set(prev);
                        newSet.delete(viewType.id);
                        return newSet;
                    });
                } catch (error) {
                    console.error(`Failed to auto-generate ${viewType.id} preview:`, error);
                    setGeneratingPreviews(prev => {
                        const newSet = new Set(prev);
                        newSet.delete(viewType.id);
                        return newSet;
                    });

                    // Mark as failed to prevent infinite retries
                    setFailedPreviews(prev => new Set(prev).add(viewType.id));

                    // If it's a 404 error, stop trying to generate for this file
                    if (error instanceof Error && (error.message.includes('404') || error.message.includes('File not found'))) {
                        console.warn(`Stopping preview generation for file ${fileUpload.id} due to missing file`);
                        return;
                    }
                }
            }

            // Mark auto-generation as complete after processing all types
            setAutoGenerationComplete(true);
        };

        // Only auto-generate if we have fetched previews and some are missing
        // but not currently generating anything and auto-generation is not complete
        if (!loadingPreviews &&
            !autoGenerationComplete &&
            Object.keys(previews).length < viewTypes.length - 1 &&
            generatingPreviews.size === 0) {
            autoGeneratePreviews();
        }
    }, [previews, loadingPreviews, viewTypes, fileUpload.id, generatingPreviews, failedPreviews, autoGenerationComplete, isSTEPFile, generatePreview]);

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title={fileUpload.filename_original} />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <FileIcon className="h-12 w-12 text-muted-foreground mt-1" />
                        <div>
                            <h1 className="text-2xl font-bold">{fileUpload.filename_original}</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <Badge variant={fileUpload.status === 'processed' ? 'default' : 'secondary'}>
                                    {fileUpload.status}
                                </Badge>
                                <span className="text-sm text-muted-foreground">
                                    {(fileUpload.size / 1024 / 1024).toFixed(2)} MB
                                </span>
                                <span className="text-sm text-muted-foreground">
                                    Subido {new Date(fileUpload.created_at).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" asChild>
                            <a href={`/3d/${fileUpload.id}/download`}>
                                <DownloadIcon className="mr-2 h-4 w-4" />
                                Descargar
                            </a>
                        </Button>
                        {fileUpload.status === 'uploaded' && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleAnalyze}
                                disabled={analyzing}
                            >
                                <ActivityIcon className="mr-2 h-4 w-4" />
                                Analizar
                            </Button>
                        )}
                        {(fileUpload.status === 'processed' || fileUpload.status === 'analyzed' || fileUpload.status === 'error') && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleAnalyze}
                                disabled={analyzing}
                            >
                                <RefreshCwIcon className="mr-2 h-4 w-4" />
                                Re-analizar
                            </Button>
                        )}
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={handleDelete}
                            disabled={processing}
                        >
                            <TrashIcon className="mr-2 h-4 w-4" />
                            Eliminar
                        </Button>
                    </div>
                </div>

                {/* Error Alert */}
                {errors.length > 0 && (
                    <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Error en el procesamiento</AlertTitle>
                        <AlertDescription>
                            {errors[0].error_message}
                        </AlertDescription>
                    </Alert>
                )}

                {/* 3D Viewer - Show for uploaded or processed files */}
                {isViewable3D && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Vista previa 3D</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="relative h-[500px] overflow-hidden rounded-b-lg">
                                <Viewer3D
                                    fileUpload={fileUpload}
                                    viewTypes={viewTypes}
                                    previews={previews}
                                />
                                {loadingPreviews && (
                                    <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded text-xs">
                                        Loading previews...
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Debug information for STEP files */}
                {process.env.NODE_ENV === 'development' && isSTEPFile && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm">Debug Info - STEP File</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-xs space-y-2">
                                <div>isSTEPFile: {isSTEPFile ? 'YES' : 'NO'}</div>
                                <div>result exists: {result ? 'YES' : 'NO'}</div>
                                <div>fileUpload.status: {fileUpload.status}</div>
                                <div>fileUpload.analysis_result exists: {fileUpload.analysis_result ? 'YES' : 'NO'}</div>
                                {result && (
                                    <div>
                                        <div>result keys: {Object.keys(result).join(', ')}</div>
                                        <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">
                                            {JSON.stringify(result, null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* STEP File Information - Show for STEP files */}
                {isSTEPFile && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileIcon className="h-5 w-5" />
                                Información del archivo STEP
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {!result && (
                                <div className="text-center py-8">
                                    <div className="text-muted-foreground mb-4">
                                        <AlertCircle className="h-12 w-12 mx-auto mb-2" />
                                        No hay análisis disponible para este archivo STEP
                                    </div>
                                    <div className="text-sm text-muted-foreground">
                                        El archivo necesita ser analizado para ver información detallada.
                                    </div>
                                    {(fileUpload.status === 'uploaded' || fileUpload.status === 'error') && (
                                        <Button
                                            className="mt-4"
                                            onClick={handleAnalyze}
                                            disabled={analyzing}
                                        >
                                            {analyzing ? 'Analizando...' : fileUpload.status === 'error' ? 'Re-analizar archivo' : 'Analizar archivo'}
                                        </Button>
                                    )}
                                </div>
                            )}

                            {result && (
                                <>
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                {/* File Info */}
                                {result.file_info && (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium text-muted-foreground">Archivo</h4>
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-sm">
                                                <span>Tipo:</span>
                                                <span className="font-mono">{result.file_info.file_type || 'STEP'}</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span>Tamaño:</span>
                                                <span className="font-mono">{result.file_info.file_size_mb} MB</span>
                                            </div>
                                            <div className="flex justify-between text-sm">
                                                <span>Codificación:</span>
                                                <span className="font-mono">{result.file_info.encoding}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* SOLIDWORKS Info */}
                                {result.metadata?.solidworks_info && Object.keys(result.metadata.solidworks_info).length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium text-muted-foreground">SOLIDWORKS</h4>
                                        <div className="space-y-1">
                                            {result.metadata.solidworks_info.sw_version && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Versión:</span>
                                                    <span className="font-mono">{result.metadata.solidworks_info.sw_version}</span>
                                                </div>
                                            )}
                                            {result.metadata.solidworks_info.sw_author && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Autor:</span>
                                                    <span className="font-mono">{result.metadata.solidworks_info.sw_author}</span>
                                                </div>
                                            )}
                                            {result.metadata.solidworks_info.sw_material && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Material:</span>
                                                    <span className="font-mono">{result.metadata.solidworks_info.sw_material}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* General STEP Info */}
                                {result.metadata?.general && (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium text-muted-foreground">STEP</h4>
                                        <div className="space-y-1">
                                            {result.metadata.general.file_schema && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Esquema:</span>
                                                    <span className="font-mono">{result.metadata.general.file_schema}</span>
                                                </div>
                                            )}
                                            {result.metadata.general.file_description && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Descripción:</span>
                                                    <span className="font-mono">{result.metadata.general.file_description}</span>
                                                </div>
                                            )}
                                            {result.metadata.general.timestamp && (
                                                <div className="flex justify-between text-sm">
                                                    <span>Fecha:</span>
                                                    <span className="font-mono">{new Date(result.metadata.general.timestamp).toLocaleDateString()}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Assembly Components */}
                            {result.structure_info?.is_assembly && result.structure_info.components && result.structure_info.components.length > 0 && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3">
                                        Componentes del ensamblaje ({result.structure_info.components.length})
                                    </h4>
                                    <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                                        {result.structure_info.components.slice(0, 12).map((component, index) => (
                                            <div key={index} className="bg-muted/50 rounded p-2">
                                                <div className="text-xs font-mono text-muted-foreground">#{component.id}</div>
                                                <div className="text-sm font-medium truncate">{component.name}</div>
                                            </div>
                                        ))}
                                        {result.structure_info.components.length > 12 && (
                                            <div className="bg-muted/30 rounded p-2 flex items-center justify-center">
                                                <span className="text-sm text-muted-foreground">
                                                    +{result.structure_info.components.length - 12} más
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Entity Counts */}
                            {result.structure_info?.entity_counts && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3">Entidades STEP</h4>
                                    <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4">
                                        {Object.entries(result.structure_info.entity_counts).map(([entity, count]) => (
                                            <div key={entity} className="bg-muted/50 rounded p-2 text-center">
                                                <div className="text-lg font-bold text-blue-600">{count.toLocaleString()}</div>
                                                <div className="text-xs text-muted-foreground">{entity.replace('_', ' ')}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Status and Suggestions */}
                            {(result.status || result.suggestions) && (
                                <div className="mt-6">
                                    <div className="grid gap-4 md:grid-cols-2">
                                        {result.status && (
                                            <div className="space-y-2">
                                                <h4 className="text-sm font-medium text-muted-foreground">Estado del análisis</h4>
                                                <Badge variant={
                                                    result.status === "success" ? "default" :
                                                    result.status.includes("with_analysis") ? "secondary" : "destructive"
                                                }>
                                                    {result.status.replace(/_/g, ' ')}
                                                </Badge>
                                                {result.error && (
                                                    <p className="text-sm text-muted-foreground">{result.error}</p>
                                                )}
                                            </div>
                                        )}

                                        {result.suggestions && result.suggestions.length > 0 && (
                                            <div className="space-y-2">
                                                <h4 className="text-sm font-medium text-muted-foreground">Sugerencias</h4>
                                                <ul className="text-sm text-muted-foreground space-y-1">
                                                    {result.suggestions.slice(0, 3).map((suggestion, index) => (
                                                        <li key={index} className="flex items-start gap-2">
                                                            <span className="text-blue-500 mt-1">•</span>
                                                            <span>{suggestion}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Coordinate Bounds */}
                            {result.coordinate_bounds && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3">Dimensiones y coordenadas</h4>
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                        {result.coordinate_bounds.approximate_dimensions && (
                                            <div className="bg-muted/50 rounded p-3">
                                                <div className="text-xs font-medium text-muted-foreground mb-2">Dimensiones aproximadas</div>
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-sm">
                                                        <span>Ancho:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.approximate_dimensions.width.toFixed(2)} {result.coordinate_bounds.units || 'mm'}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm">
                                                        <span>Alto:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.approximate_dimensions.height.toFixed(2)} {result.coordinate_bounds.units || 'mm'}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm">
                                                        <span>Profundidad:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.approximate_dimensions.depth.toFixed(2)} {result.coordinate_bounds.units || 'mm'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {result.coordinate_bounds.x && (
                                            <div className="bg-muted/50 rounded p-3">
                                                <div className="text-xs font-medium text-muted-foreground mb-2">Límites X</div>
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-sm">
                                                        <span>Mínimo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.x.min.toFixed(3)}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm">
                                                        <span>Máximo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.x.max.toFixed(3)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {result.coordinate_bounds.y && (
                                            <div className="bg-muted/50 rounded p-3">
                                                <div className="text-xs font-medium text-muted-foreground mb-2">Límites Y</div>
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-sm">
                                                        <span>Mínimo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.y.min.toFixed(3)}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm">
                                                        <span>Máximo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.y.max.toFixed(3)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {result.coordinate_bounds.z && (
                                            <div className="bg-muted/50 rounded p-3">
                                                <div className="text-xs font-medium text-muted-foreground mb-2">Límites Z</div>
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-sm">
                                                        <span>Mínimo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.z.min.toFixed(3)}</span>
                                                    </div>
                                                    <div className="flex justify-between text-sm">
                                                        <span>Máximo:</span>
                                                        <span className="font-mono">{result.coordinate_bounds.z.max.toFixed(3)}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {result.coordinate_bounds.coordinate_points_analyzed && (
                                        <div className="mt-3 text-sm text-muted-foreground">
                                            <span className="font-medium">{result.coordinate_bounds.coordinate_points_analyzed.toLocaleString()}</span> puntos de coordenadas analizados
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Weldment Information */}
                            {result.weldment_info && result.weldment_info.weldment_detected && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                        <WrenchIcon className="h-4 w-4" />
                                        Información de soldadura
                                    </h4>
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                        {result.weldment_info.weld_beads !== undefined && (
                                            <div className="bg-blue-50 rounded p-3 text-center">
                                                <div className="text-xl font-bold text-blue-600">{result.weldment_info.weld_beads}</div>
                                                <div className="text-xs text-blue-700">Cordones de soldadura</div>
                                            </div>
                                        )}
                                        {result.weldment_info.weld_fillets !== undefined && (
                                            <div className="bg-green-50 rounded p-3 text-center">
                                                <div className="text-xl font-bold text-green-600">{result.weldment_info.weld_fillets}</div>
                                                <div className="text-xs text-green-700">Filetes de soldadura</div>
                                            </div>
                                        )}
                                        {result.weldment_info.gussets !== undefined && (
                                            <div className="bg-purple-50 rounded p-3 text-center">
                                                <div className="text-xl font-bold text-purple-600">{result.weldment_info.gussets}</div>
                                                <div className="text-xs text-purple-700">Cartelas</div>
                                            </div>
                                        )}
                                        {result.weldment_info.end_caps !== undefined && (
                                            <div className="bg-orange-50 rounded p-3 text-center">
                                                <div className="text-xl font-bold text-orange-600">{result.weldment_info.end_caps}</div>
                                                <div className="text-xs text-orange-700">Tapas finales</div>
                                            </div>
                                        )}
                                    </div>

                                    {result.weldment_info.members && result.weldment_info.members.length > 0 && (
                                        <div className="mt-4">
                                            <div className="text-xs font-medium text-muted-foreground mb-2">
                                                Miembros estructurales ({result.weldment_info.members.length})
                                            </div>
                                            <div className="flex flex-wrap gap-1">
                                                {result.weldment_info.members.slice(0, 10).map((member, index) => (
                                                    <Badge key={index} variant="outline" className="text-xs">
                                                        {member}
                                                    </Badge>
                                                ))}
                                                {result.weldment_info.members.length > 10 && (
                                                    <Badge variant="secondary" className="text-xs">
                                                        +{result.weldment_info.members.length - 10} más
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* SOLIDWORKS-specific suggestions */}
                            {result.solidworks_specific && (
                                <div className="mt-6">
                                    <h4 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                        <CogIcon className="h-4 w-4" />
                                        Recomendaciones específicas para SOLIDWORKS
                                    </h4>
                                    <div className="grid gap-4 md:grid-cols-2">
                                        {result.solidworks_specific.export_options && (
                                            <div className="bg-green-50 rounded p-4">
                                                <div className="text-sm font-medium text-green-800 mb-2">Opciones de exportación</div>
                                                <div className="space-y-2">
                                                    <div>
                                                        <div className="text-xs font-medium text-green-700">Recomendado:</div>
                                                        <div className="text-xs text-green-600">{result.solidworks_specific.export_options.suggested}</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-xs font-medium text-green-700">Evitar:</div>
                                                        <div className="text-xs text-green-600">{result.solidworks_specific.export_options.avoid}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {result.solidworks_specific.weldment_handling && (
                                            <div className="bg-blue-50 rounded p-4">
                                                <div className="text-sm font-medium text-blue-800 mb-2">Manejo de soldaduras</div>
                                                <div className="space-y-2">
                                                    <div>
                                                        <div className="text-xs font-medium text-blue-700">Consejo:</div>
                                                        <div className="text-xs text-blue-600">{result.solidworks_specific.weldment_handling.tip}</div>
                                                    </div>
                                                    {result.solidworks_specific.weldment_handling.common_issues && (
                                                        <div>
                                                            <div className="text-xs font-medium text-blue-700">Problemas comunes:</div>
                                                            <ul className="text-xs text-blue-600 space-y-1">
                                                                {result.solidworks_specific.weldment_handling.common_issues.map((issue, index) => (
                                                                    <li key={index} className="flex items-start gap-1">
                                                                        <span className="text-blue-500 mt-0.5">•</span>
                                                                        <span>{issue}</span>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                                </>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Main Content */}
                <div className="space-y-4">
                    <h2 className="text-lg font-semibold">Análisis del archivo</h2>

                    {result ? (
                        <div className="space-y-6">
                            {/* Estadísticas principales */}
                            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                                            <RulerIcon className="h-4 w-4" />
                                            Dimensiones
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">
                                            {result.coordinate_bounds?.approximate_dimensions ?
                                                `${result.coordinate_bounds.approximate_dimensions.width?.toFixed(1)} × ${result.coordinate_bounds.approximate_dimensions.height?.toFixed(1)} × ${result.coordinate_bounds.approximate_dimensions.depth?.toFixed(1)}`
                                                : result.dimensions ?
                                                (result.dimensions.x !== undefined ?
                                                    `${result.dimensions.x?.toFixed(1)} × ${result.dimensions.y?.toFixed(1)} × ${result.dimensions.z?.toFixed(1)}`
                                                    : `${result.dimensions.width?.toFixed(1)} × ${result.dimensions.height?.toFixed(1)} × ${result.dimensions.depth?.toFixed(1)}`
                                                )
                                                : 'N/A'
                                            }
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            {result.coordinate_bounds?.units || 'mm'}
                                            {result.coordinate_bounds?.coordinate_points_analyzed &&
                                                ` (${result.coordinate_bounds.coordinate_points_analyzed} puntos)`
                                            }
                                        </p>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                                            <BoxIcon className="h-4 w-4" />
                                            Volumen
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">
                                            {result.volume && result.volume > 1e-10 ? result.volume.toFixed(2) : 'N/A'}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            {result.volume && result.volume > 1e-10 ?
                                                'mm³' :
                                                result.volume && result.volume <= 1e-10 ?
                                                    'Modelo requiere reparación' :
                                                    'Requiere PythonOCC'
                                            }
                                        </p>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                                            <LayersIcon className="h-4 w-4" />
                                            Área superficial
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">
                                            {result.area ? result.area.toFixed(2) : 'N/A'}
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            {result.area ? 'mm²' : 'Requiere PythonOCC'}
                                        </p>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                                            <ActivityIcon className="h-4 w-4" />
                                            Tiempo de análisis
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">
                                            {result.analysis_time_ms ?
                                                result.analysis_time_ms + ' ms'
                                                : 'N/A'
                                            }
                                        </div>
                                        <p className="text-xs text-muted-foreground">milisegundos</p>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* STEP Analysis Status - Show for STEP files */}
                            {isSTEPFile && result && (
                                <div>
                                    <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                                        <GaugeIcon className="h-5 w-5" />
                                        Estado del análisis STEP
                                    </h3>
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                        <Card>
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-sm font-medium">Lectura del archivo</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex items-center gap-2">
                                                    {result.read_status === 'success' ? (
                                                        <>
                                                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                                            <span className="text-sm text-green-700">Exitosa</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                                                            <span className="text-sm text-red-700">Error</span>
                                                        </>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>

                                        <Card>
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-sm font-medium">Transferencia de geometría</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex items-center gap-2">
                                                    {result.transfer_roots ? (
                                                        <>
                                                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                                            <span className="text-sm text-green-700">
                                                                {typeof result.transfer_roots === 'number' ? `${result.transfer_roots} raíces` : 'Exitosa'}
                                                            </span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                                                            <span className="text-sm text-orange-700">Limitada</span>
                                                        </>
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {result.transfer_roots ? 'Geometría transferida correctamente' : 'Sin transferencia de geometría'}
                                                </p>
                                            </CardContent>
                                        </Card>

                                        <Card>
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-sm font-medium">Análisis geométrico</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex items-center gap-2">
                                                    {result.geometric_analysis ? (
                                                        <>
                                                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                                            <span className="text-sm text-green-700">Completado</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                                            <span className="text-sm text-yellow-700">Parcial</span>
                                                        </>
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {result.geometric_analysis ? 'Análisis completo realizado' : 'Solo análisis de estructura'}
                                                </p>
                                            </CardContent>
                                        </Card>

                                        <Card>
                                            <CardHeader className="pb-2">
                                                <CardTitle className="text-sm font-medium">Validez del archivo</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex items-center gap-2">
                                                    {result.file_validity === 'valid' ? (
                                                        <>
                                                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                                                            <span className="text-sm text-green-700">Válido</span>
                                                        </>
                                                    ) : result.file_validity === 'corrupted' ? (
                                                        <>
                                                            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                                                            <span className="text-sm text-red-700">Corrupto</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                                                            <span className="text-sm text-gray-700">Desconocido</span>
                                                        </>
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {result.file_validity === 'valid' ? 'Archivo STEP válido' :
                                                     result.file_validity === 'corrupted' ? 'Archivo posiblemente dañado' :
                                                     'Estado no determinado'}
                                                </p>
                                            </CardContent>
                                        </Card>
                                    </div>

                                    {/* Analysis Summary */}
                                    {(result.analysis_complete !== undefined || result.status) && (
                                        <div className="mt-4 bg-muted/30 rounded p-4">
                                            <div className="flex items-start gap-3">
                                                <div className="flex-shrink-0 mt-1">
                                                    {result.analysis_complete ? (
                                                        <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                                                            <div className="w-2 h-2 bg-white rounded-full"></div>
                                                        </div>
                                                    ) : (
                                                        <div className="w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center">
                                                            <div className="w-2 h-2 bg-white rounded-full"></div>
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="text-sm font-medium">
                                                        {result.analysis_complete ? 'Análisis completo' : 'Análisis parcial'}
                                                    </div>
                                                    <div className="text-sm text-muted-foreground mt-1">
                                                        {result.status && result.status.replace(/_/g, ' ')}
                                                        {result.error && ` - ${result.error}`}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Estadísticas de geometría */}
                            {result.metadata && (
                                <div>
                                    <h3 className="text-md font-semibold mb-3">Estadísticas de geometría</h3>
                                    <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
                                        {result.metadata.triangles !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Triángulos</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-blue-600">
                                                        {result.metadata.triangles.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.vertices !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Vértices</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-green-600">
                                                        {result.metadata.vertices.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.faces !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Caras</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-purple-600">
                                                        {result.metadata.faces.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.edges !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Aristas</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-orange-600">
                                                        {result.metadata.edges.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.surfaces !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Superficies</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-teal-600">
                                                        {result.metadata.surfaces.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.solids !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Sólidos</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-xl font-bold text-red-600">
                                                        {result.metadata.solids.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Centro de masa y caja delimitadora */}
                            {result.metadata && (result.metadata.center_of_mass || (result.metadata.bbox_min && result.metadata.bbox_max)) && (
                                <div>
                                    <h3 className="text-md font-semibold mb-3">Información espacial</h3>
                                    <div className="grid gap-4 md:grid-cols-2">
                                        {result.metadata.center_of_mass && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Centro de masa</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-2">
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">X:</span>
                                                            <span className="text-sm font-mono">{result.metadata.center_of_mass.x.toFixed(2)}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">Y:</span>
                                                            <span className="text-sm font-mono">{result.metadata.center_of_mass.y.toFixed(2)}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">Z:</span>
                                                            <span className="text-sm font-mono">{result.metadata.center_of_mass.z.toFixed(2)}</span>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.bbox_min && result.metadata.bbox_max && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Caja delimitadora</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <div className="text-xs font-medium text-muted-foreground mb-1">Mínimo:</div>
                                                            <div className="text-xs font-mono bg-gray-100 p-2 rounded">
                                                                ({result.metadata.bbox_min.x.toFixed(2)}, {result.metadata.bbox_min.y.toFixed(2)}, {result.metadata.bbox_min.z.toFixed(2)})
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <div className="text-xs font-medium text-muted-foreground mb-1">Máximo:</div>
                                                            <div className="text-xs font-mono bg-gray-100 p-2 rounded">
                                                                ({result.metadata.bbox_max.x.toFixed(2)}, {result.metadata.bbox_max.y.toFixed(2)}, {result.metadata.bbox_max.z.toFixed(2)})
                                                            </div>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* DEBUG: Manufacturing Data Check */}
                            {process.env.NODE_ENV === 'development' && (
                                <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
                                    <h4 className="text-sm font-semibold text-yellow-800">DEBUG INFO:</h4>
                                    <p className="text-xs text-yellow-700">
                                        result exists: {result ? 'YES' : 'NO'}
                                    </p>
                                    {result && (
                                        <p className="text-xs text-yellow-700">
                                            result.manufacturing exists: {result.manufacturing ? 'YES' : 'NO'}
                                        </p>
                                    )}
                                    {result?.manufacturing && (
                                        <pre className="text-xs text-yellow-700 mt-2 bg-yellow-100 p-2 rounded">
                                            {JSON.stringify(result.manufacturing, null, 2)}
                                        </pre>
                                    )}
                                </div>
                            )}

                            {/* Métricas de fabricación */}
                            {result.manufacturing && (
                                <div>
                                    <h3 className="text-md font-semibold mb-3">Métricas de fabricación</h3>
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                                        {result.manufacturing.cutting_perimeters !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <ScissorsIcon className="h-4 w-4" />
                                                        Perímetros de corte
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-2xl font-bold text-blue-600">
                                                        {result.manufacturing.cutting_perimeters.toLocaleString()}
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">operaciones</p>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.manufacturing.cutting_length_mm !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <RulerIcon className="h-4 w-4" />
                                                        Longitud de corte
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-2xl font-bold text-green-600">
                                                        {result.manufacturing.cutting_length_mm.toFixed(1)}
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">mm</p>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.manufacturing.holes_detected !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <DrillIcon className="h-4 w-4" />
                                                        Agujeros detectados
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-2xl font-bold text-purple-600">
                                                        {result.manufacturing.holes_detected.toLocaleString()}
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">operaciones</p>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.manufacturing.bend_orientations !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <WrenchIcon className="h-4 w-4" />
                                                        Orientaciones de plegado
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-2xl font-bold text-orange-600">
                                                        {result.manufacturing.bend_orientations.toLocaleString()}
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">orientaciones</p>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>

                                    {/* Información adicional de fabricación */}
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mt-4">
                                        {result.manufacturing.work_planes && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <LayersIcon className="h-4 w-4" />
                                                        Planos de trabajo
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-2">
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">XY:</span>
                                                            <span className="text-sm font-mono">{result.manufacturing.work_planes.xy_faces || 0}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">XZ:</span>
                                                            <span className="text-sm font-mono">{result.manufacturing.work_planes.xz_faces || 0}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">YZ:</span>
                                                            <span className="text-sm font-mono">{result.manufacturing.work_planes.yz_faces || 0}</span>
                                                        </div>
                                                        <div className="flex justify-between font-medium">
                                                            <span className="text-sm text-foreground">Dominante:</span>
                                                            <span className="text-sm font-mono text-blue-600">{result.manufacturing.work_planes.dominant_plane || 'N/A'}</span>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.manufacturing.complexity && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <SlidersIcon className="h-4 w-4" />
                                                        Complejidad
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-2">
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">Superficie:</span>
                                                            <Badge variant={
                                                                result.manufacturing.complexity.surface_complexity === 'High' ? 'destructive' :
                                                                result.manufacturing.complexity.surface_complexity === 'Medium' ? 'secondary' : 'default'
                                                            }>
                                                                {result.manufacturing.complexity.surface_complexity}
                                                            </Badge>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-sm text-muted-foreground">Fabricación:</span>
                                                            <Badge variant={
                                                                result.manufacturing.complexity.fabrication_difficulty === 'Complex' ? 'destructive' :
                                                                result.manufacturing.complexity.fabrication_difficulty === 'Medium' ? 'secondary' : 'default'
                                                            }>
                                                                {result.manufacturing.complexity.fabrication_difficulty}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.manufacturing.material_efficiency !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                                                        <GaugeIcon className="h-4 w-4" />
                                                        Eficiencia del material
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-2xl font-bold text-teal-600">
                                                        {result.manufacturing.material_efficiency.toFixed(1)}%
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">
                                                        {result.manufacturing.material_efficiency > 80 ? 'Excelente' :
                                                         result.manufacturing.material_efficiency > 60 ? 'Buena' :
                                                         result.manufacturing.material_efficiency > 40 ? 'Regular' : 'Baja'
                                                        }
                                                    </p>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>

                                    {/* Estimaciones de peso por material */}
                                    {result.manufacturing.weight_estimates && (
                                        <div className="mt-6">
                                            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                                                <CogIcon className="h-4 w-4" />
                                                Estimaciones de peso y costo por material
                                            </h4>
                                            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                                                {Object.entries(result.manufacturing.weight_estimates).map(([key, material]) => (
                                                    <Card key={key} className="border-l-4 border-l-blue-500">
                                                        <CardHeader className="pb-2">
                                                            <CardTitle className="text-sm font-medium flex items-center justify-between">
                                                                <span>{material.name}</span>
                                                                <Badge variant="outline" className="text-xs">
                                                                    {material.type}
                                                                </Badge>
                                                            </CardTitle>
                                                        </CardHeader>
                                                        <CardContent>
                                                            <div className="space-y-2">
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-xs text-muted-foreground">Peso:</span>
                                                                    <div className="text-right">
                                                                        <div className="text-sm font-bold text-blue-600">
                                                                            {material.weight_grams.toFixed(2)}g
                                                                        </div>
                                                                        <div className="text-xs text-muted-foreground">
                                                                            {material.weight_kg.toFixed(4)}kg
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-xs text-muted-foreground">Costo est.:</span>
                                                                    <div className="text-right">
                                                                        <div className="text-sm font-bold text-green-600">
                                                                            ${material.estimated_cost_usd.toFixed(2)}
                                                                        </div>
                                                                        <div className="text-xs text-muted-foreground">
                                                                            ${material.cost_per_kg}/kg
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex justify-between items-center">
                                                                    <span className="text-xs text-muted-foreground">Densidad:</span>
                                                                    <span className="text-xs font-mono">
                                                                        {material.density}g/cm³
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            </div>
                                            <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                                                <p className="text-xs text-blue-800">
                                                    <strong>Nota:</strong> Las estimaciones se basan en el volumen calculado ({result.volume?.toFixed(2)} mm³)
                                                    y densidades estándar de materiales. Los costos son aproximados y pueden variar según el proveedor.
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Información técnica del archivo */}
                            {result.metadata && (
                                <div>
                                    <h3 className="text-md font-semibold mb-3">Información técnica</h3>
                                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                        {result.metadata.file_size_kb && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Tamaño del archivo</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-lg font-bold text-indigo-600">
                                                        {result.metadata.file_size_kb.toFixed(2)} KB
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.format && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Formato STL</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-lg font-bold text-yellow-600">
                                                        {result.metadata.format}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.total_entities !== undefined && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Total entidades</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-lg font-bold text-pink-600">
                                                        {result.metadata.total_entities.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.point_count !== undefined && result.metadata.point_count > 0 && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Puntos cartesianos</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-lg font-bold text-cyan-600">
                                                        {result.metadata.point_count.toLocaleString()}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.schema && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Schema</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-lg font-bold text-emerald-600">
                                                        {result.metadata.schema}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {result.metadata.file_name && (
                                            <Card>
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-sm font-medium">Nombre interno</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="text-sm font-mono text-gray-600 break-all">
                                                        {result.metadata.file_name}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <Card className="border-dashed">
                            <CardContent className="flex flex-col items-center justify-center py-16">
                                <ActivityIcon className="h-12 w-12 text-muted-foreground mb-4" />
                                <p className="text-muted-foreground text-center">
                                    {fileUpload.status === 'processing'
                                        ? 'El archivo está siendo procesado...'
                                        : 'No hay resultados de análisis disponibles'
                                    }
                                </p>
                            </CardContent>
                        </Card>
                    )}

                    {/* Metadata section */}
                    <div className="mt-8">
                        <h2 className="text-lg font-semibold mb-4">Metadatos del archivo</h2>
                        <div className="grid gap-4 md:grid-cols-2">
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm font-medium">Información del archivo</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <dl className="space-y-2">
                                        <div>
                                            <dt className="text-sm font-medium">Tipo MIME</dt>
                                            <dd className="text-sm text-muted-foreground">{fileUpload.mime_type}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium">Extensión</dt>
                                            <dd className="text-sm text-muted-foreground">.{fileUpload.extension}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium">Tamaño</dt>
                                            <dd className="text-sm text-muted-foreground">{(fileUpload.size / 1024 / 1024).toFixed(2)} MB</dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium">Fecha de subida</dt>
                                            <dd className="text-sm text-muted-foreground">
                                                {new Date(fileUpload.created_at).toLocaleString()}
                                            </dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium">Fecha de procesamiento</dt>
                                            <dd className="text-sm text-muted-foreground">
                                                {fileUpload.processed_at
                                                    ? new Date(fileUpload.processed_at).toLocaleString()
                                                    : 'No procesado'
                                                }
                                            </dd>
                                        </div>
                                    </dl>
                                </CardContent>
                            </Card>

                            {result?.metadata && (
                                <Card>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-sm font-medium">Información adicional</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {result.metadata.warning && (
                                            <Alert className="mb-4">
                                                <AlertCircle className="h-4 w-4" />
                                                <AlertDescription className="text-xs">
                                                    {result.metadata.warning}
                                                </AlertDescription>
                                            </Alert>
                                        )}

                                        {/* Mostrar información específica del formato */}
                                        {result.metadata.description && (
                                            <div className="mb-4">
                                                <dt className="text-sm font-medium">Descripción</dt>
                                                <dd className="text-sm text-muted-foreground">{result.metadata.description}</dd>
                                            </div>
                                        )}

                                        {/* Mostrar tipos de entidades si están disponibles */}
                                        {result.metadata.entity_types && Object.keys(result.metadata.entity_types).length > 0 && (
                                            <div className="mt-4">
                                                <h4 className="text-sm font-medium mb-2">Tipos de entidades</h4>
                                                <div className="space-y-1">
                                                    {Object.entries(result.metadata.entity_types).map(([type, count]) => (
                                                        <div key={type} className="flex justify-between text-xs">
                                                            <span className="text-muted-foreground">{type}:</span>
                                                            <span className="font-mono font-medium">{count}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Información de depuración si está disponible */}
                                        {result.metadata.debug_info && (
                                            <div className="mt-4 p-3 bg-muted/30 rounded-md">
                                                <h4 className="text-sm font-medium mb-2">Información de depuración</h4>
                                                <dl className="space-y-1 text-xs">
                                                    <div>
                                                        <dt className="inline font-medium">Tamaño del archivo:</dt>
                                                        <dd className="inline ml-1">{result.metadata.debug_info.file_size_bytes} bytes</dd>
                                                    </div>
                                                    <div>
                                                        <dt className="inline font-medium">Longitud del contenido:</dt>
                                                        <dd className="inline ml-1">{result.metadata.debug_info.content_length}</dd>
                                                    </div>
                                                    <div>
                                                        <dt className="inline font-medium">Tiene header:</dt>
                                                        <dd className="inline ml-1">{result.metadata.debug_info.has_header ? 'Sí' : 'No'}</dd>
                                                    </div>
                                                    <div>
                                                        <dt className="inline font-medium">Tiene sección DATA:</dt>
                                                        <dd className="inline ml-1">{result.metadata.debug_info.has_data_section ? 'Sí' : 'No'}</dd>
                                                    </div>
                                                    {result.metadata.debug_info.first_100_chars && (
                                                        <div>
                                                            <dt className="font-medium">Primeros caracteres:</dt>
                                                            <dd className="mt-1 font-mono text-xs bg-background p-2 rounded overflow-x-auto">
                                                                {result.metadata.debug_info.first_100_chars}
                                                            </dd>
                                                        </div>
                                                    )}
                                                </dl>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
