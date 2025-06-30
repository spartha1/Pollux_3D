<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class FileError extends Model
{
    use HasFactory;

    protected $fillable = [
        'file_upload_id',
        'error_message',
        'stack_trace',
        'occurred_at'
    ];

    protected $casts = [
        'occurred_at' => 'datetime'
    ];

    /**
     * Get the file upload that owns the error.
     */
    public function fileUpload(): BelongsTo
    {
        return $this->belongsTo(FileUpload::class);
    }
}
