declare global { interface Window { sbToast?: (message: string, variant?: string) => void } }

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
  },
});

export type DashboardData = {
  projects: Array<{ id: number; code: string; title: string; status: string; status_label: string; progress: number; updated_at: string; stages: Array<{ name: string; progress: number }> }>;
  links: Record<string, string>;
};

export async function getDashboardData(): Promise<DashboardData> {
  const node = document.getElementById('sb-react-data');
  if (!node?.textContent) {
    return {
      projects: [{ id: 1, code: 'Project 01', title: '쇼핑몰 서비스', status: 'running', status_label: '진행 중', progress: 70, updated_at: '미리보기', stages: [{ name: 'Planning', progress: 25 }, { name: 'Design', progress: 20 }] }],
      links: { projects: '/projects/list/', createProject: '/projects/create/', notifications: '/notifications/', guide: '/user-guide/', comingSoon: '/coming-soon/' },
    };
  }
  const payload = JSON.parse(node.textContent) as { data: DashboardData; links: Record<string, string> };
  return { ...payload.data, links: { ...payload.links, ...payload.data.links } };
}

export type AppPayload = { page: string; data: Record<string, any>; navProjects?: any[]; notifications?: Array<{ id: string; title: string; message: string; time: string; type: string; read: boolean; url: string }>; links: Record<string, string>; user: { name: string; role: string; role_label: string; is_admin: boolean; email?: string } | null };
export function getPayload(): AppPayload {
  const node = document.getElementById('sb-react-data');
  return node?.textContent ? JSON.parse(node.textContent) as AppPayload : { page: 'dashboard', data: {}, links: {}, user: null };
}

export function csrfToken() {
  return document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value || '';
}
