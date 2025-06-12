<?php

namespace App\Policies;

use App\Models\FileUpload;
use App\Models\User;

class FileUploadPolicy
{
    /**
     * Determine whether the user can view the model.
     */
    public function view(User $user, FileUpload $fileUpload): bool
    {
        return $user->id === $fileUpload->user_id;
    }

    /**
     * Determine whether the user can download the model.
     */
    public function download(User $user, FileUpload $fileUpload): bool
    {
        return $user->id === $fileUpload->user_id;
    }

    /**
     * Determine whether the user can delete the model.
     */
    public function delete(User $user, FileUpload $fileUpload): bool
    {
        return $user->id === $fileUpload->user_id;
    }
}
