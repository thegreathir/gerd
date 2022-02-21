import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from core.models import Word


class Command(BaseCommand):
    help = 'Clears words and imports new words from given CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file to import words from'
        )

    def handle(self, *args, **options):

        try:
            words_df: pd.DataFrame = pd.read_csv(
                options['csv_file']
            )
        except Exception as e:
            raise CommandError(f'Can not parse CSV file: {e}')

        if 'complexity' not in words_df.columns:
            raise CommandError(
                f'Can not find `complexity` in columns: '
                f'{words_df.columns.values}'
            )

        if 'text' not in words_df.columns:
            raise CommandError(
                f'Can not find `text` in columns: {words_df.columns.values}')

        Word.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared all existing words'))
        for _, row in tqdm(
            words_df.iterrows(),
            total=words_df.shape[0]
        ):
            try:
                Word.objects.create(
                    text=row['text'],
                    complexity=row['complexity']
                )
            except Exception as e:
                raise CommandError(
                    f'Can create new word from given row, '
                    f'error: {e}\nrow:\n{row}'
                )

        self.stdout.write(
            self.style.SUCCESS(f'Inserted {words_df.shape[0]} new words')
        )
