# main_app/migrations/0008_update_site_domain.py 파일 내용

from django.db import migrations
from django.conf import settings

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    site_pk = getattr(settings, 'SITE_ID', 1)
    # !!! 사용할 실제 도메인으로 설정 !!!
    site_domain = 'www.promsense.com'
    site_name = site_domain

    # pk=1 인 Site 객체를 찾아서 업데이트하거나, 없으면 새로 만듭니다.
    Site.objects.update_or_create(
        pk=site_pk,
        defaults={'domain': site_domain, 'name': site_name}
    )
    print(f"\nSite {site_pk} domain ensured to be {site_domain}")

def revert_site_domain(apps, schema_editor):
    # 롤백 시 동작 정의 (필요 없다면 이 함수와 reverse_code 부분 생략 가능)
    Site = apps.get_model('sites', 'Site')
    site_pk = getattr(settings, 'SITE_ID', 1)
    Site.objects.update_or_create(
        pk=site_pk,
        defaults={'domain': 'example.com', 'name': 'example.com'}
    )
    print(f"\nSite {site_pk} domain reverted to example.com")


class Migration(migrations.Migration):

    dependencies = [
        # Site 모델이 확실히 생성된 이후에 실행되도록 sites 앱의 첫 마이그레이션에 의존성 추가
        ('sites', '0001_initial'),
        # 회원님 앱의 이전 마이그레이션
        ("main_app", "0007_alter_customuser_groups_and_more"),
    ]

    operations = [
        migrations.RunPython(update_site_domain, reverse_code=revert_site_domain),
    ]