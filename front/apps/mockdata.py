"""Frontend 단계에서 사용하는 임시 데이터.

Backend API / MySQL 연동 시 이 모듈의 함수만 교체하면 되도록
화면 코드에서는 항상 아래 접근 함수를 통해 데이터를 가져온다.
"""

PROJECTS = [
    {
        'id': 1,
        'code': 'Project 01',
        'title': '쇼핑몰 서비스',
        'summary': '반려동물 용품 쇼핑몰 서비스 기획 및 구축',
        'status': 'running',
        'status_label': '진행 중',
        'progress': 70,
        'updated_at': '2026-08-11',
        'stages': [
            {'name': 'Planning', 'state': 'done'},
            {'name': 'Data', 'state': 'done'},
            {'name': 'Design', 'state': 'running'},
            {'name': 'Development', 'state': 'todo'},
        ],
        'tree': [
            {
                'name': 'Planning',
                'files': [
                    {'name': 'PRD.pdf', 'kind': 'pdf', 'size': '842 KB', 'updated_at': '2026-08-11', 'agent': 'Planning'},
                    {'name': '요구사항.md', 'kind': 'doc', 'size': '18 KB', 'updated_at': '2026-08-11', 'agent': 'Planning'},
                ],
            },
            {
                'name': 'Data',
                'files': [
                    {'name': '분석.xlsx', 'kind': 'sheet', 'size': '256 KB', 'updated_at': '2026-08-11', 'agent': 'Data'},
                ],
            },
            {
                'name': 'Design',
                'files': [
                    {'name': '디자인.png', 'kind': 'image', 'size': '1.2 MB', 'updated_at': '2026-08-11', 'agent': 'Creative'},
                    {'name': '로고.png', 'kind': 'image', 'size': '340 KB', 'updated_at': '2026-08-11', 'agent': 'Creative'},
                ],
            },
            {
                'name': 'Development',
                'files': [
                    {'name': 'API.md', 'kind': 'doc', 'size': '22 KB', 'updated_at': '2026-08-11', 'agent': 'Engineering'},
                    {'name': 'DB.pdf', 'kind': 'pdf', 'size': '512 KB', 'updated_at': '2026-08-11', 'agent': 'Engineering'},
                ],
            },
        ],
    },
    {
        'id': 2,
        'code': 'Project 02',
        'title': 'AI 분석 서비스',
        'summary': '사용자 로그 기반 이탈 예측 및 리포트 생성',
        'status': 'done',
        'status_label': '완료',
        'progress': 100,
        'updated_at': '2026-08-09',
        'stages': [
            {'name': 'Planning', 'state': 'done'},
            {'name': 'Data', 'state': 'done'},
            {'name': 'AI', 'state': 'done'},
            {'name': 'Reflection', 'state': 'done'},
        ],
        'tree': [
            {
                'name': 'Data',
                'files': [
                    {'name': '수집로그.csv', 'kind': 'sheet', 'size': '4.1 MB', 'updated_at': '2026-08-08', 'agent': 'Data'},
                ],
            },
            {
                'name': 'AI',
                'files': [
                    {'name': '분석보고서.pdf', 'kind': 'pdf', 'size': '980 KB', 'updated_at': '2026-08-09', 'agent': 'AI'},
                ],
            },
        ],
    },
    {
        'id': 3,
        'code': 'Project 03',
        'title': '신규 프로젝트',
        'summary': '아이디어 정리 단계',
        'status': 'ready',
        'status_label': '준비 중',
        'progress': 0,
        'updated_at': '2026-08-11',
        'stages': [
            {'name': 'Planning', 'state': 'todo'},
        ],
        'tree': [],
    },
]

TASKS = [
    {'id': 1, 'name': '요구사항 분석 및 PRD 작성', 'project': '쇼핑몰 서비스', 'status': 'done',
     'status_label': '완료', 'agent': 'Planning', 'duration': '32.4 sec', 'started_at': '2026-08-11 09:12'},
    {'id': 2, 'name': '경쟁사 데이터 수집', 'project': '쇼핑몰 서비스', 'status': 'running',
     'status_label': '진행 중', 'agent': 'Data', 'duration': '18.2 sec', 'started_at': '2026-08-11 09:40'},
    {'id': 3, 'name': '이탈 예측 모델 학습', 'project': 'AI 분석 서비스', 'status': 'failed',
     'status_label': '실패', 'agent': 'AI', 'duration': '51.7 sec', 'started_at': '2026-08-10 17:03'},
    {'id': 4, 'name': '쇼핑몰 UI 시안 생성', 'project': '쇼핑몰 서비스', 'status': 'running',
     'status_label': '진행 중', 'agent': 'Creative', 'duration': '18.4 sec', 'started_at': '2026-08-11 10:02'},
    {'id': 5, 'name': '생성 결과 검증 및 개선안 도출', 'project': '쇼핑몰 서비스', 'status': 'waiting',
     'status_label': '대기', 'agent': 'Reflection', 'duration': '-', 'started_at': '-'},
]

