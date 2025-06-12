<?php

namespace App\Http\Controllers;

use App\Models\FileUpload;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Inertia\Inertia;

class FileUploadController extends Controller
{
    use AuthorizesRequests;
    /**
     * Display a listing of the user's file uploads.
     */
    public function index(Request $request)
    {
        $files = $request->user()->fileUploads()
            ->with(['analysisResult', 'previews'])
            ->latest()
            ->paginate(20);

        return Inertia::render('3d/index', [
            'files' => $files->items()
        ]);
    }

    /**
     * Show the form for uploading a new file.
     */
    public function create()
    {
        return view('files.create');
    }

    /**
     * Store a newly uploaded file.
     */
    public function store(Request $request)
    {
        $request->validate([
            'file' => 'required|file|max:102400', // 100MB max
        ]);

        $file = $request->file('file');
        $extension = $file->getClientOriginalExtension();
        $originalName = $file->getClientOriginalName();
        $storedName = Str::uuid() . '.' . $extension;

        // Store file in private directory
        $path = $file->storeAs(
            'models/' . $request->user()->id,
            $storedName,
            'local'
        );

        $fileUpload = $request->user()->fileUploads()->create([
            'filename_original' => $originalName,
            'filename_stored' => $storedName,
            'extension' => $extension,
            'mime_type' => $file->getMimeType(),
            'size' => $file->getSize(),
            'storage_path' => $path,
            'disk' => 'local',
            'status' => 'uploaded',
            'uploaded_at' => now(),
        ]);

        // Dispatch job for processing
        // ProcessFileUpload::dispatch($fileUpload);

        return redirect()->route('3d.show', ['fileUpload' => $fileUpload->id])
            ->with('success', 'File uploaded successfully. Processing will begin shortly.');
    }

    /**
     * Display the specified file upload.
     */
    public function show(FileUpload $fileUpload)
    {
        $this->authorize('view', $fileUpload);

        $fileUpload->load(['analysisResult', 'previews', 'errors']);

        return Inertia::render('3d/show', [
            'fileUpload' => $fileUpload
        ]);
    }

    /**
     * Download the original file.
     */
    public function download(FileUpload $fileUpload)
    {
        $this->authorize('download', $fileUpload);

        $filePath = Storage::disk($fileUpload->disk)->path($fileUpload->storage_path);

        return response()->download(
            $filePath,
            $fileUpload->filename_original
        );
    }

    /**
     * Remove the specified file upload.
     */
    public function destroy(FileUpload $fileUpload)
    {
        $this->authorize('delete', $fileUpload);

        // Delete physical file
        Storage::disk($fileUpload->disk)->delete($fileUpload->storage_path);

        // Delete previews
        foreach ($fileUpload->previews as $preview) {
            Storage::disk('public')->delete($preview->image_path);
        }

        // Delete record (cascades to related tables)
        $fileUpload->delete();

        return redirect()->route('3d.index')
            ->with('success', 'File deleted successfully.');
    }
}
