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
        // Solo agregar campos si no existen (para evitar errores si ya están)
        Schema::table('file_uploads', function (Blueprint $table) {
            // Verificar si el campo uuid no existe y agregarlo si es necesario
            if (!Schema::hasColumn('file_uploads', 'uuid')) {
                $table->string('uuid')->unique()->after('id');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('file_uploads', function (Blueprint $table) {
            if (Schema::hasColumn('file_uploads', 'uuid')) {
                $table->dropColumn('uuid');
            }
        });
    }
};