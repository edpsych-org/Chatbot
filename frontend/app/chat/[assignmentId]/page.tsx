'use client';

import { useParams } from 'next/navigation';
import HybridChat from '@/src/components/chat/HybridChat';

export default function HybridChatPage() {
  const params = useParams();
  const assignmentId = params.assignmentId as string;

  return (
    <div className="h-screen w-full">
      <HybridChat assignmentId={assignmentId} />
    </div>
  );
}
