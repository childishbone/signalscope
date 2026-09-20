export function Panel({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-border bg-panel ${className}`}>
      {title && (
        <h2 className="border-b border-border px-4 py-3 text-sm font-medium">{title}</h2>
      )}
      {children}
    </section>
  );
}