TASK_METRICS = {'success_rate': '94.2%', 'avg_duration': '32.8 sec', 'error_rate': '5.8%'}

TASK_TREND = {
    'daily': [12, 18, 9, 24, 21, 30, 27],
    'weekly': [64, 82, 71, 95],
    'daily_labels': ['월', '화', '수', '목', '금', '토', '일'],
    'weekly_labels': ['1주', '2주', '3주', '4주'],
}

AGENTS = [
    {
        'key': 'supervisor',
        'name': 'Supervisor Agent',
        'group': 'supervisor',
        'category': '조율',
        'status': 'running',
        'status_label': '실행 중',
        'short': '전체 작업 조율 / Agent 분배',
        'role': '전체 프로젝트 작업을 분석하고 Worker Agent에 작업을 분배한다.',
        'project': 'Project 01 / 쇼핑몰 서비스',
        'task': '프로젝트 요구사항 분석 및 Agent 작업 분배',
        'steps': [
            {'name': '요구사항 분석', 'state': 'done'},
            {'name': 'Planning Agent 호출', 'state': 'done'},
            {'name': 'Data Agent 대기', 'state': 'running'},
        ],
        'flow': 'Supervisor → Planning → Data → Engineering → Reflection',
        'tech': ['LangGraph', 'ReAct', 'A2A', 'MCP', 'LLM'],
        'metrics': [
            {'label': '성공률', 'value': '96.8%'},
            {'label': '평균 실행시간', 'value': '10.2s'},
            {'label': '오류율', 'value': '3.2%'},
        ],
        'children': [],
    },
    {
        'key': 'planning',
        'name': 'Planning Agent',
        'group': 'worker',
        'category': '전략',
        'status': 'waiting',
        'status_label': '대기',
        'short': '기획 / 요구사항',
        'role': '프로젝트 요구사항을 분석하고 기획 문서와 작업 계획을 생성한다.',
        'project': 'Project 01 / 쇼핑몰 서비스',
        'task': '요구사항 분석 및 PRD 작성',
        'steps': [
            {'name': '요구사항 정리', 'state': 'done'},
            {'name': '기능 정의', 'state': 'running'},
            {'name': 'PRD 생성', 'state': 'todo'},
        ],
        'flow': 'Supervisor → Planning → Reflection',
        'tech': ['LLM', 'Prompt Engineering', 'RAG', 'LangChain', 'T5'],
        'metrics': [
            {'label': '성공률', 'value': '95.4%'},
            {'label': '평균 실행시간', 'value': '7.8s'},
            {'label': '요구사항 적중률', 'value': '93.1%'},
        ],
        'children': [],
    },
    {
        'key': 'creative',
        'name': 'Creative Agent',
        'group': 'worker',
        'category': '창의',
        'status': 'running',
        'status_label': '실행 중',
        'short': '디자인 / 이미지',
        'role': '디자인, 이미지 및 시각 콘텐츠를 생성한다.',
        'project': 'Project 01 / 쇼핑몰 서비스',
        'task': '쇼핑몰 UI 및 이미지 생성',
        'steps': [
            {'name': '디자인 요구사항 분석', 'state': 'done'},
            {'name': 'UI 시안 생성', 'state': 'done'},
            {'name': '이미지 생성', 'state': 'running'},
        ],
        'flow': 'Planning → Creative → Engineering',
        'tech': ['Multimodal', 'CNN', 'GAN', 'Image Generation'],
        'metrics': [
            {'label': '성공률', 'value': '91.8%'},
            {'label': '평균 생성시간', 'value': '18.4s'},
            {'label': '평가 점수', 'value': '89.6%'},
        ],
        'children': [],
    },
    {
        'key': 'engineering',
        'name': 'Engineering Agent',
        'group': 'worker',
        'category': '구현',
        'status': 'running',
        'status_label': '실행 중',
        'short': 'Front / Back',
        'role': '프로젝트의 Frontend / Backend 개발을 담당한다.',
        'project': 'Project 01 / Project Detail',
        'task': 'Frontend 완료 / Backend 실행 중',
        'steps': [
            {'name': 'Frontend · 화면 구현 / Bootstrap / JavaScript', 'state': 'done'},
            {'name': 'Backend · API / Django / DB 연동', 'state': 'running'},
        ],
        'flow': 'Creative → Engineering → Reflection',
        'tech': ['Django', 'HTML / CSS', 'Bootstrap', 'JavaScript', 'REST API', 'MySQL'],
        'metrics': [
            {'label': '성공률', 'value': '94.8%'},
            {'label': '평균 실행시간', 'value': '8.2s'},
            {'label': '오류율', 'value': '5.2%'},
        ],
        'children': ['frontend', 'backend'],
    },
    {
        'key': 'frontend',
        'name': 'Frontend Worker',
        'group': 'engineering',
        'category': '구현',
        'status': 'running',
        'status_label': '실행 중',
        'short': '화면 / UI Component',
        'role': '사용자 화면 및 UI Component를 구현한다.',
        'project': 'Project 01 / Project Detail',
        'task': 'Project Detail UI 구현',
        'steps': [
            {'name': '화면 분석', 'state': 'done'},
            {'name': 'Component 생성', 'state': 'done'},
            {'name': 'Bootstrap 적용', 'state': 'done'},
            {'name': 'API 연동', 'state': 'running'},
        ],
        'flow': 'Engineering → Frontend',
        'tech': ['HTML / CSS', 'Bootstrap', 'JavaScript', 'Django', 'REST API'],
        'metrics': [
            {'label': '성공률', 'value': '96.2%'},
            {'label': '평균 실행시간', 'value': '12.4s'},
            {'label': '오류율', 'value': '3.8%'},
        ],
        'children': [],
    },
    {
        'key': 'backend',
        'name': 'Backend Worker',
        'group': 'engineering',
        'category': '구현',
        'status': 'running',
        'status_label': '실행 중',
        'short': 'API / DB',
        'role': 'API, 비즈니스 로직 및 데이터베이스 연동을 구현한다.',
        'project': 'Project 01 / Project API',
        'task': 'Project API 구현',
        'steps': [
            {'name': 'Model 생성', 'state': 'done'},
            {'name': 'API 구현', 'state': 'done'},
            {'name': 'DB 연동', 'state': 'running'},
        ],
        'flow': 'Engineering → Backend',
        'tech': ['Django', 'REST API', 'MySQL', 'ORM', 'Python'],
        'metrics': [
            {'label': '성공률', 'value': '97.1%'},
            {'label': '평균 응답시간', 'value': '1.8s'},
            {'label': '오류율', 'value': '2.9%'},
        ],
        'children': [],
    },
    {
        'key': 'data',
        'name': 'Data Agent',
        'group': 'worker',
        'category': '분석',
        'status': 'waiting',
        'status_label': '대기',
        'short': '수집 / 분석',
        'role': '데이터 수집, 전처리 및 분석을 담당한다.',
        'project': 'Project 01 / 경쟁사 데이터 분석',
        'task': '경쟁사 데이터 수집 및 분석',
        'steps': [
            {'name': 'Crawling', 'state': 'done'},
            {'name': '데이터 전처리', 'state': 'done'},
            {'name': '분석', 'state': 'running'},
        ],
        'flow': 'Supervisor → Data → AI',
        'tech': ['Python', 'SQL', 'Web Crawling', 'Pandas', 'Matplotlib', 'Seaborn'],
        'metrics': [
            {'label': '수집 성공률', 'value': '98.4%'},
            {'label': '처리시간', 'value': '14.2s'},
            {'label': '데이터 오류율', 'value': '1.6%'},
        ],
        'children': [],
    },
    {
        'key': 'ai',
        'name': 'AI Agent',
        'group': 'worker',
        'category': '지능',
        'status': 'running',
        'status_label': '실행 중',
        'short': 'ML / DL / LLM',
        'role': 'ML / DL / NLP / LLM 모델을 활용한 AI 기능을 담당한다.',
        'project': 'Project 01 / 사용자 데이터 분석',
        'task': '사용자 이탈 예측 모델 생성',
        'steps': [
            {'name': '데이터 전처리', 'state': 'done'},
            {'name': '모델 학습', 'state': 'done'},
            {'name': '모델 평가', 'state': 'running'},
        ],
        'flow': 'Data → AI → Reflection',
        'tech': ['Machine Learning', 'Deep Learning', 'NLP', 'LLM', 'Fine-tuning', 'PEFT'],
        'metrics': [
            {'label': 'Accuracy', 'value': '96.2%'},
            {'label': 'F1', 'value': '94.8%'},
            {'label': 'AUC', 'value': '98.7%'},
            {'label': '평균 추론', 'value': '0.8s'},
        ],
        'children': [],
    },
    {
        'key': 'reflection',
        'name': 'Reflection Agent',
        'group': 'worker',
        'category': '성찰',
        'status': 'waiting',
        'status_label': '대기',
        'short': '검증 / 개선',
        'role': 'Agent 실행 결과를 검증하고 오류 및 개선점을 분석한다.',
        'project': 'Project 01 / 프로젝트 결과 검증',
        'task': '생성 결과 검증 및 개선안 도출',
        'steps': [
            {'name': '결과 검증', 'state': 'done'},
            {'name': '오류 분석', 'state': 'done'},
            {'name': '개선안 생성', 'state': 'running'},
        ],
        'flow': 'Engineering → Reflection → Supervisor',
        'tech': ['LLM Judge', 'RAG', 'Vector DB', 'Evaluation', 'Prompt Engineering'],
        'metrics': [
            {'label': '검증 성공률', 'value': '95.7%'},
            {'label': '오류 탐지율', 'value': '93.4%'},
            {'label': '개선 반영률', 'value': '91.2%'},
        ],
        'children': [],
    },
]

