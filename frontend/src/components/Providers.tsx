'use client';

import React, { useMemo } from 'react';
import { ToastProvider } from '@/components/ui';
import ChatbotWidget from '@/components/ChatbotWidget';
import AuthGate from '@/components/AuthGate';

export default function Providers({ children }: { children: React.ReactNode }) {
    // useEffect 없이 선언적으로 항상 표시하도록 수정 (필요 시 특정 경로 제외 로직 추가 가능)
    const showChatbot = true;

    return (
        <ToastProvider>
            <AuthGate>
                {children}
                {showChatbot && <ChatbotWidget />}
            </AuthGate>
        </ToastProvider>
    );
}
