import "./globals.css";

export const metadata = {
  title: "open-gui",
  description: "Full-fidelity claude CLI session with a live decision tree.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
