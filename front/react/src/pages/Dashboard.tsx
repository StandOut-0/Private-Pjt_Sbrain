import { useQuery } from '@tanstack/react-query';
import { Bell, BookOpen, CheckCircle2, Clock3, FolderOpen, Plus, Sparkles, Activity } from 'lucide-react';
import { RouteLink as Link } from '../components/RouteLink';
import { getDashboardData } from '../api';

export function Dashboard() {
  const { data, isLoading, isError } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardData });
  if (isLoading) return <div className="loading-card">Dashboard를 불러오는 중입니다…</div>;
  if (isError || !data) return <div className="error-card" role="alert">Dashboard 데이터를 불러오지 못했습니다. 새로고침 후 다시 시도해 주세요.</div>;

  const metrics = [
    { title: '전체 프로젝트', value: data.projects.length, icon: FolderOpen },
    { title: '진행 중', value: data.projects.filter(project => project.status === 'running').length, icon: Activity },
    { title: '완료', value: data.projects.filter(project => project.status === 'done').length, icon: CheckCircle2 },
    { title: '준비 중', value: data.projects.filter(project => project.status === 'ready').length, icon: Clock3 },
  ];

  return <div className="sb-overview dashboard-page">
    <section className="sb-overview-hero" aria-label="워크스페이스 소개"><div className="sb-hero-copy"><h2>다음 아이디어를<br/>현실로 만들어 보세요.</h2><p>프로젝트 진행 상황을 확인하고, 다음 단계를 시작하세요.</p><Link to={data.links.projects}>프로젝트 둘러보기 <i className="bi bi-arrow-up-right" aria-hidden="true"/></Link></div><div className="sb-hero-art" aria-hidden="true"><span className="sb-orbit"/><span className="sb-orbit sb-orbit-two"/><span className="sb-brain-core"><i className="bi bi-cpu"/></span><span className="sb-orbit-label sb-orbit-label-one">IDEA</span><span className="sb-orbit-label sb-orbit-label-two">PROJECT</span><span className="sb-orbit-label sb-orbit-label-three">PROGRESS</span></div></section>
    <section className="sb-overview-metrics" aria-label="프로젝트 요약">{metrics.map(({title,value,icon:Icon})=><Link to={data.links.projects} key={title}><span className="sb-metric-icon"><Icon/></span><span>{title}<strong>{value}<small>개</small></strong></span><i className="bi bi-arrow-up-right" aria-hidden="true"/></Link>)}</section>
    <section className="mb-4"><div className="sb-card-title mb-2 d-flex justify-content-between align-items-center"><span>내 프로젝트</span><div><Link to={data.links.createProject} className="small me-3">+ 새 프로젝트</Link><Link to={data.links.projects} className="small">전체 보기 →</Link></div></div><div className="row g-3">{data.projects.length?data.projects.map(project=><div className="col-md-4" key={project.id}><Link className="sb-dashboard-project sb-project-card position-relative" to={`/projects/${project.id}/`}><span className="small text-secondary position-absolute top-0 end-0 m-3" data-sb-relative-time>{project.updated_at}</span><div className="small text-secondary">{project.code}</div><div className="sb-project-symbol"><FolderOpen/></div><div className="fw-semibold mb-2 sb-project-name">{project.title}</div><div className="small mb-2"><span className={`sb-dot sb-dot-${project.status}`}/>{project.status_label}</div><div className="sb-progress mb-2">{project.stages.map((stage,i)=><div key={`${stage.name}-${i}`} className={`sb-progress-bar ${stage.name.toLowerCase()}`} style={{width:`${stage.progress}%`}}/>)}</div><div className="mb-2">{project.stages.map(stage=><span className={`sb-chip sb-chip-${stage.name.toLowerCase()} small`} key={stage.name}>{stage.name}</span>)}</div><div className="sb-project-completion"><span>전체 진행률</span><strong>{project.progress}%</strong></div></Link></div>):<div className="col-12"><div className="sb-overview-empty">아직 등록된 프로젝트가 없습니다. 새 프로젝트를 만들어 시작해보세요.</div></div>}</div></section>
    <section aria-label="자주 찾는 메뉴"><h2 className="sb-card-title mb-2">자주 찾는 메뉴</h2><div className="sb-dashboard-shortcuts"><Link to={data.links.createProject}><span><Plus/></span><div><strong>새 프로젝트</strong><small>새 아이디어를 프로젝트로 시작합니다.</small></div><i className="bi bi-arrow-up-right"/></Link><Link to={data.links.notifications}><span><Bell/></span><div><strong>알림</strong><small>프로젝트의 최근 소식을 확인합니다.</small></div><i className="bi bi-arrow-up-right"/></Link><Link to={data.links.guide}><span><BookOpen/></span><div><strong>사용자 가이드</strong><small>서비스 이용 방법을 살펴봅니다.</small></div><i className="bi bi-arrow-up-right"/></Link><Link to={data.links.comingSoon}><span><Sparkles/></span><div><strong>Coming Soon</strong><small>준비 중인 기능과 아이디어를 둘러봅니다.</small></div><i className="bi bi-arrow-up-right"/></Link></div></section>
  </div>;
}
