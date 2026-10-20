import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

export const projectSchema = z.object({
  title: z.string().trim().min(2, '프로젝트명은 2자 이상 입력해 주세요.').max(80, '프로젝트명은 80자 이하여야 합니다.'),
  summary: z.string().trim().max(500, '설명은 500자 이하여야 합니다.').optional(),
});
export type ProjectFormValues = z.infer<typeof projectSchema>;

export function useProjectForm() {
  return useForm<ProjectFormValues>({ resolver: zodResolver(projectSchema), defaultValues: { title: '', summary: '' } });
}
