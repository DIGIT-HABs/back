from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class TestAuthView(APIView):
    """Simple test view to check JWT authentication."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'message': 'Authentication works!',
            'user_id': str(user.id),
            'username': user.username,
            'email': user.email,
            'user_id_type': type(user.id).__name__,
        })

