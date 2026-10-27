import { AuthGate } from "@/components/AuthProvider";
import { Sidebar } from "@/components/Sidebar";
import { ToastProvider } from "@/components/Toast";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <ToastProvider>
        <div className="flex min-h-screen flex-col md:flex-row">
          <Sidebar />
          <main className="min-w-0 flex-1 p-5 md:p-8">{children}</main>
        </div>
      </ToastProvider>
    </AuthGate>
  );
}
