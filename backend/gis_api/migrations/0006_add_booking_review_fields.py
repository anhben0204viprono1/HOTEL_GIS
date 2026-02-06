# Data migration to add booking review columns using raw SQL

from django.db import migrations

def add_columns(apps, schema_editor):
    """Add reviewed columns to bookings table using raw SQL"""
    sql = """
    BEGIN;
    
    -- Add reviewed_by_id column
    ALTER TABLE public.bookings 
    ADD COLUMN IF NOT EXISTS reviewed_by_id INTEGER REFERENCES public.auth_user(id) ON DELETE SET NULL;
    
    -- Add reviewed_date column  
    ALTER TABLE public.bookings 
    ADD COLUMN IF NOT EXISTS reviewed_date TIMESTAMP NULL;
    
    -- Add review_notes column
    ALTER TABLE public.bookings 
    ADD COLUMN IF NOT EXISTS review_notes TEXT NULL;
    
    COMMIT;
    """
    
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'bookings'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            if 'reviewed_by_id' not in columns:
                print("Adding reviewed_by_id ...")
                cursor.execute("""
                    ALTER TABLE public.bookings 
                    ADD COLUMN reviewed_by_id INTEGER REFERENCES public.auth_user(id) ON DELETE SET NULL
                """)
                print("✓ reviewed_by_id added")
            
            if 'reviewed_date' not in columns:
                print("Adding reviewed_date ...")
                cursor.execute("""
                    ALTER TABLE public.bookings 
                    ADD COLUMN reviewed_date TIMESTAMP NULL
                """)
                print("✓ reviewed_date added")
            
            if 'review_notes' not in columns:
                print("Adding review_notes ...")
                cursor.execute("""
                    ALTER TABLE public.bookings 
                    ADD COLUMN review_notes TEXT NULL
                """)
                print("✓ review_notes added")
            
            print("✓ All columns verified/added successfully!")
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()


def remove_columns(apps, schema_editor):
    """Reverse migration - remove columns"""
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'bookings'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'reviewed_by_id' in columns:
                cursor.execute("ALTER TABLE public.bookings DROP COLUMN reviewed_by_id")
            if 'reviewed_date' in columns:
                cursor.execute("ALTER TABLE public.bookings DROP COLUMN reviewed_date")
            if 'review_notes' in columns:
                cursor.execute("ALTER TABLE public.bookings DROP COLUMN review_notes")
                
        except Exception as e:
            print(f"Error in reverse: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('gis_api', '0005_hotel_created_date_hotel_description_hotel_email_and_more'),
    ]

    operations = [
        migrations.RunPython(add_columns, remove_columns),
    ]
