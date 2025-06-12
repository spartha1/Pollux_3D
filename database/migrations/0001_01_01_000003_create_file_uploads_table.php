<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('file_uploads', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->onDelete('cascade');

            $table->string('filename_original');
            $table->string('filename_stored');
            $table->string('extension', 10);
            $table->string('mime_type')->nullable();
            $table->unsignedBigInteger('size');

            $table->enum('status', ['uploaded', 'processing', 'processed', 'failed'])->default('uploaded');

            $table->string('storage_path'); // private/models/1/file.stl
            $table->string('disk')->default('local'); // útil si luego pasas a s3, etc.

            $table->timestamp('uploaded_at')->useCurrent();
            $table->timestamp('processed_at')->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('file_uploads');
    }
};
