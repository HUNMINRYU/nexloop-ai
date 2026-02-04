'use client';

import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from '@/components/ui';
import ChatbotWidget from '@/components/ChatbotWidget';
import AuthGate from '@/components/AuthGate';

export default function Providers({ children }: { children: React.ReactNode }) {
    // 리렌더링 시에도 인스턴스가 유지되도록 useState 사용
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60 * 1000,
                retry: 1,
            },
        },
    }));

    const showChatbot = true;

    return (
        <QueryClientProvider client={queryClient}>
            <ToastProvider>
                <AuthGate>
                    {children}
                    {showChatbot && <ChatbotWidget />}
                </AuthGate>
            </ToastProvider>
        </QueryClientProvider>
    );
}
