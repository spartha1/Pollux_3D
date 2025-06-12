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
        Schema::create('file_analysis_results', function (Blueprint $table) {
            $table->id();
            $table->foreignId('file_upload_id')->constrained()->onDelete('cascade');

            $table->json('dimensions')->nullable(); // { width: x, height: y, depth: z }
            $table->float('volume')->nullable();    // para archivos 3D
            $table->float('area')->nullable();      // para archivos 2D

            $table->integer('layers')->nullable();  // AI, EPS, DWG
            $table->json('metadata')->nullable();  // campos adicionales según tipo

            $table->integer('analysis_time_ms')->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('file_analysis_results');
    }
};
