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
        Schema::table('file_analysis_results', function (Blueprint $table) {
            // Add analysis_data column if it doesn't exist
            if (!Schema::hasColumn('file_analysis_results', 'analysis_data')) {
                $table->json('analysis_data')->nullable()->after('file_upload_id');
            }

            // Add analyzer_type column if it doesn't exist
            if (!Schema::hasColumn('file_analysis_results', 'analyzer_type')) {
                $table->string('analyzer_type')->nullable()->after('file_upload_id');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('file_analysis_results', function (Blueprint $table) {
            if (Schema::hasColumn('file_analysis_results', 'analysis_data')) {
                $table->dropColumn('analysis_data');
            }

            if (Schema::hasColumn('file_analysis_results', 'analyzer_type')) {
                $table->dropColumn('analyzer_type');
            }
        });
    }
};
