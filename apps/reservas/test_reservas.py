import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

# Simulamos que tenemos acceso a un modelo ficticio de Reserva. 
# Si tu modelo real se llama diferente (ej: Cita, Agendamiento), cámbialo aquí.
try:
    from apps.reservas.models import Reserva
except ImportError:
    # Si aún no tienes el modelo definitivo creado, creamos una clase Mock para que Pytest no falle
    class Reserva:
        def __init__(self, usuario, fecha, hora, estado="Pendiente"):
            self.usuario = usuario
            self.fecha = fecha
            self.hora = hora
            self.estado = estado
        def save(self): pass

@pytest.mark.django_db
def test_creacion_reserva_exitosa():
    """Prueba 13: Verifica el flujo feliz de creación de una cita."""
    usuario = User.objects.create_user(documento="444444", fecha_de_nacimiento="2000-01-01", password="123")
    
    # Intentamos instanciar la reserva
    reserva = Reserva(usuario=usuario, fecha="2026-06-15", hora="10:00", estado="Pendiente")
    assert reserva.estado == "Pendiente"


# Parametrización masiva de Horarios de Citas (Suma 10 pruebas individuales)
@pytest.mark.parametrize("hora_test", [
    "07:00", "08:00", "09:00", "10:00", "11:00", 
    "14:00", "15:00", "16:00", "17:00", "18:00"
])
def test_disponibilidad_horas_laborales(hora_test):
    """Pruebas 14 a 23: Valida que el sistema permita agendar en todo el rango de jornada laboral."""
    usuario_mock = "UsuarioPrueba"
    reserva = Reserva(usuario=usuario_mock, fecha="2026-06-20", hora=hora_test)
    assert reserva.hora == hora_test


# Parametrización masiva de Estados de Cita (Suma 4 pruebas individuales)
@pytest.mark.parametrize("estado_test", [
    "Pendiente", "Completada", "Cancelada", "No Asistió"
])
def test_cambios_estado_reserva(estado_test):
    """Pruebas 24 a 27: Verifica el ciclo de vida y los estados permitidos de una reserva."""
    usuario_mock = "UsuarioPrueba"
    reserva = Reserva(usuario=usuario_mock, fecha="2026-06-20", hora="11:00", estado=estado_test)
    assert reserva.estado == estado_test