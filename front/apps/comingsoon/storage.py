"""Coming Soon 문서 파일 저장소.

기획안에 따라 DB가 아닌 Markdown 파일로 추가 / 수정 / 삭제를 관리한다.
삭제한 문서는 지우지 않고 deleted 폴더로 이동한다.
"""

import re
from datetime import date

import yaml
from django.conf import settings

STATUS_CHOICES = ['아이디어', '연구 예정', '개발 예정', '보류', '완료']
CATEGORY_CHOICES = ['Agent', 'LLM', 'Data', 'Engineering', 'Infra', 'ETC']

# 모든 문서가 공유하는 메타데이터 공통 form
META_FORM = {
    'title': '',
    'summary': '',
    'status': '아이디어',
    'category': 'Agent',
    'technologies': [],
    'related_agents': [],
    'created_at': '',
    'updated_at': '',
}

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', re.DOTALL)


def _root():
    path = settings.COMING_SOON_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _deleted_root():
    path = settings.COMING_SOON_DELETED_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(title):
    slug = re.sub(r'[^0-9A-Za-z가-힣]+', '-', title).strip('-').lower()
    if not re.fullmatch(r'[-a-zA-Z0-9_]+', slug):
        raise ValueError(
            '제목에 한글 또는 URL에서 사용할 수 없는 문자가 포함되어 있습니다.'
        )

    return slug

def _split_front_matter(text):
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    return meta, match.group(2)


def _dump(meta, body):
    front = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    return f'---\n{front}\n---\n\n{body.strip()}\n'


def _to_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    return [item.strip() for item in str(value).split(',') if item.strip()]


def normalize(meta):
    normalized = dict(META_FORM)
    normalized.update({key: value for key, value in meta.items() if key in META_FORM})
    normalized['technologies'] = _to_list(normalized['technologies'])
    normalized['related_agents'] = _to_list(normalized['related_agents'])
    return normalized


def list_documents(keyword='', status='', category=''):
    documents = []
    for path in sorted(_root().glob('*.md')):
        document = read_document(path.stem)
        if not document:
            continue
        if keyword and keyword.lower() not in (document['title'] + document['summary']).lower():
            continue
        if status and document['status'] != status:
            continue
        if category and document['category'] != category:
            continue
        documents.append(document)
    return documents


def read_document(slug):
    path = _root() / f'{slug}.md'
    if not path.exists():
        return None
    meta, body = _split_front_matter(path.read_text(encoding='utf-8'))
    document = normalize(meta)
    document['slug'] = slug
    document['body'] = body.strip()
    return document


def save_document(slug, meta, body):
    document = normalize(meta)
    today = date.today().isoformat()
    document['created_at'] = document['created_at'] or today
    document['updated_at'] = today

    new_slug = slug or slugify(document['title'])    
    path = _root() / f'{new_slug}.md'
    path.write_text(_dump(document, body), encoding='utf-8')
    return new_slug


def delete_document(slug):
    path = _root() / f'{slug}.md'
    if not path.exists():
        return False
    target = _deleted_root() / f'{slug}-{date.today().isoformat()}.md'
    path.rename(target)
    return True
