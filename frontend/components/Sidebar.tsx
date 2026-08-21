"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Item = { href: string; label: string; icon: string; badge?: string };
type Group = { title: string; items: Item[] };

/* Nhóm theo đúng luồng công việc của cán bộ đào tạo, không theo cấu trúc
   kỹ thuật. Năm bước xếp lịch gộp vào một mục có thanh tiến trình riêng. */
const GROUPS: Group[] = [
  {
    title: "Vận hành",
    items: [
      { href: "/", label: "Tổng quan", icon: "▤" },
      { href: "/schedule", label: "Thời khoá biểu", icon: "▦" },
      { href: "/xep-lich", label: "Xếp thời khoá biểu", icon: "▶" },
      { href: "/tinh-chinh", label: "Tinh chỉnh thủ công", icon: "✎" },
      { href: "/ke-thua", label: "Kế thừa lịch cũ", icon: "♻" },
      { href: "/bang-giao-vien", label: "Bảng giáo viên", icon: "▥" },
      { href: "/lich-cua-toi", label: "Lịch của tôi", icon: "☑" },
    ],
  },
  {
    title: "Dữ liệu",
    items: [
      { href: "/lop", label: "Lớp & nhóm nghề", icon: "◫" },
      { href: "/giao-vien", label: "Giáo viên", icon: "☺" },
      { href: "/phong", label: "Phòng & xưởng", icon: "⌗" },
      { href: "/mo-dun", label: "Mô-đun", icon: "≡" },
      { href: "/import", label: "Nhập từ Excel", icon: "⤓" },
    ],
  },
  {
    title: "Cấu hình",
    items: [
      { href: "/rang-buoc", label: "Ràng buộc", icon: "⚖" },
      { href: "/khung-gio", label: "Khung giờ & mốc giờ", icon: "◷" },
      { href: "/chuong-trinh", label: "Chương trình đào tạo", icon: "◈" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 flex-col border-r border-black/10 bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-2.5 border-b border-white/10 px-4 py-3.5">
        <span
          aria-hidden
          className="grid h-9 w-9 flex-none place-items-center rounded-md bg-white font-display text-[13px] font-bold text-sidebar"
        >
          CUWC
        </span>
        <div className="min-w-0">
          <b className="block font-display text-[19px] font-bold leading-tight text-white">
            Xếp TKB
          </b>
          <span className="block text-[9.5px] uppercase leading-snug tracking-wide opacity-60">
            CĐ Xây dựng Công trình Đô thị
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        {GROUPS.map((group) => (
          <div key={group.title} className="pb-1.5 pt-2.5">
            <p className="px-4 pb-1.5 text-[9.5px] font-semibold uppercase tracking-[0.13em] opacity-45">
              {group.title}
            </p>
            {group.items.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2.5 border-l-[3px] px-4 py-[7px] text-[13.5px] transition-colors ${
                    active
                      ? "border-l-vocational bg-white/10 font-semibold text-white"
                      : "border-l-transparent hover:bg-white/[0.06] hover:text-white"
                  }`}
                >
                  <i className="w-4 flex-none text-center text-[13px] not-italic opacity-80">
                    {item.icon}
                  </i>
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="border-t border-white/10 px-4 py-3 text-[11px] opacity-60">
        Học kỳ I · 2026–2027
      </div>
    </aside>
  );
}
