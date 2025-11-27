import os
import django
import csv
import sys

# Proje dizinini yola ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django ortamını ayarla
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_management.settings")
django.setup()

# Sizin özel modellerinizi import ediyoruz
from user.models import User, Student, Staff

def load_custom_users(filename, user_type):
    """
    CSV dosyasından verileri okuyup özel User, Student ve Staff tablolarına yazar.
    user_type: 'student' veya 'staff' olmalıdır.
    """
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    
    print(f"\n🚀 {filename} dosyası {user_type} olarak yükleniyor...")

    if not os.path.exists(file_path):
        print(f"❌ {filename} bulunamadı!")
        return

    with open(file_path, mode='r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file)
        
        count = 0
        skipped = 0

        for row in reader:
            username = row.get('username')
            
            # CSV'deki name ve surname'i birleştirip modeldeki 'Name' alanına yazıyoruz
            full_name = f"{row.get('name', '')} {row.get('surname', '')}".strip()
            
            email = row.get('email')
            phone = row.get('phone')
            password = row.get('password') # Şifreler modelinize göre düz metin kaydediliyor

            # Kullanıcı zaten var mı kontrol et (Username üzerinden)
            if User.objects.filter(Username=username).exists():
                print(f"⏭  Atlandı (Zaten var): {username}")
                skipped += 1
                continue

            try:
                # 1. Ana User tablosuna kayıt oluştur
                new_user = User.objects.create(
                    Name=full_name,
                    Email=email,
                    Phone=phone,
                    Username=username,
                    Password=password,
                    Type=user_type  # 'student' veya 'staff'
                )

                # 2. Alt tablolara (Student veya Staff) ilişkiyi ekle
                if user_type == 'student':
                    Student.objects.create(user=new_user)
                    print(f"✅ Öğrenci eklendi: {full_name}")
                
                elif user_type == 'staff':
                    Staff.objects.create(user=new_user)
                    print(f"✅ Personel eklendi: {full_name}")
                
                count += 1
                
            except Exception as e:
                print(f"❌ Hata ({username}): {e}")
                skipped += 1

    print(f"✨ {filename} tamamlandı.")
    print(f"   Eklenen: {count}")
    print(f"   Atlanan: {skipped}")

if __name__ == "__main__":
    # Öğrencileri yükle
    load_custom_users("student.csv", user_type="student")
    
    # Personeli yükle
    load_custom_users("staff.csv", user_type="staff")