export function PageHeader({
  title,
  description,
  sampleData = true,
}: {
  title: string;
  description?: string;
  sampleData?: boolean;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {sampleData && (
        <span className="rounded-md border border-border px-2 py-1 text-xs text-muted">
          Sample data
        </span>
      )}
    </div>
  );
}