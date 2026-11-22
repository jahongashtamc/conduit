import type { Metadata } from 'next';
import { Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700'],
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono-jb',
  weight: ['400', '500', '700'],
  display: 'swap',
});

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
    <html lang="uz" className={`dark w-screen h-screen m-0 p-0 overflow-hidden ${spaceGrotesk.variable} ${jetbrainsMono.variable}`}>
      <body className="w-screen h-screen m-0 p-0 overflow-hidden text-zinc-100 flex flex-col font-sans">
        {children}
      </body>
    </html>
  );
}
