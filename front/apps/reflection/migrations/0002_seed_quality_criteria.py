from django.db import migrations


def seed_criteria(apps, schema_editor):
    Criterion = apps.get_model('reflection', 'QualityCriterion')
    Criterion.objects.bulk_create([
        Criterion(key='requirement-coverage', label='요구사항 충족', description='사용자 요청과 기능 요구사항의 정합성', weight=40, sort_order=1),
        Criterion(key='flow-completeness', label='사용 흐름 완성도', description='주요 사용자 흐름과 예외 경로의 구체성', weight=25, sort_order=2),
        Criterion(key='acceptance-clarity', label='완료 기준 명확성', description='검증 가능한 인수 기준의 구체성', weight=25, sort_order=3),
        Criterion(key='assumption-transparency', label='가정과 질문 명시', description='확인되지 않은 사항과 가정의 투명성', weight=10, sort_order=4),
    ])


class Migration(migrations.Migration):
    dependencies = [('reflection', '0001_initial')]
    operations = [migrations.RunPython(seed_criteria, migrations.RunPython.noop)]
