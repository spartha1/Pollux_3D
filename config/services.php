<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'token' => env('POSTMARK_TOKEN'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'resend' => [
        'key' => env('RESEND_KEY'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'python' => [
        'conda_root' => env('CONDA_ROOT'),
        'conda_env' => env('CONDA_ENV', 'pollux-preview-env'),
        'conda_path' => env('CONDA_ROOT') ? (PHP_OS_FAMILY === 'Windows' ? env('CONDA_ROOT') . '\\Scripts\\conda.exe' : env('CONDA_ROOT') . '/bin/conda') : null,
        'executable' => env('PYTHON_EXECUTABLE'), // Auto-detection handled in controller
    ],

    'preview' => [
        'url' => env('PREVIEW_SERVICE_URL', 'http://localhost:8052'),
        'api_key' => env('PREVIEW_SERVICE_API_KEY'),
        'server_port' => env('PREVIEW_SERVER_PORT', 8052),
        'server_host' => env('PREVIEW_SERVER_HOST', 'localhost'),
    ],

    'project' => [
        'root' => env('PROJECT_ROOT', base_path()),
        'storage_path' => env('STORAGE_PATH', storage_path()),
        'analyzer_path' => env('ANALYZER_PATH', app_path('Services/FileAnalyzers')),
    ],
];
