import os
import django
import csv
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_management.settings")
django.setup()

from Books.models import Book  # kendi app adın neyse onu yaz

def normalize_year(year):
    if not year or year.strip() == "":
        return None
    year = str(year).strip()
    if year.isdigit() and len(year) == 4:
        return f"{year}-01-01"
    try:
        datetime.fromisoformat(year)
        return year
    except:
        return None


def load_books_from_csv(csv_path):
    print(f"\n🚀 Başlıyor: {csv_path}\n")

    if not os.path.exists(csv_path):
        print("❌ CSV bulunamadı!")
        return

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        inserted = 0
        skipped = 0

        for i, row in enumerate(reader, start=1):
            name = row.get("name")
            isbn = row.get("ISBN")

            if not isbn:
                print(f"❌ Atlandı: ISBN boş")
                skipped += 1
                continue

            isbn_str = isbn.strip()

            if Book.objects.filter(ISBN=isbn_str).exists():
                print(f"⏭ Atlandı: Duplicate ISBN → {isbn_str}")
                skipped += 1
                continue

            year_value = normalize_year(row.get("publication_year"))

            if year_value is None:
                print(f"⚠ year null → year None olarak kaydedilecek")

            try:
                book = Book.objects.create(
                    ISBN=isbn_str,
                    name=row.get("name", "")[:200],
                    explanation=row.get("explanation", ""),
                    publisher=row.get("publisher", "")[:50],
                    author=row.get("author", "")[:50],
                    type=row.get("book_type", "")[:50],
                    year=year_value,
                    image=row.get("book_img", ""),
                    status="available",
                )
                inserted += 1

            except Exception as e:
                print(f"❌ HATA: {e}")
                skipped += 1


    print("\n=========== ÖZET ===========")
    print(f"📚 Eklenen kitap: {inserted}")
    print(f"⚠ Atlanan kitap: {skipped}")
    print("============================")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "TurkishBookDataSet.csv")

    load_books_from_csv(csv_path)
