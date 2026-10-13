import '@/styles/globals.css';
import { Metadata } from 'next';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Industrial Maintenance Copilot · AI Predictive Maintenance Platform',
  description: 'Closed-loop industrial maintenance platform from telemetry, diagnosis, and risk prediction to work orders and verification',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" translate="no" className="notranslate">
      <head>
        <meta name="google" content="notranslate" />
      </head>
      <body className="min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
