import Link from "next/link";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/import", label: "Import" },
  { href: "/schedule", label: "Schedule" },
  { href: "/constraints", label: "Constraints" },
  { href: "/compare", label: "Compare" },
];

export function Sidebar() {
  return (
    <aside className="flex w-60 flex-col gap-1 border-r border-border bg-sidebar p-4 text-sidebar-foreground">
      <h1 className="mb-4 text-lg font-bold text-primary">EVO Scheduler</h1>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm font-medium hover:bg-primary hover:text-white transition-colors"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
