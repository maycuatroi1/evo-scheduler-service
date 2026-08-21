import { ImportWizard } from "@/components/import/ImportWizard";

export default function ImportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Import</h2>
        <p className="text-sm text-foreground-2">
          Tải lên workbook Excel, kiểm tra, và commit vào backend.
        </p>
      </div>
      <ImportWizard />
    </div>
  );
}
