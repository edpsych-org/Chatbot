"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function VerifyAccessRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center p-8">
        <h2 className="text-xl font-bold text-on-surface mb-2">Verification Updated</h2>
        <p className="text-slate-500">This verification method has been updated. Please check your email for a new invitation link.</p>
        <p className="text-slate-400 text-sm mt-4">Redirecting to login...</p>
      </div>
    </div>
  );
}
