import json

from apps.reflection.models import QualityCriterion, ReflectionReport


MOCK_SCORES = {
    'requirement-coverage': (90, '요구사항 목록이 생성되어 요청 내용을 검토할 수 있습니다.'),
    'flow-completeness': (82, '요청 접수부터 결과 검토까지 기본 흐름이 정의되어 있습니다.'),
    'acceptance-clarity': (86, '검증 가능한 완료 기준이 포함되어 있습니다.'),
    'assumption-transparency': (88, '추가 확인 질문과 전제를 별도 항목으로 구분했습니다.'),
}


def evaluate_artifact(artifact):
    existing = ReflectionReport.objects.filter(artifact=artifact).first()
    if existing:
        return existing, False
    criteria = [{'key': item.key, 'label': item.label, 'description': item.description, 'weight': item.weight}
                for item in QualityCriterion.objects.filter(is_active=True)]
    if not criteria or sum(item['weight'] for item in criteria) != 100:
        raise ValueError('ACTIVE_CRITERIA_WEIGHT_INVALID')
    result = json.loads(artifact.content)
    details = []
    weighted_total = 0
    for criterion in criteria:
        score, evidence = MOCK_SCORES.get(criterion['key'], (75, f"'{criterion['label']}' 기준을 정량 mock 평가했습니다."))
        details.append({**criterion, 'score': score, 'weighted_score': round(score * criterion['weight'] / 100, 2), 'evidence': evidence, 'deductions': []})
        weighted_total += score * criterion['weight']
    score = round(weighted_total / 100)
    improvements = []
    if result.get('open_questions'):
        improvements.append('열린 질문을 사용자와 확인한 뒤 요구사항을 구체화하세요.')
    if result.get('target_users') == []:
        improvements.append('대상 사용자와 이용 맥락을 추가로 정의하세요.')
    report = ReflectionReport.objects.create(
        artifact=artifact,
        run=artifact.task.run,
        criteria_snapshot=criteria,
        score_details=details,
        total_score=score,
        summary='규칙 기반 mock 평가입니다. 실제 모델 심사 점수가 아닙니다.',
        improvements=improvements,
        is_mock=True,
    )
    return report, True
