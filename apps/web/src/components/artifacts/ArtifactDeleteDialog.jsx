/**
 * ArtifactDeleteDialog Component
 * Confirmation dialog for deleting artifacts (single or bulk)
 */

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog.jsx'
import { Loader2 } from 'lucide-react'

const ArtifactDeleteDialog = ({
  open,
  onOpenChange,
  deleteTarget,
  selectedCount,
  deleting,
  onConfirm
}) => {
  const isBulkDelete = deleteTarget === 'bulk'

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isBulkDelete 
              ? `Delete ${selectedCount} Artifact(s)?`
              : 'Delete Artifact?'
            }
          </AlertDialogTitle>
          <AlertDialogDescription>
            {isBulkDelete 
              ? `Are you sure you want to delete ${selectedCount} selected artifact(s)? This will permanently delete the artifacts, their normalized content, evaluations, and all related data from storage. This action cannot be undone.`
              : 'Are you sure you want to delete this artifact? This will permanently delete the artifact, its normalized content, evaluations, and all related data from storage. This action cannot be undone.'
            }
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={deleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

export default ArtifactDeleteDialog

