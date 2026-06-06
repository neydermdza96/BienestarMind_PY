import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@pytest.mark.django_db
def test_creacion_usuario_perfil_correcto():
    """1. Prueba básica de creación correcta."""
    usuario = User.objects.create_user(
        documento="88888888",
        fecha_de_nacimiento="1995-05-15",
        password="ClaveSegura123*"
    )
    assert usuario.documento == "88888888"
    assert usuario.is_active is True


@pytest.mark.django_db
def test_error_documento_duplicado():
    """2. Prueba de restricción de duplicados."""
    User.objects.create_user(
        documento="55555555",
        fecha_de_nacimiento="1990-10-10",
        password="PasswordUno123*"
    )
    with pytest.raises(IntegrityError):
        User.objects.create_user(
            documento="55555555",
            fecha_de_nacimiento="2001-02-02",
            password="PasswordDos123*"
        )


# --- AQUÍ EMPIEZA LA PARAMETRIZACIÓN MASIVA ---

# Validar múltiples tipos de documentos de prueba (Suma 5 pruebas individuales)
@pytest.mark.django_db
@pytest.mark.parametrize("doc_ejemplo", [
    "10102030",       # Cédula estándar
    "TI998877",       # Tarjeta de identidad con letras
    "CE-443322",      # Cédula de extranjería con guion
    "1.023.445.112",  # Formato con puntos
    "A1234567"        # Pasaporte
])
def test_formatos_documento_permitidos(doc_ejemplo):
    """Pruebas 3 a 7: Verifica que el modelo acepte diferentes formatos de identificación."""
    usuario = User.objects.create_user(
        documento=doc_ejemplo,
        fecha_de_nacimiento="1998-12-25",
        password="ClaveSegura123*"
    )
    assert usuario.documento == doc_ejemplo


# Validar diferentes contraseñas (Suma 5 pruebas individuales)
@pytest.mark.django_db
@pytest.mark.parametrize("clave_ejemplo", [
    "ClaveMuyLargaYSegura2026*",
    "12345678aA*",
    "Bogota2026#",
    "Admin_Mind_2026",
    "UsuarioProvisional99!"
])
def test_registro_varios_tipos_password(clave_ejemplo):
    """Pruebas 8 a 12: Verifica que el sistema procese y encripte correctamente diferentes estructuras de clave."""
    usuario = User.objects.create_user(
        documento="999" + clave_ejemplo[:4],  # Genera un documento único corto
        fecha_de_nacimiento="2000-01-01",
        password=clave_ejemplo
    )
    assert usuario.check_password(clave_ejemplo) is True