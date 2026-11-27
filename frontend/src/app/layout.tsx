import type { Metadata } from 'next';
import './globals.css';

// Shriftlar ATAYLAB `next/font/google` orqali olinmaydi.
//
// Sabab (o'lchangan, 2026-11-27): `next/font/google` HAR build'da Google
// Fonts'ga tarmoq so'rovi yuboradi. CI'da bu so'rov muvaffaqiyatsiz bo'lsa
// build butunlay yiqiladi:
//   TypeError: Cannot read properties of null (reading '1')
//     at next/dist/compiled/@next/font/dist/google/loader.js:122
//     at Object.<anonymous> (.../next/font/google/target.css?...Space_Grotesk...)
// Ya'ni build tashqi tarmoqqa bog'liq bo'lib qolgan — bu flaky.
//
// Endi shriftlar oddiy `<link>` bilan yuklanadi: brauzer ularni runtime'da
// oladi, build esa tarmoqsiz ishlaydi. O'zgaruvchilar nomi o'zgarmadi
// (`--font-display`, `--font-mono-jb`), shuning uchun tailwind.config.js
// va mavjud CSS o'zgartirilmaydi. Agar Google Fonts yetib bo'lmasa,
// Tailwind'dagi `system-ui` / `Consolas` fallback'lari ishlaydi.

const FONT_LINK =
  'https://fonts.googleapis.com/css2' +
  '?family=Space+Grotesk:wght@400;500;600;700' +
  '&family=JetBrains+Mono:wght@400;500;700' +
  '&display=swap';

export const metadata: Metadata = {
  title: 'Nexus — AI Agentlar Studiyasi',
  description: 'AI subagentlar va ilovalar boshqaruv ekotizimi',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="uz" className="dark w-screen h-screen m-0 p-0 overflow-hidden">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="stylesheet" href={FONT_LINK} />
        {/*
          Tailwind `.font-sans` / `.font-mono` shu o'zgaruvchilarga tayanadi.
          `next/font` ularni avtomatik yaratardi; endi o'zimiz beramiz.
        */}
        <style
          dangerouslySetInnerHTML={{
            __html: `:root{--font-display:'Space Grotesk',Inter,system-ui,sans-serif;--font-mono-jb:'JetBrains Mono',Consolas,monospace}`,
          }}
        />
      </head>
      <body className="w-screen h-screen m-0 p-0 overflow-hidden text-zinc-100 flex flex-col font-sans">
        {children}
      </body>
    </html>
  );
}
