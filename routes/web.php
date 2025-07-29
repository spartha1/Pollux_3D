<?php

use Illuminate\Support\Facades\Route;
use Inertia\Inertia;
use App\Http\Controllers\FileUploadController;
use App\Http\Controllers\FileAnalysisController;
use App\Http\Controllers\FilePreviewController;
use App\Http\Controllers\Viewer3DController;

Route::get('/', function () {
    return Inertia::render('welcome');
})->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('dashboard', function () {
        return Inertia::render('dashboard');
    })->name('dashboard');

    // 3D File Management Routes
    Route::prefix('3d')->group(function () {
        Route::get('/', [FileUploadController::class, 'index'])->name('3d.index');
        Route::get('/upload', function () {
            return Inertia::render('3d/upload');
        })->name('3d.upload');
        Route::post('/', [FileUploadController::class, 'store'])->name('3d.store');
        Route::get('/{fileUpload}', [FileUploadController::class, 'show'])->name('3d.show');
        Route::post('/{fileUpload}/analyze', [FileAnalysisController::class, 'analyze'])->name('3d.analyze');
        Route::get('/{fileUpload}/download', [FileUploadController::class, 'download'])->name('3d.download');
        Route::delete('/{fileUpload}', [FileUploadController::class, 'destroy'])->name('3d.destroy');

        // Preview routes
        Route::post('/{fileUpload}/preview', [FilePreviewController::class, 'generate'])->name('3d.preview.generate');
        Route::get('/{fileUpload}/preview', [FilePreviewController::class, 'index'])->name('3d.preview.index');
        Route::get('/{fileUpload}/preview/{preview}', [FilePreviewController::class, 'show'])->name('3d.preview.show');
        Route::get('/{fileUpload}/file', [FileUploadController::class, 'serveFile'])->name('3d.file');
    });
    // File Analysis
    Route::get('/viewer/{fileUpload}', [Viewer3DController::class, 'show'])->name('viewer.show');

});

// API routes for file serving
Route::prefix('api')->middleware(['auth'])->group(function () {
    Route::get('/file/{fileUpload}/download', [FileUploadController::class, 'download'])
        ->name('api.file.download');
});

// Test CSRF route
Route::post('/test-csrf', function () {
    return response()->json([
        'message' => 'CSRF test successful',
        'token' => csrf_token()
    ]);
})->middleware('auth');

// Test route - no CSRF protection
Route::post('/test-preview/{fileUpload}', [FilePreviewController::class, 'generate'])->name('test.preview');

// Simple debug test route
Route::get('/debug-test', function() {
    return response()->json([
        'status' => 'OK',
        'timestamp' => now(),
        'message' => 'Debug endpoint working'
    ]);
});

// Debug file view without auth
Route::get('/debug-file/{fileUpload}', [FileUploadController::class, 'show'])
    ->name('debug.file.show')
    ->withoutMiddleware(['auth', 'verified']);

require __DIR__.'/settings.php';
require __DIR__.'/auth.php';

// Debug preview route completely outside middleware groups
Route::post('/debug-preview/{fileUpload}', [FilePreviewController::class, 'generate'])
    ->name('debug.preview');
