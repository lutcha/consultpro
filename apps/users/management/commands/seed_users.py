from django.core.management.base import BaseCommand
from apps.users.models import User


USERS = [
    {
        'email': 'ana.silva@consultpro.cv',
        'username': 'ana.silva',
        'first_name': 'Ana',
        'last_name': 'Silva',
        'role': 'consultant',
        'availability': 'available',
        'skills': ['Saúde Pública', 'Gestão de Projectos', 'M&E', 'Epidemiologia'],
        'languages': ['Português', 'Inglês', 'Francês'],
        'bio': 'Consultora sénior com 12 anos de experiência em projectos de saúde pública para organizações internacionais.',
        'password': 'ConsultPro2026!',
    },
    {
        'email': 'carlos.mendes@consultpro.cv',
        'username': 'carlos.mendes',
        'first_name': 'Carlos',
        'last_name': 'Mendes',
        'role': 'senior_consultant',
        'availability': 'available',
        'skills': ['Educação', 'Desenvolvimento Curricular', 'Formação de Professores', 'EMIS'],
        'languages': ['Português', 'Inglês', 'Espanhol'],
        'bio': 'Especialista em sistemas educativos africanos com projectos em 15 países.',
        'password': 'ConsultPro2026!',
    },
    {
        'email': 'fatima.costa@consultpro.cv',
        'username': 'fatima.costa',
        'first_name': 'Fátima',
        'last_name': 'Costa',
        'role': 'consultant',
        'availability': 'available',
        'skills': ['Governação', 'Administração Pública', 'Descentralização', 'PEFA'],
        'languages': ['Português', 'Inglês', 'Francês', 'Árabe'],
        'bio': 'Consultora em reforma do sector público com foco em África Ocidental e Médio Oriente.',
        'password': 'ConsultPro2026!',
    },
    {
        'email': 'joao.ferreira@consultpro.cv',
        'username': 'joao.ferreira',
        'first_name': 'João',
        'last_name': 'Ferreira',
        'role': 'manager',
        'availability': 'available',
        'skills': ['Gestão de Propostas', 'Financiamento UE', 'Banco Mundial', 'PNUD'],
        'languages': ['Português', 'Inglês', 'Francês'],
        'bio': 'Gestor de propostas com track record de 85% de aprovação em concursos internacionais.',
        'password': 'ConsultPro2026!',
    },
    {
        'email': 'maria.rodrigues@consultpro.cv',
        'username': 'maria.rodrigues',
        'first_name': 'Maria',
        'last_name': 'Rodrigues',
        'role': 'consultant',
        'availability': 'partial',
        'skills': ['Ambiente', 'Alterações Climáticas', 'REDD+', 'Biodiversidade'],
        'languages': ['Português', 'Inglês'],
        'bio': 'Especialista ambiental com experiência em CPLP e projectos de adaptação climática.',
        'password': 'ConsultPro2026!',
    },
    {
        'email': 'pedro.neves@consultpro.cv',
        'username': 'pedro.neves',
        'first_name': 'Pedro',
        'last_name': 'Neves',
        'role': 'consultant',
        'availability': 'available',
        'skills': ['Infra-estruturas', 'Engenharia Civil', 'PPP', 'Transportes'],
        'languages': ['Português', 'Inglês', 'Francês'],
        'bio': 'Engenheiro civil com 18 anos em projectos de infra-estruturas para o BAfD e BM.',
        'password': 'ConsultPro2026!',
    },
]


class Command(BaseCommand):
    help = 'Seed initial user profiles for testing'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for data in USERS:
            password = data.pop('password')
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(f"  skip  {data['email']}")
                data['password'] = password
                skipped += 1
                continue

            user = User(**data)
            user.set_password(password)
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  created  {data['email']}"))
            data['password'] = password
            created += 1

        self.stdout.write(self.style.SUCCESS(f'\nDone: {created} created, {skipped} skipped'))
