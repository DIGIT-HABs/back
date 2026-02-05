import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.crm.models import ClientProfile, ClientNote
from apps.crm.serializers import ClientProfileSerializer

User = get_user_model()

print("\n" + "="*60)
print("📊 VÉRIFICATION DE LA BASE DE DONNÉES CRM")
print("="*60)

# Compter les utilisateurs
total_users = User.objects.count()
clients = User.objects.filter(role='client').count()
agents = User.objects.filter(role='agent').count()

print(f"\n👥 UTILISATEURS:")
print(f"   Total: {total_users}")
print(f"   Clients: {clients}")
print(f"   Agents: {agents}")

# Compter les profils clients
total_profiles = ClientProfile.objects.count()
print(f"\n📝 PROFILS CLIENTS: {total_profiles}")

# Compter les notes
total_notes = ClientNote.objects.count()
print(f"📋 NOTES: {total_notes}")

# Afficher les 5 premiers clients
if total_profiles > 0:
    print(f"\n{'='*60}")
    print("🎯 PREMIERS CLIENTS:")
    print(f"{'='*60}\n")
    
    profiles = ClientProfile.objects.select_related('user').all()[:5]
    for profile in profiles:
        print(f"✅ {profile.user.get_full_name()}")
        print(f"   Email: {profile.user.email}")
        print(f"   Status: {profile.status}")
        print(f"   Priority: {profile.priority_level}")
        print(f"   Budget: {profile.min_budget:,}€ - {profile.max_budget:,}€")
        print(f"   Tags: {', '.join(profile.tags) if profile.tags else 'Aucun'}")
        print()
else:
    print("\n⚠️  AUCUN CLIENT TROUVÉ!")
    print("\n💡 Pour créer des clients:")
    print("   python create_clients.py")

print("="*60)
print("\n✅ Vérification terminée!\n")
