"""
Vistas de Elementos e Inventario — BienestarMind
Control completo de stock, préstamos, entradas/salidas y alertas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django import forms
from django.views.decorators.cache import never_cache
import datetime

from apps.elementos.models import (
    Elemento, CategoriaElemento, MovimientoInventario,
    ReservaElemento, ReservaEspacio
)


# ── FORMULARIOS ────────────────────────────────────────────────────

class ElementoForm(forms.ModelForm):
    class Meta:
        model = Elemento
        fields = ['nombre_elemento','categoria','descripcion','estado_elemento',
                'codigo','stock_total','stock_disponible','stock_minimo','ubicacion']
        widgets = {
            'nombre_elemento': forms.TextInput(attrs={'class':'form-control'}),
            'categoria':       forms.Select(attrs={'class':'form-select'}),
            'descripcion':     forms.Textarea(attrs={'class':'form-control','rows':2}),
            'estado_elemento': forms.Select(attrs={'class':'form-select'}),
            'codigo':          forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: BM-PC-001'}),
            'stock_total':     forms.NumberInput(attrs={'class':'form-control','min':0}),
            'stock_disponible':forms.NumberInput(attrs={'class':'form-control','min':0}),
            'stock_minimo':    forms.NumberInput(attrs={'class':'form-control','min':0}),
            'ubicacion':       forms.TextInput(attrs={'class':'form-control','placeholder':'Ej: Armario 2, Sala Bienestar'}),
        }

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('stock_total', 0)
        disp  = cleaned.get('stock_disponible', 0)
        if disp > total:
            raise forms.ValidationError('El stock disponible no puede ser mayor al stock total.')
        return cleaned


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = CategoriaElemento
        fields = ['descripcion']
        widgets = {'descripcion': forms.TextInput(attrs={'class':'form-control'})}


class MovimientoForm(forms.Form):
    cantidad    = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class':'form-control','min':1}))
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Descripción u observaciones...'}),
    )


# ── ELEMENTOS CRUD ─────────────────────────────────────────────────
@never_cache
@login_required
def lista_elementos(request):
    qs = Elemento.objects.select_related('categoria').all()
    q      = request.GET.get('q','')
    estado = request.GET.get('estado','')
    cat    = request.GET.get('categoria','')
    if q:      qs = qs.filter(Q(nombre_elemento__icontains=q)|Q(codigo__icontains=q))
    if estado: qs = qs.filter(estado_elemento=estado)
    if cat:    qs = qs.filter(categoria__id=cat)
    return render(request, 'elementos/lista.html', {
        'elementos':   qs,
        'categorias':  CategoriaElemento.objects.all(),
        'estados':     Elemento.ESTADO_CHOICES,
        'q':q,'estado':estado,'categoria':cat,
        'total':       qs.count(),
        'alertas':     qs.filter(stock_disponible__lte=models_stock_minimo()).count() if False else
                       sum(1 for e in qs if e.alerta_stock),
    })

@never_cache
@login_required
def crear_elemento(request):
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:lista')
    form = ElementoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        el = form.save()
        # Registrar entrada inicial
        MovimientoInventario.objects.create(
            elemento=el, tipo='ENTRADA', cantidad=el.stock_total,
            descripcion='Registro inicial de inventario',
            stock_antes=0, stock_despues=el.stock_total,
            usuario=request.user,
        )
        messages.success(request, f'Elemento "{el.nombre_elemento}" creado con stock {el.stock_total}.')
        return redirect('elementos:inventario')
    return render(request,'elementos/form.html',{'form':form,'titulo':'Nuevo Elemento'})

@never_cache
@login_required
def editar_elemento(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:lista')
    el   = get_object_or_404(Elemento, pk=pk)
    form = ElementoForm(request.POST or None, instance=el)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request,'Elemento actualizado.')
        return redirect('elementos:inventario')
    return render(request,'elementos/form.html',{'form':form,'titulo':f'Editar: {el.nombre_elemento}'})

@never_cache
@login_required
def eliminar_elemento(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:lista')
    get_object_or_404(Elemento, pk=pk).delete()
    messages.success(request,'Elemento eliminado.')
    return redirect('elementos:lista')

@never_cache
@login_required
def lista_categorias(request):
    return render(request,'elementos/categorias.html',{
        'categorias': CategoriaElemento.objects.annotate(total=Count('elementos')).all()
    })

@never_cache
@login_required
def crear_categoria(request):
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:categorias')
    form = CategoriaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request,'Categoría creada.')
        return redirect('elementos:categorias')
    return render(request,'elementos/categoria_form.html',{'form':form,'titulo':'Nueva Categoría'})


# ── INVENTARIO ─────────────────────────────────────────────────────
@never_cache
@login_required
def inventario_dashboard(request):
    """Dashboard de inventario con resumen, alertas y estado de todos los elementos."""
    elementos = Elemento.objects.select_related('categoria').all()
    alertas   = [e for e in elementos if e.alerta_stock and e.estado_elemento not in ('BAJA',)]
    ultimos   = MovimientoInventario.objects.select_related('elemento','usuario').all()[:15]

    resumen = {
        'total_elementos':   elementos.count(),
        'disponibles':       elementos.filter(estado_elemento='DISPONIBLE').count(),
        'en_uso':            elementos.filter(estado_elemento='EN_USO').count(),
        'mantenimiento':     elementos.filter(estado_elemento='MANTENIMIENTO').count(),
        'agotados':          elementos.filter(estado_elemento='AGOTADO').count(),
        'alertas_stock':     len(alertas),
        'prestamos_activos': ReservaElemento.objects.filter(estado='APROBADA').count(),
    }

    q   = request.GET.get('q','')
    cat = request.GET.get('categoria','')
    if q:   elementos = elementos.filter(Q(nombre_elemento__icontains=q)|Q(codigo__icontains=q))
    if cat: elementos = elementos.filter(categoria__id=cat)

    return render(request,'elementos/inventario.html',{
        'elementos':   elementos,
        'alertas':     alertas,
        'ultimos':     ultimos,
        'resumen':     resumen,
        'categorias':  CategoriaElemento.objects.all(),
        'q':q,'categoria':cat,
    })

@never_cache
@login_required
def registrar_entrada(request, pk):
    """Registrar llegada de nuevos elementos al inventario."""
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR','INSTRUCTOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:inventario')
    el   = get_object_or_404(Elemento, pk=pk)
    form = MovimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cant = form.cleaned_data['cantidad']
        desc = form.cleaned_data.get('descripcion','')
        ant  = el.stock_disponible
        el.stock_disponible += cant
        el.stock_total      += cant
        el.actualizar_estado()
        MovimientoInventario.objects.create(
            elemento=el, tipo='ENTRADA', cantidad=cant,
            descripcion=desc or f'Entrada de {cant} unidad(es)',
            stock_antes=ant, stock_despues=el.stock_disponible,
            usuario=request.user,
        )
        messages.success(request, f'Entrada registrada: +{cant} {el.nombre_elemento}. Stock: {el.stock_disponible}/{el.stock_total}')
        return redirect('elementos:inventario')
    return render(request,'elementos/movimiento_form.html',{
        'form':form,'elemento':el,'tipo':'ENTRADA',
        'titulo':f'Registrar Entrada — {el.nombre_elemento}',
        'color':'verde','icono':'bi-box-arrow-in-down',
    })

@never_cache
@login_required
def registrar_salida(request, pk):
    """Registrar préstamo o salida de un elemento."""
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR','INSTRUCTOR'):
        messages.error(request,'Sin permisos.'); return redirect('elementos:inventario')
    el   = get_object_or_404(Elemento, pk=pk)
    form = MovimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cant = form.cleaned_data['cantidad']
        desc = form.cleaned_data.get('descripcion','')
        if cant > el.stock_disponible:
            form.add_error('cantidad', f'Stock disponible insuficiente ({el.stock_disponible} unidades).')
        else:
            ant = el.stock_disponible
            el.stock_disponible -= cant
            el.actualizar_estado()
            MovimientoInventario.objects.create(
                elemento=el, tipo='SALIDA', cantidad=cant,
                descripcion=desc or f'Salida/préstamo de {cant} unidad(es)',
                stock_antes=ant, stock_despues=el.stock_disponible,
                usuario=request.user,
            )
            messages.success(request, f'Salida registrada: -{cant} {el.nombre_elemento}. Disponible: {el.stock_disponible}')
            return redirect('elementos:inventario')
    return render(request,'elementos/movimiento_form.html',{
        'form':form,'elemento':el,'tipo':'SALIDA',
        'titulo':f'Registrar Salida — {el.nombre_elemento}',
        'color':'naranja','icono':'bi-box-arrow-up',
    })

@never_cache
@login_required
def devolver_elemento(request, pk):
    """Registrar devolución de un elemento prestado."""
    el   = get_object_or_404(Elemento, pk=pk)
    form = MovimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cant = form.cleaned_data['cantidad']
        desc = form.cleaned_data.get('descripcion','')
        max_devolver = el.stock_total - el.stock_disponible
        if cant > max_devolver:
            form.add_error('cantidad', f'Solo hay {max_devolver} unidad(es) pendientes de devolución.')
        else:
            ant = el.stock_disponible
            el.stock_disponible += cant
            el.actualizar_estado()
            MovimientoInventario.objects.create(
                elemento=el, tipo='DEVOLUCION', cantidad=cant,
                descripcion=desc or f'Devolución de {cant} unidad(es)',
                stock_antes=ant, stock_despues=el.stock_disponible,
                usuario=request.user,
            )
            messages.success(request, f'Devolución registrada: +{cant} {el.nombre_elemento}. Disponible: {el.stock_disponible}')
            return redirect('elementos:inventario')
    return render(request,'elementos/movimiento_form.html',{
        'form':form,'elemento':el,'tipo':'DEVOLUCION',
        'titulo':f'Registrar Devolución — {el.nombre_elemento}',
        'color':'verde','icono':'bi-arrow-return-left',
    })

@never_cache
@login_required
def ajustar_inventario(request, pk):
    """Ajuste manual de inventario (corrección de errores, conteo físico)."""
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request,'Solo administradores pueden hacer ajustes.'); return redirect('elementos:inventario')
    el   = get_object_or_404(Elemento, pk=pk)
    form = MovimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nuevo_stock = form.cleaned_data['cantidad']
        desc        = form.cleaned_data.get('descripcion','Ajuste de inventario')
        ant         = el.stock_disponible
        el.stock_disponible = nuevo_stock
        if nuevo_stock > el.stock_total:
            el.stock_total = nuevo_stock
        el.actualizar_estado()
        MovimientoInventario.objects.create(
            elemento=el, tipo='AJUSTE', cantidad=abs(nuevo_stock - ant),
            descripcion=f'{desc} (de {ant} a {nuevo_stock})',
            stock_antes=ant, stock_despues=nuevo_stock,
            usuario=request.user,
        )
        messages.success(request, f'Inventario ajustado: {el.nombre_elemento} → {nuevo_stock} disponibles.')
        return redirect('elementos:inventario')
    return render(request,'elementos/movimiento_form.html',{
        'form':form,'elemento':el,'tipo':'AJUSTE',
        'titulo':f'Ajustar Inventario — {el.nombre_elemento}',
        'color':'azul','icono':'bi-sliders',
        'ajuste':True,
    })

@never_cache
@login_required
def historial_movimientos(request):
    """Historial completo de movimientos de inventario."""
    qs = MovimientoInventario.objects.select_related('elemento','elemento__categoria','usuario').all()
    q    = request.GET.get('q','')
    tipo = request.GET.get('tipo','')
    if q:    qs = qs.filter(Q(elemento__nombre_elemento__icontains=q)|Q(descripcion__icontains=q))
    if tipo: qs = qs.filter(tipo=tipo)
    return render(request,'elementos/historial.html',{
        'movimientos': qs[:200],
        'tipos':       MovimientoInventario.TIPO_CHOICES,
        'q':q,'tipo':tipo,
        'total':qs.count(),
    })
