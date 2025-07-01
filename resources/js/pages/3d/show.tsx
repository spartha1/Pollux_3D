import { Head, useForm } from '@inertiajs/react';
import { useState, useEffect } from 'react';
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
    AlertCircle
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
        debug_info?: {
            file_size_bytes: number;
            content_length: number;
            has_header: boolean;
            has_data_section: boolean;
            first_100_chars?: string;
        };
    };
    analysis_time_ms?: number;
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
    processed_at?: string;
    analysis_result?: FileAnalysisResult;
    errors?: FileError[];
    disk: string;
    storage_path?: string;  // Add this if needed
}

interface Props {
    fileUpload: FileUpload;
}

export default function Show({ fileUpload }: Props) {
    const [previews, setPreviews] = useState<Partial<Record<string, Preview>>>({});
    const [loadingPreviews, setLoadingPreviews] = useState(false);

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
    const viewTypes: ViewType[] = [
        {
            id: '3d',
            name: '3D',
            description: 'Vista 3D interactiva del modelo'
        },
        {
            id: '2d',
            name: '2D',
            description: 'Vista 2D del modelo'
        },
        {
            id: 'wireframe',
            name: 'Wireframe',
            description: 'Vista del modelo en modo wireframe'
        }
    ];

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
        analyze(`/3d/${fileUpload.id}/analyze`);
    };

    const result = fileUpload.analysis_result;
    const errors = fileUpload.errors || [];

    // Check if file is a 3D model that can be viewed
    const isViewable3D = ['stl', 'obj', '3mf'].includes(fileUpload.extension.toLowerCase());

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
                        {fileUpload.status === 'processed' && (
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
                {isViewable3D && (fileUpload.status === 'processed' || fileUpload.status === 'uploaded') && (
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

                {/* Main Content */}
                <div className="space-y-4">
                    <h2 className="text-lg font-semibold">Análisis del archivo</h2>

                    {result ? (
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
                                        {result.dimensions ?
                                            (result.dimensions.x !== undefined ?
                                                `${result.dimensions.x?.toFixed(1)} × ${result.dimensions.y?.toFixed(1)} × ${result.dimensions.z?.toFixed(1)}`
                                                : `${result.dimensions.width?.toFixed(1)} × ${result.dimensions.height?.toFixed(1)} × ${result.dimensions.depth?.toFixed(1)}`
                                            )
                                            : 'N/A'
                                        }
                                    </div>
                                    <p className="text-xs text-muted-foreground">mm</p>
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
                                        {result.volume ? result.volume.toFixed(2) : 'N/A'}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {result.volume ? 'mm³' : 'Requiere PythonOCC'}
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
                                            (result.analysis_time_ms / 1000).toFixed(2)
                                            : 'N/A'
                                        }
                                    </div>
                                    <p className="text-xs text-muted-foreground">segundos</p>
                                </CardContent>
                            </Card>
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
                        <h2 className="text-lg font-semibold mb-4">Metadatos</h2>
                        <div className="grid gap-4 md:grid-cols-2">
                            <Card>
                                <CardContent className="pt-6">
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
                                        <dl className="space-y-2">
                                            {result.metadata.faces !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Caras</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.faces}</dd>
                                                </div>
                                            )}
                                            {result.metadata.edges !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Aristas</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.edges}</dd>
                                                </div>
                                            )}
                                            {result.metadata.vertices !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Vértices/Puntos</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.vertices}</dd>
                                                </div>
                                            )}
                                            {result.metadata.surfaces !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Superficies</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.surfaces}</dd>
                                                </div>
                                            )}
                                            {result.metadata.solids !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Sólidos</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.solids}</dd>
                                                </div>
                                            )}
                                            {result.metadata.total_entities !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Total de entidades</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.total_entities}</dd>
                                                </div>
                                            )}
                                            {result.metadata.triangles !== undefined && (
                                                <div>
                                                    <dt className="text-sm font-medium">Triángulos</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.triangles}</dd>
                                                </div>
                                            )}
                                            {result.metadata.center_of_mass && (
                                                <div>
                                                    <dt className="text-sm font-medium">Centro de masa</dt>
                                                    <dd className="text-sm text-muted-foreground">
                                                        X: {result.metadata.center_of_mass.x.toFixed(2)},
                                                        Y: {result.metadata.center_of_mass.y.toFixed(2)},
                                                        Z: {result.metadata.center_of_mass.z.toFixed(2)}
                                                    </dd>
                                                </div>
                                            )}
                                            {result.metadata.file_name && (
                                                <div>
                                                    <dt className="text-sm font-medium">Nombre en STEP</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.file_name}</dd>
                                                </div>
                                            )}
                                            {result.metadata.schema && (
                                                <div>
                                                    <dt className="text-sm font-medium">Schema</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.schema}</dd>
                                                </div>
                                            )}
                                            {result.metadata.point_count !== undefined && result.metadata.point_count > 0 && (
                                                <div>
                                                    <dt className="text-sm font-medium">Puntos cartesianos</dt>
                                                    <dd className="text-sm text-muted-foreground">{result.metadata.point_count}</dd>
                                                </div>
                                            )}
                                            {result.metadata.bbox_min && result.metadata.bbox_max && (
                                                <div>
                                                    <dt className="text-sm font-medium">Caja delimitadora</dt>
                                                    <dd className="text-sm text-muted-foreground">
                                                        Min: ({result.metadata.bbox_min.x}, {result.metadata.bbox_min.y}, {result.metadata.bbox_min.z})<br/>
                                                        Max: ({result.metadata.bbox_max.x}, {result.metadata.bbox_max.y}, {result.metadata.bbox_max.z})
                                                    </dd>
                                                </div>
                                            )}
                                            {result.metadata.debug_info && (
                                                <div className="mt-4 p-3 bg-muted/50 rounded-md">
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
                                        </dl>

                                        {result.metadata.entity_types && Object.keys(result.metadata.entity_types).length > 0 && (
                                            <div className="mt-4">
                                                <h4 className="text-sm font-medium mb-2">Tipos de entidades</h4>
                                                <div className="text-xs space-y-1">
                                                    {Object.entries(result.metadata.entity_types).map(([type, count]) => (
                                                        <div key={type} className="flex justify-between">
                                                            <span className="text-muted-foreground">{type}:</span>
                                                            <span className="font-mono">{count}</span>
                                                        </div>
                                                    ))}
                                                </div>
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
