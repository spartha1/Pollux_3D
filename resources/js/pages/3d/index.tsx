import { Link } from "@inertiajs/react";
import { Head } from '@inertiajs/react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileIcon, UploadIcon, EyeIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';

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
    disk: string;
}

// Define pagination data structure
interface PaginatedFiles {
    data: FileUpload[];
    current_page: number;
    last_page: number;
    per_page: number;
    total: number;
    from: number;
    to: number;
    links: Array<{
        url: string | null;
        label: string;
        active: boolean;
    }>;
}

interface Props {
    files: PaginatedFiles;
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
                        <p className="text-muted-foreground">
                            Gestiona tus archivos 3D y 2D
                            {files.total > 0 && (
                                <span className="ml-2">
                                    ({files.from}-{files.to} de {files.total} archivos)
                                </span>
                            )}
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        {files.total > 20 && (
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">Mostrar:</span>
                                <Select
                                    value={files.per_page.toString()}
                                    onValueChange={(value) => {
                                        window.location.href = `/3d?per_page=${value}`;
                                    }}
                                >
                                    <SelectTrigger className="w-20">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="20">20</SelectItem>
                                        <SelectItem value="30">30</SelectItem>
                                        <SelectItem value="50">50</SelectItem>
                                        <SelectItem value="100">100</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}
                        <Button asChild>
                            <Link href="/3d/upload">
                                <UploadIcon className="mr-2 h-4 w-4" />
                                Subir archivo
                            </Link>
                        </Button>
                    </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {files.data.map((file: FileUpload) => (
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

                {/* Pagination Controls */}
                {files.last_page > 1 && (
                    <div className="flex items-center justify-between mt-6">
                        <div className="text-sm text-muted-foreground">
                            Mostrando {files.from} a {files.to} de {files.total} resultados
                        </div>
                        <div className="flex items-center space-x-2">
                            {/* Previous Page Button */}
                            {files.current_page > 1 ? (
                                <Button variant="outline" size="sm" asChild>
                                    <Link href={`/3d?page=${files.current_page - 1}`}>
                                        <ChevronLeftIcon className="h-4 w-4" />
                                        Anterior
                                    </Link>
                                </Button>
                            ) : (
                                <Button variant="outline" size="sm" disabled>
                                    <ChevronLeftIcon className="h-4 w-4" />
                                    Anterior
                                </Button>
                            )}

                            {/* Page Numbers */}
                            <div className="flex items-center space-x-1">
                                {files.links.map((link, index) => {
                                    // Skip the "Anterior" and "Siguiente" links
                                    if (link.label === '&laquo; Previous' || link.label === 'Next &raquo;') {
                                        return null;
                                    }

                                    // Handle "..." ellipsis
                                    if (link.label === '...') {
                                        return (
                                            <span key={index} className="px-3 py-2 text-sm text-muted-foreground">
                                                ...
                                            </span>
                                        );
                                    }

                                    return (
                                        <Button
                                            key={index}
                                            variant={link.active ? "default" : "outline"}
                                            size="sm"
                                            asChild={!!link.url}
                                            disabled={!link.url}
                                        >
                                            {link.url ? (
                                                <Link href={link.url}>
                                                    {link.label}
                                                </Link>
                                            ) : (
                                                <span>{link.label}</span>
                                            )}
                                        </Button>
                                    );
                                })}
                            </div>

                            {/* Next Page Button */}
                            {files.current_page < files.last_page ? (
                                <Button variant="outline" size="sm" asChild>
                                    <Link href={`/3d?page=${files.current_page + 1}`}>
                                        Siguiente
                                        <ChevronRightIcon className="h-4 w-4" />
                                    </Link>
                                </Button>
                            ) : (
                                <Button variant="outline" size="sm" disabled>
                                    Siguiente
                                    <ChevronRightIcon className="h-4 w-4" />
                                </Button>
                            )}
                        </div>
                    </div>
                )}

                {files.data.length === 0 && (
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
