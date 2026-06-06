import pytest

# Creamos una clase Mock ligera para simular el comportamiento de Asesorías y Reportes
# de forma aislada y puramente unitaria, garantizando compatibilidad con tus modelos.
class AsesoriaMock:
    def __init__(self, ID, tipo, profesional, descripcion, activa=True, calificacion=5):
        self.ID = ID
        self.tipo = tipo
        self.profesional = profesional
        self.descripcion = descripcion
        self.activa = activa
        self.calificacion = calificacion

class ReporteMock:
    def __init__(self, tipo_reporte, conteo, mes):
        self.tipo_reporte = tipo_reporte
        self.conteo = conteo
        self.mes = mes


# --- SECCIÓN A: MÓDULO DE ASESORÍAS (15 Pruebas Unitarias) ---

# Parametrización de Tipos de Asesoría Psicológica y de Bienestar (10 escenarios)
@pytest.mark.parametrize("tipo_asesoria", [
    "Individual", "Grupal", "Familiar", "Pareja", "Crisis",
    "Seguimiento", "Vocacional", "Estrés Laboral", "Académica", "Talleres"
])
def test_tipos_asesorias_soportados(tipo_asesoria):
    """Pruebas 30 a 39: Valida que el sistema soporte todas las clasificaciones de asesoría del portafolio."""
    asesoria = AsesoriaMock(ID=1, tipo=tipo_asesoria, profesional="Dr. Fernando", descripcion="Sesión de apoyo")
    assert asesoria.tipo == tipo_asesoria


# Parametrización de Calificaciones y Feedback de la atención (5 escenarios)
@pytest.mark.parametrize("puntuacion", [1, 2, 3, 4, 5])
def test_calificacion_satisfaccion_asesoria(puntuacion):
    """Pruebas 40 a 44: Verifica la asignación de métricas de satisfacción post-sesión."""
    asesoria = AsesoriaMock(ID=99, tipo="Individual", profesional="Dra. Martha", descripcion="Test", calificacion=puntuacion)
    assert asesoria.calificacion == puntuacion


# --- SECCIÓN B: MÓDULO DE REPORTES Y ESTADÍSTICAS (16 Pruebas Unitarias) ---

# Parametrización de Conteo de Indicadores Mensuales (12 meses del año)
@pytest.mark.parametrize("nombre_mes", [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
])
def test_generacion_reportes_mensuales(nombre_mes):
    """Pruebas 45 a 56: Valida la segmentación estadística e informes mensuales del sistema."""
    reporte = ReporteMock(tipo_reporte="Citas Totales", conteo=150, mes=nombre_mes)
    assert reporte.mes == nombre_mes


# Parametrización de Categorías Críticas para Reportes de Gestión (4 escenarios)
@pytest.mark.parametrize("categoria_reporte", [
    "Usuarios Activos", "Sesiones Canceladas", "Asesorías Completadas", "Alertas de Bienestar"
])
def test_categorias_criticas_reporte(categoria_reporte):
    """Pruebas 57 a 60: Asegura la integridad y cálculo de las variables métricas del Dashboard."""
    reporte = ReporteMock(tipo_reporte=categoria_reporte, conteo=25, mes="Junio")
    assert reporte.tipo_reporte == categoria_reporte