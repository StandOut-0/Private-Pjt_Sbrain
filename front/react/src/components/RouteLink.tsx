import type { AnchorHTMLAttributes, ReactNode } from 'react';

export function RouteLink({ to, children, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { to: string; children: ReactNode }) {
  return <a href={to} {...props}>{children}</a>;
}
