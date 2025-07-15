<?php
require_once 'vendor/autoload.php';

use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

// Bootstrap the application
$app = Application::configure(basePath: getcwd())
    ->withRouting(
        web: __DIR__.'/routes/web.php',
        commands: __DIR__.'/routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware) {
        //
    })
    ->withExceptions(function (Exceptions $exceptions) {
        //
    })
    ->create();

// Set up the request context
$app->instance('request', new \Illuminate\Http\Request());

// Find a file to test
$files = FileUpload::all();

if ($files->isEmpty()) {
    echo "No files found in database\n";
    exit;
}

echo "Available files:\n";
foreach ($files as $file) {
    echo "- ID: {$file->id}, Name: {$file->original_name}, Status: {$file->status}\n";
}

// Test with the first file
$file = $files->first();
echo "\nTesting analysis with file: {$file->original_name} (ID: {$file->id})\n";

try {
    $controller = new FileAnalysisController();
    $result = $controller->analyze($file);
    echo "Analysis completed successfully!\n";
    print_r($result);
} catch (Exception $e) {
    echo "Error during analysis: " . $e->getMessage() . "\n";
    echo "Stack trace: " . $e->getTraceAsString() . "\n";
}
