import re

from django.db.models import Q
from django.db.models.functions import Substr

from apps.management.models import KnowledgeDocument


TOKEN_RE = re.compile(r'[가-힣A-Za-z0-9]{2,}')
MAX_DOCUMENTS_TO_SCAN = 100
MAX_CONTENT_SCAN_CHARS = 12_000
MAX_REFERENCES = 3
MAX_EXCERPT_CHARS = 1600


def retrieve_knowledge(project_id, request_data):
    """Return a few scoped, keyword-matched references for a Planning request."""
    query = ' '.join([
        str(request_data.get('objective', '')),
        str(request_data.get('user_request', '')),
        ' '.join(str(item) for item in request_data.get('known_requirements', []) if isinstance(item, str)),
    ])
    tokens = {token.casefold() for token in TOKEN_RE.findall(query)}
    if not tokens:
        return []

    documents = KnowledgeDocument.objects.filter(scope=KnowledgeDocument.SCOPE_GLOBAL)
    if project_id:
        documents = KnowledgeDocument.objects.filter(
            Q(scope=KnowledgeDocument.SCOPE_GLOBAL) | Q(scope=KnowledgeDocument.SCOPE_PROJECT, project_id=project_id)
        )

    ranked = []
    searchable = documents.annotate(
        search_content=Substr('content', 1, MAX_CONTENT_SCAN_CHARS)
    ).values('id', 'title', 'scope', 'updated_at', 'search_content').order_by('-updated_at', '-id')
    for document in searchable[:MAX_DOCUMENTS_TO_SCAN]:
        title_tokens = {token.casefold() for token in TOKEN_RE.findall(document['title'])}
        content = document['search_content'] or ''
        content_folded = content.casefold()
        title_hits = tokens & title_tokens
        content_hits = tokens & {token.casefold() for token in TOKEN_RE.findall(content)}
        score = len(title_hits) * 3 + len(content_hits)
        if score:
            ranked.append((score, document, content_folded, content_hits))

    ranked.sort(key=lambda item: (item[0], item[1]['updated_at'], item[1]['id']), reverse=True)
    references = []
    for score, document, content_folded, content_hits in ranked[:MAX_REFERENCES]:
        excerpt_start = 0
        for token in sorted(content_hits, key=len, reverse=True):
            position = content_folded.find(token)
            if position >= 0:
                excerpt_start = max(0, position - MAX_EXCERPT_CHARS // 4)
                break
        excerpt = content[excerpt_start:excerpt_start + MAX_EXCERPT_CHARS].strip()
        references.append({
            'document_id': document['id'],
            'title': document['title'],
            'scope': document['scope'],
            'excerpt': excerpt,
            'match_score': score,
        })
    return references
