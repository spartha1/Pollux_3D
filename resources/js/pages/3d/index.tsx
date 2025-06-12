import { Link } from "@inertiajs/react";
import { Head } from '@inertiajs/react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileIcon, UploadIcon, EyeIcon } from 'lucide-react';

// Define the file type
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
    analysis_result?: Record<string, unknown>;
    previews?: unknown[];
}

interface Props {
    files: FileUpload[];
}

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Dashboard',
        href: '/dashboard',
    },
    {
        title: 'Modelos 3D',
        href: '/3d',
    },
];

export default function Index({ files }: Props) {
    const getStatusBadge = (status: string) => {
        const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
            'uploaded': 'secondary',
            'processing': 'default',
            'processed': 'outline',
            'failed': 'destructive'
        };

        const labels: Record<string, string> = {
            'uploaded': 'Subido',
            'processing': 'Procesando',
            'processed': 'Procesado',
            'failed': 'Error'
        };

        return (
            <Badge variant={variants[status] || 'default'}>
                {labels[status] || status}
            </Badge>
        );
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Modelos 3D" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">Modelos 3D</h1>
                        <p className="text-muted-foreground">Gestiona tus archivos 3D y 2D</p>
                    </div>
                    <Button asChild>
                        <Link href="/3d/upload">
                            <UploadIcon className="mr-2 h-4 w-4" />
                            Subir archivo
                        </Link>
                    </Button>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {files.map((file: FileUpload) => (
                        <Card key={file.id} className="hover:shadow-lg transition-shadow">
                            <CardHeader className="pb-3">
                                <div className="flex items-start justify-between">
                                    <FileIcon className="h-8 w-8 text-muted-foreground" />
                                    {getStatusBadge(file.status)}
                                </div>
                                <CardTitle className="text-base line-clamp-1">
                                    {file.filename_original}
                                </CardTitle>
                                <CardDescription>
                                    {new Date(file.created_at).toLocaleDateString()}
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
                                    <span>Tamaño: {(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                    <span>.{file.extension}</span>
                                </div>
                                <Button variant="secondary" size="sm" className="w-full" asChild>
                                    <Link href={`/3d/${file.id}`}>
                                        <EyeIcon className="mr-2 h-4 w-4" />
                                        Ver análisis
                                    </Link>
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {files.length === 0 && (
                    <Card className="border-dashed">
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <FileIcon className="h-12 w-12 text-muted-foreground mb-4" />
                            <p className="text-muted-foreground text-center mb-4">
                                No hay archivos subidos aún
                            </p>
                            <Button asChild>
                                <Link href="/3d/upload">
                                    <UploadIcon className="mr-2 h-4 w-4" />
                                    Subir tu primer archivo
                                </Link>
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </div>
        </AppLayout>
    );
}
