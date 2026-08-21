import type { Metadata } from "next";
import { Barlow_Condensed, Roboto_Mono, Source_Sans_3 } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { AppShell } from "@/components/AppShell";

/* Ba font, mỗi font một vai trò. Đều khai subset vietnamese — thiếu nó thì
   chữ có dấu rơi về font dự phòng của hệ điều hành, cao thấp không đều. */

// Chữ thân: dễ đọc ở cỡ nhỏ 9–11px trong ô lưới thời khoá biểu
const body = Source_Sans_3({
  variable: "--font-body",
  subsets: ["latin", "latin-ext", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

// Tiêu đề: hẹp ngang nên tiêu đề tiếng Việt dài không vỡ dòng
const display = Barlow_Condensed({
  variable: "--font-display",
  subsets: ["latin", "latin-ext", "vietnamese"],
  weight: ["500", "600", "700"],
  display: "swap",
});

// Số liệu: chữ đều bề ngang nên mã phòng, số tiết, giờ thẳng cột
const mono = Roboto_Mono({
  variable: "--font-mono-code",
  subsets: ["latin", "latin-ext", "vietnamese"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Xếp TKB — CĐ Xây dựng Công trình Đô thị",
  description:
    "Phần mềm sắp xếp thời khoá biểu cho Trường Cao đẳng Xây dựng Công trình Đô thị",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="vi"
      className={`${body.variable} ${display.variable} ${mono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full">
        <AuthProvider>
          <ThemeProvider>
            <AppShell>{children}</AppShell>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
