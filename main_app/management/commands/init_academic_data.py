from django.core.management.base import BaseCommand
from main_app.models import AcademicYear, Holiday, Vacation
from datetime import date

class Command(BaseCommand):
    help = "Initialise l'année académique, les jours fériés et les vacances."

    def handle(self, *args, **options):
        # 1. Créer ou mettre à jour l'année académique (avec la date de début comme clé unique)
        start_year = 2024
        end_year = 2025
        AcademicYear.objects.update_or_create(
            start_date=date(start_year, 9, 1),
            defaults={'end_date': date(end_year, 6, 30)}
        )

        # 2. Définir les jours fériés (à adapter selon vos besoins)
        holidays = [
            {'date': date(start_year, 9, 16), 'description': 'Almaoulid'},   # 16/09/2024
            {'date': date(start_year, 11, 6), 'description': 'MARCHE VERTE'},  # 06/11/2024
            {'date': date(start_year, 11, 18), 'description': 'Independance'},  # 18/11/2024
            {'date': date(end_year, 1, 1), 'description': 'Année'},        # 01/01/2025
            {'date': date(end_year, 1, 11), 'description': 'Indépendance'},  # 11/01/2025
           {'date': date(end_year, 1, 14), 'description': 'Année Amazigh'}, # 14/01/2025
            {'date': date(end_year, 5, 1), 'description': 'Travail'},      # 01/05/2025
            {'date': date(end_year, 6, 6), 'description': 'Adha'},         # 06/06/2025
            {'date': date(end_year, 6, 27), 'description': 'Moharam'},    # 27/06/2025
        ]

        for holiday_data in holidays:
            Holiday.objects.update_or_create(
                date=holiday_data['date'],
                defaults={'description': holiday_data['description']}
            )

        # 3. Définir les périodes de vacances (à adapter selon vos besoins)
        vacations = [
            {'start_date': date(end_year, 1, 26), 'end_date': date(end_year, 2, 2), 'description': 'Vac. 1er Semestre'}, # 26/01/2025 - 02/02/2025
            {'start_date': date(end_year, 3, 31), 'end_date': date(end_year, 4, 3), 'description': 'Fitr'},   # 31/03/2025 - 03/04/2025
             {'start_date': date(end_year, 5, 4), 'end_date': date(end_year, 5, 11), 'description': 'Vac Printemps'}, # 04/05/2025 - 11/05/2025
        ]

        for vacation_data in vacations:
            Vacation.objects.update_or_create(
                 start_date = vacation_data['start_date'],
                 defaults = {
                     'end_date': vacation_data['end_date'],
                    'description': vacation_data['description']
                     }
                )

        self.stdout.write(self.style.SUCCESS('Données académiques initialisées avec succès'))