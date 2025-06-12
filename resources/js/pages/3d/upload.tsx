import { useForm } from "@inertiajs/react";
import { Head } from '@inertiajs/react';
import AppLayout from '@/layouts/app-layout';
import { type BreadcrumbItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
// Make sure that '@/components/ui/progress' exists and exports 'Progress'.
// If you get a "module not found" or "Progress is not exported" error, check the file path and export.
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FileIcon, UploadIcon, AlertCircle } from 'lucide-react';
import { FormEvent, useState } from "react";

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
        title: 'Subir archivo',
        href: '/3d/upload',
    },
];

export default function Upload() {
    const { data, setData, post, progress, processing, errors } = useForm<{
        file: File | null;
    }>({
        file: null,
    });

    const [dragActive, setDragActive] = useState(false);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setData("file", e.dataTransfer.files[0]);
        }
    };

    const submit = (e: FormEvent) => {
        e.preventDefault();
        post("/3d");
    };

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Subir archivo 3D" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                <div className="max-w-2xl mx-auto w-full">
                    <Card>
                        <CardHeader>
                            <CardTitle>Subir archivo 3D o 2D</CardTitle>
                            <CardDescription>
                                Sube archivos CAD, STL, OBJ y otros formatos para análisis
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={submit} className="space-y-4">
                                <div
                                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                                        dragActive ? 'border-primary bg-primary/5' : 'border-border'
                                    }`}
                                    onDragEnter={handleDrag}
                                    onDragLeave={handleDrag}
                                    onDragOver={handleDrag}
                                    onDrop={handleDrop}
                                >
                                    <FileIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />

                                    <Label htmlFor="file-upload" className="cursor-pointer">
                                        <span className="text-primary hover:underline">
                                            Haz clic para seleccionar
                                        </span>
                                        <span className="text-muted-foreground"> o arrastra un archivo aquí</span>
                                    </Label>

                                    <Input
                                        id="file-upload"
                                        type="file"
                                        className="hidden"
                                        onChange={e => setData("file", e.target.files?.[0] || null)}
                                        accept=".stl,.obj,.iges,.step,.stp,.brep,.fcstd"
                                    />

                                    <p className="text-xs text-muted-foreground mt-2">
                                        STL, OBJ, IGES, STEP, BREP hasta 100MB
                                    </p>
                                </div>

                                {data.file && (
                                    <div className="bg-secondary/20 rounded-lg p-4">
                                        <div className="flex items-center gap-3">
                                            <FileIcon className="h-8 w-8 text-muted-foreground" />
                                            <div className="flex-1">
                                                <p className="font-medium">{data.file.name}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {(data.file.size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {errors.file && (
                                    <Alert variant="destructive">
                                        <AlertCircle className="h-4 w-4" />
                                        <AlertDescription>{errors.file}</AlertDescription>
                                    </Alert>
                                )}

                                {progress && (
                                    <div className="space-y-2">
                                        <Progress value={progress.percentage} />
                                        <p className="text-sm text-muted-foreground text-center">
                                            Subiendo: {progress.percentage}%
                                        </p>
                                    </div>
                                )}

                                <Button
                                    type="submit"
                                    disabled={processing || !data.file}
                                    className="w-full"
                                >
                                    <UploadIcon className="mr-2 h-4 w-4" />
                                    {processing ? 'Subiendo...' : 'Subir archivo'}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </AppLayout>
    );
}
