import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

# Obtenemos el modelo de usuario activo de BienestarMind
User = get_user_model()

@pytest.mark.django_db
def test_login_usuario_correcto(client):
    """
    Prueba unitaria para verificar que un usuario registrado
    con su documento y campos obligatorios puede iniciar sesión con éxito.
    """
    # 1. Crear el usuario incluyendo documento y fecha_de_nacimiento corregida
    usuario_prueba = User.objects.create_user(
        documento="123456789",
        fecha_de_nacimiento="2000-01-01",  # Corregido con 'de' en español
        password="ClaveSegura123*"
    )
    
    url_login = reverse('usuarios:login')
    
    # 2. Simular el envío de datos.
    datos_login = {
        'username': '123456789',
        'documento': '123456789',
        'password': 'ClaveSegura123*'
    }
    respuesta = client.post(url_login, datos_login)
    
    # 3. Verificación: Redirección exitosa (Status 302)
    assert respuesta.status_code == 302


@pytest.mark.django_db
def test_login_usuario_incorrecto(client):
    """
    Prueba unitaria para verificar que el sistema rechaza el acceso
    cuando la contraseña ingresada es errónea.
    """
    # 1. Crear el usuario de prueba con sus campos obligatorios
    User.objects.create_user(
        documento="987654321",
        fecha_de_nacimiento="2000-01-01",  # Corregido con 'de' en español
        password="ClaveSegura123*"
    )
    
    url_login = reverse('usuarios:login')
    
    # 2. Simular el envío de datos con una contraseña equivocada
    datos_incorrectos = {
        'username': '987654321',
        'documento': '987654321',
        'password': 'ContrasenaIncorrecta999'
    }
    respuesta = client.post(url_login, datos_incorrectos)
    
    # 3. Verificación: Al fallar, se recarga el login (Status 200)
    assert respuesta.status_code == 200