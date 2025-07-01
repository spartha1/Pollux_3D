<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;
use Illuminate\Database\Eloquent\Relations\HasMany;

class FileUpload extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'filename_original',
        'filename_stored',
        'extension',
        'mime_type',
        'size',
        'status',
        'storage_path',
        'disk',
        'uploaded_at',
        'processed_at',
    ];

    protected $casts = [
        'uploaded_at' => 'datetime',
        'processed_at' => 'datetime',
        'size' => 'integer',
    ];

    // Status constants
    const STATUS_UPLOADED = 'uploaded';
    const STATUS_PROCESSING = 'processing';
    const STATUS_ANALYZED = 'analyzed';
    const STATUS_ERROR = 'error';

    protected $hidden = [
        'created_at',
        'updated_at'
    ];

    protected $appends = [
        // 'storage_path' // Only append when needed
    ];

    /**
     * Get the user that owns the file upload.
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the analysis result for the file upload.
     */
    public function analysisResult(): HasOne
    {
        return $this->hasOne(FileAnalysisResult::class);
    }

    /**
     * Get the errors for the file upload.
     */
    public function errors(): HasMany
    {
        return $this->hasMany(FileError::class);
    }

    /**
     * Get the previews for the file upload.
     */
    public function previews(): HasMany
    {
        return $this->hasMany(FilePreview::class);
    }

    public function getStoragePathAttribute()
    {
        // Return the stored path directly as it already contains the full relative path
        return $this->attributes['storage_path'] ?? null;
    }

    /**
     * Get formatted analysis result data
     */
    public function getFormattedAnalysisAttribute()
    {
        $analysisResult = $this->analysisResult;
        if (!$analysisResult || !$analysisResult->analysis_data) {
            return null;
        }

        $data = $analysisResult->analysis_data;

        return [
            'dimensions' => $data['dimensions'] ?? null,
            'volume' => $data['volume'] ?? null,
            'area' => $data['area'] ?? $data['surface_area'] ?? null,
            'layers' => $data['layers'] ?? null,
            'metadata' => $data['metadata'] ?? [],
            'analysis_time_ms' => $data['analysis_time_ms'] ?? $data['processing_time'] ?? null,
        ];
    }
}
