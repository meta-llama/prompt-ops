import React from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface StepDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  onSave?: () => void;
  onCancel?: () => void;
  hideSaveButton?: boolean;
}

export const StepDialog: React.FC<StepDialogProps> = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  onSave,
  onCancel,
  hideSaveButton = false,
}) => {
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onOpenChange(false);
    }
  };

  const handleSave = () => {
    if (onSave) {
      onSave();
    }
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-2xl overflow-y-auto"
      >
        <SheetHeader>
          <div className="flex items-start justify-between">
            <div>
              <SheetTitle>{title}</SheetTitle>
              {description && (
                <SheetDescription className="mt-2">
                  {description}
                </SheetDescription>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancel}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </SheetHeader>

        <div className="mt-6">{children}</div>

        {!hideSaveButton && (
          <div className="flex gap-2 justify-end mt-6 pt-4 border-t">
            <Button variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Save & Close</Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};
