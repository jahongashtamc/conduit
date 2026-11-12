import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Conduit — AI Agentlar Boshqaruv Dashboardi',
  description: 'AI subagentlar va ilovalar boshqaruv ekotizimi',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="uz" className="dark w-screen h-screen m-0 p-0 overflow-hidden bg-slate-950">
      <body className="w-screen h-screen m-0 p-0 overflow-hidden bg-slate-950 text-slate-100 flex flex-col font-sans">
        {children}
      </body>
    </html>
  );
}
