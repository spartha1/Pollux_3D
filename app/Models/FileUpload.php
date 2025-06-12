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
}
