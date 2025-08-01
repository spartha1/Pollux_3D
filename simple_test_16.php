<?php

// Simple test to trigger re-analysis via Laravel command
$fileId = 16;

echo "Testing manufacturing analysis for file ID $fileId\n";

// Use Laravel's HTTP test functionality
$response = file_get_contents("http://localhost/laravel/Pollux_3D/public/files/$fileId/analyze");

if ($response) {
    echo "Response received:\n";
    echo $response . "\n";
} else {
    echo "No response received\n";
}
