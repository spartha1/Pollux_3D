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
        Schema::create('file_errors', function (Blueprint $table) {
            $table->id();
            $table->foreignId('file_upload_id')->constrained()->onDelete('cascade');

            $table->text('error_message');
            $table->longText('stack_trace')->nullable();
            $table->timestamp('occurred_at')->useCurrent();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('file_errors');
    }
};