KNOWLEDGE_STATS = [
    {'label': 'Knowledge', 'value': 124},
    {'label': 'Memory', 'value': 86},
    {'label': 'Document', 'value': 42},
    {'label': 'Template', 'value': 18},
]

VECTOR_DOCUMENTS = [
    {'project': '쇼핑몰 서비스', 'document': 'PRD.pdf', 'chunks': 24, 'status': 'Indexed'},
    {'project': '쇼핑몰 서비스', 'document': '요구사항.md', 'chunks': 12, 'status': 'Indexed'},
    {'project': 'AI 분석 서비스', 'document': '분석보고서.pdf', 'chunks': 31, 'status': 'Indexed'},
    {'project': 'AI 분석 서비스', 'document': '수집로그.csv', 'chunks': 18, 'status': 'Indexing'},
]

SEARCH_METRICS = [
    {'label': '검색 성공률', 'value': '93.4%'},
    {'label': '평균 검색시간', 'value': '0.42 sec'},
    {'label': 'RAG 적중률', 'value': '91.8%'},
]

CHAT_GUIDE = [
    '1. 주요 상품 / 서비스:',
    '2. 주요 고객층:',
    '3. 만들고 싶은 서비스:',
    '4. 필요한 주요 기능:',
    '5. 참고 서비스 / 디자인:',
]


def get_projects():
    return PROJECTS


def get_project(project_id):
    try:
        project_id = int(project_id)
    except (TypeError, ValueError):
        return None
    for project in PROJECTS:
        if project['id'] == project_id:
            return project
    return None


def get_agents():
    return AGENTS


def get_agent(key):
    for agent in AGENTS:
        if agent['key'] == key:
            return agent
    return None


def get_worker_agents():
    return [agent for agent in AGENTS if agent['group'] == 'worker']


def get_tasks():
    return TASKS


def get_recent_artifacts(limit=5):
    artifacts = []
    for project in PROJECTS:
        for folder in project['tree']:
            for file in folder['files']:
                artifacts.append({
                    'project_id': project['id'],
                    'project': project['title'],
                    'folder': folder['name'],
                    **file,
                })
    artifacts.sort(key=lambda item: item['updated_at'], reverse=True)
    return artifacts[:limit]


def get_agent_executions():
    return [
        {'name': agent['name'], 'status': agent['status'], 'status_label': agent['status_label'],
         'count': index + 1}
        for index, agent in enumerate(AGENTS)
        if agent['group'] != 'engineering'
    ]
