from django.db import migrations


def add_hotel_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'hotels'
            """)
            columns = [row[0] for row in cursor.fetchall()]

            if 'is_approved' not in columns:
                cursor.execute("ALTER TABLE public.hotels ADD COLUMN is_approved BOOLEAN DEFAULT FALSE")

            if 'reviewed_by_id' not in columns:
                cursor.execute(
                    "ALTER TABLE public.hotels ADD COLUMN reviewed_by_id INTEGER REFERENCES public.auth_user(id) ON DELETE SET NULL"
                )

            if 'reviewed_date' not in columns:
                cursor.execute("ALTER TABLE public.hotels ADD COLUMN reviewed_date TIMESTAMP NULL")

            if 'review_notes' not in columns:
                cursor.execute("ALTER TABLE public.hotels ADD COLUMN review_notes TEXT NULL")

        except Exception as e:
            print('Error adding hotel review columns:', e)


def remove_hotel_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'hotels'
            """)
            columns = [row[0] for row in cursor.fetchall()]

            if 'review_notes' in columns:
                cursor.execute("ALTER TABLE public.hotels DROP COLUMN review_notes")
            if 'reviewed_date' in columns:
                cursor.execute("ALTER TABLE public.hotels DROP COLUMN reviewed_date")
            if 'reviewed_by_id' in columns:
                cursor.execute("ALTER TABLE public.hotels DROP COLUMN reviewed_by_id")
            if 'is_approved' in columns:
                cursor.execute("ALTER TABLE public.hotels DROP COLUMN is_approved")

        except Exception as e:
            print('Error removing hotel review columns:', e)


class Migration(migrations.Migration):

    dependencies = [
        ('gis_api', '0006_add_booking_review_fields'),
    ]

    operations = [
        migrations.RunPython(add_hotel_columns, remove_hotel_columns),
    ]
