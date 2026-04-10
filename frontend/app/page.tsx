'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        switch (parsedUser.role?.toUpperCase()) {
          case 'PSYCHOLOGIST':
            router.replace('/psychologist/dashboard');
            break;
          case 'ADMIN':
            router.replace('/admin/dashboard');
            break;
          case 'PARENT':
          default:
            router.replace('/dashboard');
            break;
        }
      } catch {
        router.replace('/login');
      }
    } else {
      router.replace('/login');
    }
  }, [router]);

  return null;
}
