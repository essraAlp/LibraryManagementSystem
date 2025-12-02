"""
Migration script to hash existing plain text passwords.
Run this ONCE to convert all existing passwords to hashed format.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from user.models import User

def hash_passwords():
    """Hash all existing plain text passwords."""
    users = User.objects.all()
    updated_count = 0
    
    for user in users:
        # Check if password is already hashed (starts with algorithm identifier)
        if not user.Password.startswith('pbkdf2_sha256$'):
            print(f"Hashing password for user: {user.Username}")
            user.Password = make_password(user.Password)
            user.save()
            updated_count += 1
        else:
            print(f"Password already hashed for user: {user.Username}")
    
    print(f"\n✅ Successfully hashed {updated_count} passwords")
    print(f"✅ {users.count() - updated_count} passwords were already hashed")

if __name__ == '__main__':
    print("=" * 50)
    print("PASSWORD HASHING MIGRATION")
    print("=" * 50)
    print("\nThis will convert all plain text passwords to secure hashed format.")
    
    confirm = input("\nDo you want to continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        hash_passwords()
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration cancelled.")
