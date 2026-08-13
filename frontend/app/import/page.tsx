import { ImportWizard } from "@/components/import/ImportWizard";

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Import</h2>
        <p className="text-sm text-foreground/60">
          Upload an Excel workbook, map columns, preview validation, and commit.
        </p>
      </div>
      <ImportWizard />
    </div>
  );
}
