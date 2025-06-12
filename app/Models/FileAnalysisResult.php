<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FileAnalysisResult extends Model
{
    use HasFactory;

    protected $fillable = [
        'file_upload_id',
        'dimensions',
        'volume',
        'area',
        'layers',
        'metadata',
        'analysis_time_ms',
    ];

    protected $casts = [
        'dimensions' => 'array',
        'metadata' => 'array',
        'volume' => 'float',
        'area' => 'float',
        'layers' => 'integer',
        'analysis_time_ms' => 'integer',
    ];

    /**
     * Get the file upload that owns the analysis result.
     */
    public function fileUpload(): BelongsTo
    {
        return $this->belongsTo(FileUpload::class);
    }
}
