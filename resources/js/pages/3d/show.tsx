import { Head, useForm } from '@inertiajs/react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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
    };
    volume?: number;
    area?: number;
    layers?: number;
    metadata?: Record<string, unknown>;
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
}

interface Props {
    fileUpload: FileUpload;
}

export default function Show({ fileUpload }: Props) {
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

    const { delete: destroy, processing } = useForm();
    const { post: analyze, processing: analyzing } = useForm();

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
                                            `${result.dimensions.x?.toFixed(1)} × ${result.dimensions.y?.toFixed(1)} × ${result.dimensions.z?.toFixed(1)}`
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
                                        {result.volume?.toFixed(2) ?? 'N/A'}
                                    </div>
                                    <p className="text-xs text-muted-foreground">mm³</p>
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
                                        {result.area?.toFixed(2) ?? 'N/A'}
                                    </div>
                                    <p className="text-xs text-muted-foreground">mm²</p>
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
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
