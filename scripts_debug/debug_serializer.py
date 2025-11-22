import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User

email = 'moussa.diop@digit-hab.com'
password = 'test123'

print("\n" + "="*70)
print("DEBUG SERIALIZER")
print("="*70 + "\n")

# Step 1: Find user by email
print(f"1. Recherche par email: {email}")
try:
    user = User.objects.get(email=email)
    print(f"   ✅ Utilisateur trouvé: {user.username}")
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Active: {user.is_active}")
except User.DoesNotExist:
    print("   ❌ Utilisateur non trouvé!")
    exit(1)

# Step 2: Check password
print(f"\n2. Vérification du mot de passe...")
password_ok = user.check_password(password)
print(f"   Résultat: {password_ok}")
if password_ok:
    print("   ✅ Mot de passe CORRECT")
else:
    print("   ❌ Mot de passe INCORRECT")
    exit(1)

# Step 3: Simulate serializer validation logic
print(f"\n3. Simulation de la logique du serializer...")

attrs = {
    'email': email,
    'password': password
}

print(f"   attrs['email'] = '{attrs.get('email')}'")
print(f"   attrs['username'] = '{attrs.get('username')}'")
print(f"   attrs['password'] = '{attrs.get('password')}'")

email_input = attrs.get('email')
username_input = attrs.get('username')
password_input = attrs.get('password')

print(f"\n4. Nettoyage des inputs...")
if email_input:
    email_input = email_input.strip()
    print(f"   Email après strip: '{email_input}'")
if username_input:
    username_input = username_input.strip()
    print(f"   Username après strip: '{username_input}'")

print(f"\n5. Vérification email ou username fourni...")
if not email_input and not username_input:
    print("   ❌ Ni email ni username fourni!")
else:
    print(f"   ✅ Email fourni: {bool(email_input)}")
    print(f"   ✅ Username fourni: {bool(username_input)}")

print(f"\n6. Recherche utilisateur...")
user_found = None

if email_input:
    print(f"   Recherche par email: {email_input}")
    try:
        user_candidate = User.objects.get(email=email_input)
        print(f"   - Utilisateur trouvé: {user_candidate.username}")
        print(f"   - Vérification du mot de passe...")
        if user_candidate.check_password(password_input):
            user_found = user_candidate
            print(f"   ✅ Mot de passe correct!")
        else:
            print(f"   ❌ Mot de passe incorrect!")
    except User.DoesNotExist:
        print(f"   ❌ Aucun utilisateur avec cet email")

if not user_found and username_input:
    print(f"   Recherche par username: {username_input}")
    try:
        user_candidate = User.objects.get(username=username_input)
        print(f"   - Utilisateur trouvé: {user_candidate.username}")
        if user_candidate.check_password(password_input):
            user_found = user_candidate
            print(f"   ✅ Mot de passe correct!")
        else:
            print(f"   ❌ Mot de passe incorrect!")
    except User.DoesNotExist:
        print(f"   ❌ Aucun utilisateur avec ce username")

print(f"\n7. Résultat final...")
if user_found:
    print(f"   ✅ UTILISATEUR AUTHENTIFIÉ: {user_found.username}")
    print(f"   - Active: {user_found.is_active}")
else:
    print(f"   ❌ AUTHENTIFICATION ÉCHOUÉE")

print("\n" + "="*70 + "\n")

