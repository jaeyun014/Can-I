import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Can I?",
  description: "사진과 물건 이름으로 생활 안전 판단을 돕는 MVP"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
