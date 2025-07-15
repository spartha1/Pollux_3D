<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\FileUpload;
use App\Http\Controllers\FileAnalysisController;

class ReAnalyzeFiles extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'files:reanalyze {id?}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Re-analyze uploaded files with new manufacturing metrics';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $id = $this->argument('id');
        
        if ($id) {
            $fileUpload = FileUpload::find($id);
            if (!$fileUpload) {
                $this->error("File with ID {$id} not found");
                return 1;
            }
            $files = [$fileUpload];
        } else {
            $files = FileUpload::whereIn('extension', ['stl', 'STL'])->get();
        }

        $controller = new FileAnalysisController();
        
        foreach ($files as $file) {
            $this->info("Re-analyzing file: {$file->filename_original}");
            
            try {
                $controller->analyze($file);
                $this->info("✓ Successfully analyzed {$file->filename_original}");
            } catch (\Exception $e) {
                $this->error("✗ Failed to analyze {$file->filename_original}: {$e->getMessage()}");
            }
        }

        $this->info("Re-analysis completed!");
        return 0;
    }
}
